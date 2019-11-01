import os, sys, traceback, asyncio
import jwt
from datetime import datetime, timedelta
sys.path.append("..")
from db.tables_definitions import USERS_TABLE, USERS_TESTS_TABLE, RESULTS_TABLE

REPLICAS_SECRET = os.getenv('REPLICAS_SECRET')

async def sync_getUser(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  ci = reqBody.get('ci')
  email = reqBody.get('email')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    sql = ''
    params = []
    userData = None

    if ( # body has both params
      isinstance(ci, int) and
      isinstance(email, str)
    ):
      sql = f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?'
      params = [ci, email]
    elif isinstance(ci, int): # body has ci
      sql = f'SELECT * FROM {USERS_TABLE} WHERE ci=?'
      params = [ci]
    elif isinstance(email, str): # body has email
      sql = f'SELECT * FROM {USERS_TABLE} WHERE email=?'
      params = [email]

    if (sql and params):
      try:
        userData = await db.queryOne(sql, params) # if no user is found it returns none

        body = { 'user': userData }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_deleteUser(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  ci = reqBody.get('ci')
  email = reqBody.get('email')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    sql = ''
    params = []
    userData = None

    if ( # body has both params
      isinstance(ci, int) and
      isinstance(email, str)
    ):
      sql = f'DELETE FROM {USERS_TABLE} WHERE ci=? OR email=?'
      params = [ci, email]
    elif isinstance(ci, int): # body has ci
      sql = f'DELETE FROM {USERS_TABLE} WHERE ci=?'
      params = [ci]
    elif isinstance(email, str): # body has email
      sql = f'DELETE FROM {USERS_TABLE} WHERE email=?'
      params = [email]

    if (sql and params):
      try:
        await db.queryOne(sql, params) # a delete statement does not returns anything

        body = { 'user': { 'ci': ci, 'email': email }, 'message': 'deleted successfully' }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_insertUser(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  user = reqBody.get('user')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(user.get('ci'), int) and
      isinstance(user.get('email'), str) and
      isinstance(user.get('name'), str) and
      isinstance(user.get('last_name'), str) and
      isinstance(user.get('phone'), str)
    ):
      try:
        await db.queryOne(
          (f'INSERT INTO {USERS_TABLE} (ci, email, name, last_name, phone) '
          'VALUES (:ci, :email, :name, :last_name, :phone)'),
          user
        )

        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=?',
          [user.get('ci')]
        )

        body = { 'user': userData }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_upsertUser(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  user = reqBody.get('user')
  user['session_token'] = ''
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(user.get('ci'), int) and
      isinstance(user.get('email'), str) and
      isinstance(user.get('name'), str) and
      isinstance(user.get('last_name'), str) and
      isinstance(user.get('phone'), str) and 
      isinstance(user.get('data_version'), int)
    ):
      try:
        await db.queryOne(f'''
          INSERT OR REPLACE
          INTO {USERS_TABLE} (ci, email, name, last_name, phone, session_token, data_version)
          VALUES (:ci, :email, :name, :last_name, :phone, :session_token, :data_version)
          ''',
          user
        )

        userData = await db.queryOne(
          f'SELECT * FROM {USERS_TABLE} WHERE ci=?',
          [user.get('ci')]
        )

        body = { 'user': userData }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_getUserTests(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  user_ci = reqBody.get('user_ci')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(user_ci, int)
    ):
      try:
        userTests = await db.queryMany(
          f'SELECT * FROM {USERS_TESTS_TABLE} WHERE user_ci=?',
          [user_ci]
        )

        body = { 'tests': userTests }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_upsertUserTests(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  userTests = reqBody.get('user_tests')
  user_ci = reqBody.get('user_ci')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(userTests, list) and
      isinstance(user_ci, int)
    ):
      areAllTestOfTheSameUser = True
      for test in userTests:
        if test.get('user_ci') != user_ci:
          areAllTestOfTheSameUser = False

      if (areAllTestOfTheSameUser):
        try:
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

          userTests = await db.queryMany(
            f'SELECT * FROM {USERS_TESTS_TABLE} WHERE user_ci=?',
            [user_ci]
          )

          body = { 'tests': userTests }
          header = { **reqHeader, 'code': 200 }

        except Exception as e:
          traceback.print_exc()
          body = { 'error_code': 'internal-error', 'error': repr(e) }
          header = { **reqHeader, 'code': 500 }
      else:
        body = { 'error_code': 'inconsistent-data' }
        header = { **reqHeader, 'code': 400 }
    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_getUserResults(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  user_ci = reqBody.get('user_ci')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(user_ci, int)
    ):
      try:
        userResults = await db.queryMany(
          f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci=?',
          [user_ci]
        )

        body = { 'tests': userResults }
        header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body

async def sync_upsertUserResults(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  user_results = reqBody.get('user_results')
  user_ci = reqBody.get('user_ci')
  replicas_secret = reqBody.get('replicas_secret')

  body = {}
  header = {}

  if (replicas_secret == REPLICAS_SECRET):
    if (
      isinstance(user_results, list) and
      isinstance(user_ci, int)
    ):
      areAllResultsOfTheSameUser = True
      for result in user_results:
        if result.get('user_ci') != user_ci:
          areAllTestOfTheSameUser = False

      if (areAllResultsOfTheSameUser):
        try:
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
                in user_results
              ],
              return_exceptions = True
            )

          userTests = await db.queryMany(
            f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci=?',
            [user_ci]
          )

          body = { 'tests': userTests }
          header = { **reqHeader, 'code': 200 }

        except Exception as e:
          traceback.print_exc()
          body = { 'error_code': 'internal-error', 'error': repr(e) }
          header = { **reqHeader, 'code': 500 }
      else:
        body = { 'error_code': 'inconsistent-data' }
        header = { **reqHeader, 'code': 400 }
    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
  else:
    body = { 'error_code': 'client-not-allowed' }
    header = { **reqHeader, 'code': 403 }
  
  return header, body