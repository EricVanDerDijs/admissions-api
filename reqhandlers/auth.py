import os, sys, traceback, json, asyncio
from datetime import datetime, timedelta
import jwt

sys.path.append("..")
from db.tables_definitions import USERS_TABLE
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
                exp = datetime.utcnow() + timedelta(hours=12)
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
      ## CHECK IF USER ALREADY EXISTS IN LOCAL DB
      try:
        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=?',
          [ci]
        )
        if (userData):
          if(
            userData['ci'] == ci and
            userData['email'] == email
          ):
            exp = datetime.utcnow() + timedelta(hours=12)
            token = jwt.encode(
              { 'user': { 'ci': userData['ci'], 'email': userData['email'] }, 'exp': exp },
              SECRET
            )

            userData['session_token'] = token.decode('utf-8')

            await db.queryOne(
              f'UPDATE {USERS_TABLE} SET session_token=? WHERE ci=?',
              [userData['session_token'], ci]
            )

            body = { 'user': userData }
            header = { **reqHeader, 'code': 200 }

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