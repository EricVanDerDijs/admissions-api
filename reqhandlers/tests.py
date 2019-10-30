import os, sys, traceback, json, asyncio
from datetime import datetime, timedelta
import jwt

sys.path.append("..")
from db.tables_definitions import USERS_TABLE, TESTS_TABLE, RESULTS_TABLE
from socketserver.go import Go

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
    allTests = await db.queryOne(f'SELECT * FROM {TESTS_TABLE}')
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
    
    body = { 'tests': allTests }
    header = { **reqHeader, 'code': 200 }

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
  try:
    enrolledTest = await db.queryOne(f'''
        SELECT * FROM {USERS_TESTS_TABLE}
        WHERE user_ci = ? AND test_id = ?
      ''',
      [user.get('ci'), test_id]
    )

    if (enrolledTest):
      body = { 'error_code': 'user-already-enrolled' }
      header = { **reqHeader, 'code': 409 }

    else:
      try:
        await db.queryOne(f'''
            INSERT INTO {USERS_TESTS_TABLE} (user_ci, test_id)
            VALUES (?, ?)
          ''',
          [user.get('ci'), test_id]
        )

        body = { 'test_id': test_id, 'message': 'enrolled successfully!' }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }


  except Exception as e:
    traceback.print_exc()
    body = { 'error_code': 'internal-error', 'error': repr(e) }
    header = { **reqHeader, 'code': 500 }
    
  return header, body

