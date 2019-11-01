import os, sys, json, traceback, random
from datetime import datetime, timedelta
import jwt

sys.path.append("..")
from socketserver.go import Go
from db.tables_definitions import (USERS_TABLE,
USERS_TESTS_TABLE,
TESTS_TABLE,
RESULTS_TABLE,
QUESTIONS_TABLE)

SECRET = os.getenv('SECRET', 'secret')

async def getTest(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  token = reqBody.get('token', '')

  body = {}
  header = {}

  # DECODE TOKEN, RETURN UNAUTHORIZED ERROR IF FAILS
  try:
    token = jwt.decode(token, SECRET)
  except Exception as e:
    body = { 'error_code': 'unauthorized' }
    header = { **reqHeader, 'code': 403 }
    return header, body
  
  user = token.get('user')
  try:
    userData = await db.queryOne(f'SELECT * FROM {USERS_TABLE} WHERE ci=?', [user.get('ci')])
    if (userData.get('session_token') == reqBody.get('token', '')):
      allTests = await db.queryMany(f'SELECT * FROM {TESTS_TABLE}')
      userTests = await db.queryMany(f'''
          SELECT * FROM {USERS_TESTS_TABLE}
          WHERE user_ci = ?
        ''',
        [user.get('ci')]
      )
      userResults = await db.queryMany(f'''
          SELECT * FROM {RESULTS_TABLE}
          WHERE user_ci = ?
        ''',
        [user.get('ci')]
      )

      for i, test in enumerate(allTests):
        allTests[i]['userHasEnrrolled'] = False
        allTests[i]['onGoingTest'] = False
        allTests[i]['hasResult'] = False

        now = datetime.utcnow()
        test_start = datetime.utcfromtimestamp(test.get('test_start'))
        test_end = datetime.utcfromtimestamp(test.get('test_end'))

        for enrrolledTest in userTests:
          if enrrolledTest.get('test_id') == test.get('id'):
            allTests[i]['userHasEnrrolled'] = True

        for result in userResults:
          if(
            now >= test_start and
            now <= test_end
          ):
            if result.get('answers') == '[]':
              allTests[i]['onGoingTest'] = True
              allTests[i]['hasResult'] = False 
            else:
              allTests[i]['onGoingTest'] = False
              allTests[i]['hasResult'] = True
          else:
            allTests[i]['onGoingTest'] = False
            allTests[i]['hasResult'] = True
        allTests[i].pop('location_code', None)
      
      body = { 'tests': allTests }
      header = { **reqHeader, 'code': 200 }
    else:
      body = { 'error_code': 'token-doesnt-match-current-session' }
      header = { **reqHeader, 'code': 403 } 
  except Exception as e:
    traceback.print_exc()
    body = { 'error_code': 'internal-error', 'error': repr(e) }
    header = { **reqHeader, 'code': 500 }
    
  return header, body


async def enroll(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  token = reqBody.get('token', '')
  test_id = reqBody.get('test_id')

  body = {}
  header = {}

  # DECODE TOKEN, RETURN UNAUTHORIZED ERROR IF FAILS
  try:
    token = jwt.decode(token, SECRET)
  except Exception as e:
    body = { 'error_code': 'unauthorized' }
    header = { **reqHeader, 'code': 403 }
    return header, body
  
  user = token.get('user')

  if (
    isinstance(test_id, int)
  ):
    try:
      userData = await db.queryOne(f'SELECT * FROM {USERS_TABLE} WHERE ci=?', [user.get('ci')])
      if (userData.get('session_token') == reqBody.get('token', '')):
        test = await db.queryOne(f'SELECT * FROM {TESTS_TABLE} WHERE id = ?', [test_id])
        if(test):
          now = datetime.utcnow()
          inscription_start = datetime.utcfromtimestamp(test.get('inscription_start'))
          inscription_end = datetime.utcfromtimestamp(test.get('inscription_end'))

          if (
            now >= inscription_start and
            now <= inscription_end
          ):
            enrolledTest = await db.queryOne(f'''
                SELECT * FROM {USERS_TESTS_TABLE}
                WHERE user_ci = ? AND test_id = ?
              ''',
              [user.get('ci'), test_id]
            )

            if not enrolledTest:
              try:
                await db.queryOne(f'''
                    INSERT INTO {USERS_TESTS_TABLE} (user_ci, test_id)
                    VALUES (?, ?)
                  ''',
                  [user.get('ci'), test_id]
                )

                # Every write operation updates current user's data_version
                await db.queryOne(
                  f'UPDATE {USERS_TABLE} SET data_version = data_version + 1 WHERE ci = ?',
                  [user.get('ci')]
                )

                body = { 'test_id': test_id, 'message': 'enrolled successfully!' }
                header = { **reqHeader, 'code': 200 }

              except Exception as e:
                traceback.print_exc()
                body = { 'error_code': 'internal-error', 'error': repr(e) }
                header = { **reqHeader, 'code': 500 }
            else:
              body = { 'error_code': 'user-already-enrolled' }
              header = { **reqHeader, 'code': 409 }
          else:
            body = { 'error_code': 'enrolment-period-missed' }
            header = { **reqHeader, 'code': 403 }
        else:
          body = { 'error_code': 'test-does-not-exists' }
          header = { **reqHeader, 'code': 400 }
      else:
        body = { 'error_code': 'token-doesnt-match-current-session' }
        header = { **reqHeader, 'code': 403 } 
    except Exception as e:
      traceback.print_exc()
      body = { 'error_code': 'internal-error', 'error': repr(e) }
      header = { **reqHeader, 'code': 500 }
  else:
    body = { 'error_code': 'missing-params' }
    header = { **reqHeader, 'code': 400 }
    
  return header, body

async def generateTest(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  token = reqBody.get('token', '')
  test_id = reqBody.get('test_id')
  location_code = reqBody.get('location_code')

  body = {}
  header = {}

  # DECODE TOKEN, RETURN UNAUTHORIZED ERROR IF FAILS
  try:
    token = jwt.decode(token, SECRET)
  except Exception as e:
    body = { 'error_code': 'unauthorized' }
    header = { **reqHeader, 'code': 403 }
    return header, body
  
  user = token.get('user')

  if (
    isinstance(test_id, int) and
    isinstance(location_code, str)
  ):
    try:
      userData = await db.queryOne(f'SELECT * FROM {USERS_TABLE} WHERE ci=?', [user.get('ci')])
      if (userData.get('session_token') == reqBody.get('token', '')):
        test = await db.queryOne(f'SELECT * FROM {TESTS_TABLE} WHERE id = ?', [test_id])
        if ( # CHECK IF THE PROVIDED LOCATION CODE MATCHES
          test and
          test.get('location_code') == location_code
        ):
          testAlreadyGenerated = await db.queryOne(
            f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci = ? AND test_id = ?',
            [user.get('ci'), test_id]
          )
          # CHECK IF THE USER HAS ALREADY GENERATED A TEST
          if not testAlreadyGenerated:
            now = datetime.utcnow()
            test_start = datetime.utcfromtimestamp(test.get('test_start'))
            test_end = datetime.utcfromtimestamp(test.get('test_end'))

            if( # CHECK IF THE TEST TIME IS RUNNING
              now >= test_start and
              now <= test_end
            ):
              enrollment = await db.queryOne(
                f'SELECT * FROM {USERS_TESTS_TABLE} WHERE user_ci = ? AND test_id = ?',
                [user.get('ci'), test_id]
              )
              if (enrollment): # CHECK IF THE USER HAS ENROLLED THE TEST

                # GET TEST QUESTIONS
                mathQuestions = await db.queryMany(
                  f'SELECT * FROM {QUESTIONS_TABLE} WHERE knowledge_area = "math"'
                )
                langQuestions = await db.queryMany(
                  f'SELECT * FROM {QUESTIONS_TABLE} WHERE knowledge_area = "language"'
                )

                # PICK QUESTIONS RANDOMLY DEPENDING ON TEST TYPE
                generatedTestQuestions = []
                if (test.get('type') == 'Humanidades'):
                  for i in range(5):
                    if i == 0:
                      generatedTestQuestions.append(
                        mathQuestions.pop( random.randrange(len(mathQuestions)) )
                      )
                    else:
                      generatedTestQuestions.append(
                        langQuestions.pop( random.randrange(len(mathQuestions)) )
                      )
                elif (rest.get('type') == 'Ciencias'):
                  for i in range(5):
                    if i == 0:
                      generatedTestQuestions.append(
                        langQuestions.pop( random.randrange(len(mathQuestions)) )
                      )
                    else:
                      generatedTestQuestions.append(
                        mathQuestions.pop( random.randrange(len(mathQuestions)) )
                      )
                
                # GENERATE CLEAN QUESTIONS FOR RESPONSE AND GET IDs FOR RESULT CREATION
                questions_without_answers = []
                questions_ids = []

                for i, question in enumerate(generatedTestQuestions):
                  questions_ids.append( question.get('id') )
                  questions_without_answers.append(question)
                  questions_without_answers[i].pop('answ_index', None)

                questions_ids = json.dumps(questions_ids)

                try:
                  await db.queryOne(f'''
                      INSERT INTO {RESULTS_TABLE} (questions, user_ci, test_id)
                      VALUES (?, ?, ?)
                    ''',
                    [questions_ids, user.get('ci'), test_id]
                  )

                  # Every write operation updates current user's data_version
                  await db.queryOne(
                    f'UPDATE {USERS_TABLE} SET data_version = data_version + 1 WHERE ci = ?',
                    [user.get('ci')]
                  )
                  
                  test.pop('location_code', None)
                  test['questions'] = questions_without_answers

                  body = { 'test': test }
                  header = { **reqHeader, 'code': 200 }
                except Exception as e:
                  traceback.print_exc()
                  body = { 'error_code': 'internal-error', 'error': repr(e) }
                  header = { **reqHeader, 'code': 500 }
              else:
                body = { 'error_code': 'user-not-enrolled' }
                header = { **reqHeader, 'code': 403 }
            else:
              body = { 'error_code': 'test-missed' }
              header = { **reqHeader, 'code': 403 }
          else:
            body = { 'error_code': 'test-already-generated' }
            header = { **reqHeader, 'code': 403 }
        else:
          body = { 'error_code': 'wrong-location-code' }
          header = { **reqHeader, 'code': 403 }
      else:
        body = { 'error_code': 'token-doesnt-match-current-session' }
        header = { **reqHeader, 'code': 403 } 
    except Exception as e:
      traceback.print_exc()
      body = { 'error_code': 'internal-error', 'error': repr(e) }
      header = { **reqHeader, 'code': 500 }
  else:
    body = { 'error_code': 'missing-params' }
    header = { **reqHeader, 'code': 400 }
    
  return header, body