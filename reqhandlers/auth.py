import os, sys, traceback, json, asyncio
from datetime import datetime, timedelta
import jwt

sys.path.append("..")
from db.tables_definitions import USERS_TABLE, USERS_TESTS_TABLE, RESULTS_TABLE
from socketserver.go import Go

HOST = os.getenv('HOST', "")
PORT = int(os.getenv('PORT', 0))
SECRET = os.getenv('SECRET', 'secret')
REPLICAS_SECRET = os.getenv('REPLICAS_SECRET')

replicas_addresses = json.loads( os.getenv('REPLICAS_ADDRESSES', None) )
# remove own address from REPLICAS_ADDRESSES
REPLICAS_ADDRESSES = [tuple(addr) for addr in replicas_addresses if (tuple(addr) != (HOST, PORT))]

async def signup(reqHeader, reqBody, server_inst):
    db = server_inst._server_vars.get('db')

    ci = reqBody.get('ci')
    email = reqBody.get('email')
    phone = reqBody.get('phone')
    name = reqBody.get('name')
    last_name = reqBody.get('last_name')

    body = {}
    header = {}

    ## CHECK IF DATA IS COMPLETE
    if (
      isinstance(ci, int) and
      isinstance(email, str) and
      isinstance(phone, str) and
      isinstance(name, str) and
      isinstance(last_name, str)
    ):
      ## CHECK IF USER ALREADY EXISTS IN LOCAL DB
      try:
        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?',
          [ci, email]
        )
        if (userData):
          body = { 'error_code': 'user-already-exists' }
          header = { **reqHeader, 'code': 409 }
        else:
          userCheckResponses = await asyncio.gather(
            *[ #this list is spread into the gather method
              Go(
                'GET',
                '/sync_user',
                host_port = address,
                body = { 'ci': ci, 'email': email, 'replicas_secret': REPLICAS_SECRET }
              ).as_coroutine()
              for address
              in REPLICAS_ADDRESSES
            ],
            return_exceptions = True
          )

          ## CHECK IF USER ALREADY EXISTS IN DISTRIBUTED DB
          userData = None
          for checkResponse in userCheckResponses:
            (header, body) = checkResponse
            if (body and body.get('user')): # tuple, 0 for header, 1 for body
              userData = body.get('user')
          
          if (userData):
            body = { 'error_code': 'user-already-exists' }
            header = { **reqHeader, 'code': 409 }
          else:
            ## SAVE USER IN DISTRIBUTED DB
            user = {
              'ci': ci, 'email': email, 'phone': phone, 'name': name, 'last_name': last_name
            }
            isRollbackNeeded = False
            rollbackAddresses = []
            # Try to save user to dist db
            userInsertResponses = await asyncio.gather(
              *[ #this list is spread into the gather method
                Go(
                  'POST',
                  '/sync_user',
                  host_port = address,
                  body = { 'user': user, 'replicas_secret': REPLICAS_SECRET }
                ).as_coroutine()
                for address
                in REPLICAS_ADDRESSES
              ],
              return_exceptions = True
            )
            # Check if a insert request failed due to duplicated users
            for i, insertResponse in enumerate(userInsertResponses):
              (header, body) = insertResponse
              if (
                body and
                body.get('error') and
                'UNIQUE constraint failed' in body.get('error')
              ):
                isRollbackNeeded = True
              else:
                rollbackAddresses.append(REPLICAS_ADDRESSES[i])
            # If rollback is needed, then send delete requests and return err response
            if isRollbackNeeded:
              print(f'rollback for ci: {ci} - email: {email}')
              userDeleteResponses = await asyncio.gather(
                *[ #this list is spread into the gather method
                  Go(
                    'DELETE',
                    '/sync_user',
                    host_port = address,
                    body = { 'ci': ci, 'replicas_secret': REPLICAS_SECRET }
                  ).as_coroutine()
                  for address
                  in rollbackAddresses
                ],
                return_exceptions = True
              )
            
              for deleteResponse in userDeleteResponses:
                (header, body) = deleteResponse
                print(body)
            
              body = { 'error_code': 'user-already-exists' }
              header = { **reqHeader, 'code': 409 }
            else:
              try:
                # No rollback needed
                exp = datetime.utcnow() + timedelta(minutes=120)
                token = jwt.encode(
                  { 'user': { 'ci': ci, 'email': email }, 'exp': exp },
                  SECRET
                )
                
                # returns bytes object that needs to be decoded into string
                user['session_token'] = token.decode('utf-8')

                await db.queryOne(
                  (f'INSERT INTO {USERS_TABLE} (ci, email, name, last_name, phone, session_token) '
                  'VALUES (:ci, :email, :name, :last_name, :phone, :session_token)'),
                  user
                )
                
                userData = await db.queryOne(
                  f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?',
                  [ci, email]
                )

                body = { 'user': userData }
                header = { **reqHeader, 'code': 200 }
              except Exception as e:
                traceback.print_exc()
                body = { 'error_code': 'internal-error', 'error': repr(e) }
                header = { **reqHeader, 'code': 500 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
    
    return header, body

async def signin(reqHeader, reqBody, server_inst):
    db = server_inst._server_vars.get('db')

    ci = reqBody.get('ci')
    email = reqBody.get('email')

    body = {}
    header = {}

    ## CHECK IF DATA IS COMPLETE
    if (
      isinstance(ci, int) and
      isinstance(email, str)
    ):
      ## GET USER FROM LOCAL DB AND REPLICAS
      try:
        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=?',
          [ci]
        )
        userReplicas = await asyncio.gather(
          *[ #this list is spread into the gather method
            Go(
              'GET',
              '/sync_user',
              host_port = address,
              body = { 'ci': ci, 'replicas_secret': REPLICAS_SECRET }
            ).as_coroutine()
            for address
            in REPLICAS_ADDRESSES
          ],
          return_exceptions = True
        )
        # if user is not found (by whatever reason) then is set to None
        userReplicas = [userReplica[1].get('user') for userReplica in userReplicas]
        userReplicas.append(userData)

        ## GET IMPORTANT DATA FROM RESULTS:
        # - most recent user
        # - list of tokens
        newestUserData = None
        maxDataVersion = -1
        tokens = []
        for i, user in enumerate(userReplicas):
          tokens.append('')
          if isinstance(user, dict):
            userExists = True
            tokens.append( user.get('session_token', '') )
            if (user.get('data_version') > maxDataVersion):
              maxDataVersion = user.get('data_version')
              newestUserData = user
              if i == len(userReplicas) - 1:
                newestUserData['db-address'] = 'local'
              else:
                newestUserData['db-address'] = REPLICAS_ADDRESSES[i]
        
        ## CHECK IF USER EXISTS
        if (newestUserData):
          newestUserData['session_token'] = ''
          if( ## CHECK IF USER USER DATA IS CORRECT
            newestUserData['ci'] == ci and
            newestUserData['email'] == email
          ):
            ## CHECK IF REPLICAS HAVE OPEN SESSION
            isReplicaSessionOpen = False
            for token in tokens[:-1]:
              try:
                jwt.decode(token, SECRET)
                isReplicaSessionOpen = True
              except Exception as e:
                pass
            
            if not isReplicaSessionOpen:
              ## START DATA REPLICATION
              if newestUserData.get('db-address') == 'local':
                ## FROM LOCAL DB
                # Try to UPDATE USER on DB replicas
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user',
                      host_port = address,
                      body = { 'user': newestUserData, 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )

                # Try to UPDATE USER_TESTS on DB replicas
                userTests = await db.queryMany(
                  f'SELECT * FROM {USERS_TESTS_TABLE} WHERE user_ci=?',
                  [newestUserData.get('ci')]
                )
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user/tests',
                      host_port = address,
                      body = { 'user_tests': userTests, 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )

                # Try to UPDATE USER_RESULTS on DB replicas
                userResults = await db.queryMany(
                  f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci=?',
                  [newestUserData.get('ci')]
                )
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user/results',
                      host_port = address,
                      body = { 'user_results': userResults, 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )
              else:
                ## FROM REPLICA
                # Try to UPDATE USER on DB replicas
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user',
                      host_port = address,
                      body = { 'user': newestUserData, 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )

                # Try to UPDATE USER_TESTS on DB replicas
                userTests = await Go(
                  'GET',
                  '/sync_user/tests',
                  host_port = newestUserData.get('db-address'),
                  body= { 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                ).as_coroutine()
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user/tests',
                      host_port = address,
                      body = { 'user_tests': userTests, 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )

                # Try to UPDATE USER_RESULTS on DB replicas
                userResults = await Go(
                  'GET',
                  '/sync_user/results',
                  host_port = newestUserData.get('db-address'),
                  body= { 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                ).as_coroutine()
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    Go(
                      'PUT',
                      '/sync_user/results',
                      host_port = address,
                      body = { 'user_results': userResults, 'user_ci': newestUserData.get('ci'), 'replicas_secret': REPLICAS_SECRET }
                    ).as_coroutine()
                    for address
                    in REPLICAS_ADDRESSES
                  ],
                  return_exceptions = True
                )
                ## after updating replicas, proceed to update local
                # user data
                await db.queryOne(f'''
                  INSERT OR REPLACE
                  INTO {USERS_TABLE} (ci, email, name, last_name, phone, session_token, data_version)
                  VALUES (:ci, :email, :name, :last_name, :phone, :session_token, :data_version)
                  ''',
                  newestUserData
                )
                # user-tests data
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    db.queryOne(f'''
                        INSERT OR REPLACE
                        INTO {USERS_TESTS_TABLE} (user_ci, test_id)
                        VALUES (:user_ci, :test_id)
                      ''',
                      test
                    )
                    for test
                    in userTests
                  ],
                  return_exceptions = True
                )
                # user-results data
                await asyncio.gather(
                  *[ #this list is spread into the gather method
                    db.queryOne(f'''
                        INSERT OR REPLACE
                        INTO {RESULTS_TABLE} (questions, answers, score_per_question, score, user_ci, test_id)
                        VALUES (:questions, :answers, :score_per_question, :score, :user_ci, :test_id)
                      ''',
                      result
                    )
                    for result
                    in userResults
                  ],
                  return_exceptions = True
                )
              ## END DATA REPLICATION
              exp = datetime.utcnow() + timedelta(minutes=120)
              token = jwt.encode(
                { 'user': { 'ci': newestUserData['ci'], 'email': newestUserData['email'] }, 'exp': exp },
                SECRET
              )

              newestUserData['session_token'] = token.decode('utf-8')

              await db.queryOne(
                f'UPDATE {USERS_TABLE} SET session_token=? WHERE ci=?',
                [newestUserData['session_token'], ci]
              )

              body = { 'user': newestUserData }
              header = { **reqHeader, 'code': 200 }
            else:
              body = { 'error_code': 'duplicate-session' }
              header = { **reqHeader, 'code': 403 }
          else:
            body = { 'error_code': 'invalid-credentials' }
            header = { **reqHeader, 'code': 403 }
          
        else:
          body = { 'error_code': 'user-does-not-exists' }
          header = { **reqHeader, 'code': 400 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
    
    return header, body

async def logout(reqHeader, reqBody, server_inst):
    db = server_inst._server_vars.get('db')

    ci = reqBody.get('ci')

    body = {}
    header = {}

    ## CHECK IF DATA IS COMPLETE
    if isinstance(ci, int):
      ## CHECK IF USER ALREADY EXISTS IN LOCAL DB
      try:
        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=?',
          [ci]
        )
        if (userData):
          userData = await db.queryOne(
            f'UPDATE {USERS_TABLE} SET session_token=? WHERE ci=?',
            ["", ci]
          )

          body = { 'message': "successful logout" }
          header = { **reqHeader, 'code': 200 }
          
        else:
          body = { 'error_code': 'user-does-not-exists' }
          header = { **reqHeader, 'code': 400 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
    
    return header, body