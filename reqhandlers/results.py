import os, sys, json, traceback, random
from datetime import datetime, timedelta
import jwt

sys.path.append("..")
from db.tables_definitions import USERS_TABLE, TESTS_TABLE, RESULTS_TABLE, QUESTIONS_TABLE
from socketserver.go import Go

SECRET = os.getenv('SECRET', 'secret')

async def calcResult(reqHeader, reqBody, server_inst):
  db = server_inst._server_vars.get('db')

  token = reqBody.get('token', '')
  test_id = reqBody.get('test_id')
  location_code = reqBody.get('location_code')
  answers = reqBody.get('answers')

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
    isinstance(location_code, str) and
    isinstance(answers, list) and
    len(answers) == 5
  ):
    try:
      test = await db.queryOne(f'SELECT * FROM {TESTS_TABLE} WHERE id = ?', [test_id])
      if ( # CHECK IF THE PROVIDED LOCATION CODE MATCHES
        test and
        test.get('location_code') == location_code
      ):
        generatedTest = await db.queryOne(
          f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci = ? AND test_id = ?',
          [user.get('ci'), test_id]
        )
        # CHECK IF THE USER HAS ALREADY GENERATED THE TEST
        if generatedTest:
          now = datetime.utcnow()
          test_start = datetime.utcfromtimestamp(test.get('test_start'))
          test_end = datetime.utcfromtimestamp(test.get('test_end'))

          if( # CHECK IF THE TEST TIME IS RUNNING
            now >= test_start and
            now <= test_end
          ):
            # GET TEST QUESTIONS
            questions = json.loads( generatedTest.get('questions') )
            placeholders = ['?' for x in questions]
            testQuestions = await db.queryMany(
              f'SELECT * FROM {QUESTIONS_TABLE} WHERE id IN {"("+",".join(placeholders)+")"}',
              questions
            )

            # GET TEST RESULTS
            score_per_question = []
            score = 0.0
            for i, question in enumerate(testQuestions):
              # Check question result
              if (question.get('answ_index') == answers[i]):
                score_per_question.append( question.get('score') )
                score += question.get('score')
              else:
                score_per_question.append( 0.0 )
              # Remove answer from question
              testQuestions[i].pop('answ_index', None)
            
            # ENCODE DATA
            jsonAnswers = json.dumps(answers)
            jsonScorePerQuestion = json.dumps(score_per_question)

            try:
              await db.queryOne(f'''
                  UPDATE {RESULTS_TABLE}
                  SET answers = ?, score_per_question = ?, score = ?
                  WHERE user_ci = ? AND test_id = ?
                ''',
                [jsonAnswers, jsonScorePerQuestion, score, user.get('ci'), test_id]
              )

              # Every write operation updates current user's data_version
              await db.queryOne(
                f'UPDATE {USERS_TABLE} SET data_version = data_version + 1 WHERE ci = ?',
                [user.get('ci')]
              )
              
              test.pop('location_code', None)
              test['questions'] = testQuestions
              test['answers'] = answers
              test['score_per_question'] = score_per_question
              test['score'] = score

              body = { 'result': test }
              header = { **reqHeader, 'code': 200 }
            except Exception as e:
              traceback.print_exc()
              body = { 'error_code': 'internal-error', 'error': repr(e) }
              header = { **reqHeader, 'code': 500 }
          else:
            body = { 'error_code': 'test-missed' }
            header = { **reqHeader, 'code': 403 }
        else:
          body = { 'error_code': 'test-has-not-been-generated' }
          header = { **reqHeader, 'code': 403 }
      else:
        body = { 'error_code': 'wrong-location-code' }
        header = { **reqHeader, 'code': 403 }
    except Exception as e:
      traceback.print_exc()
      body = { 'error_code': 'internal-error', 'error': repr(e) }
      header = { **reqHeader, 'code': 500 }
  else:
    body = { 'error_code': 'missing-params' }
    header = { **reqHeader, 'code': 400 }
    
  return header, body

async def getResult(reqHeader, reqBody, server_inst):
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
      result = await db.queryOne(
        f'SELECT * FROM {RESULTS_TABLE} WHERE user_ci = ? AND test_id = ?',
        [user.get('ci'), test_id]
      )
      if (result):
        test = await db.queryOne(f'SELECT * FROM {TESTS_TABLE} WHERE id = ?', [test_id])

        questions = json.loads( result.get('questions') )
        placeholders = ['?' for x in questions]
        testQuestions = await db.queryMany(
          f'SELECT * FROM {QUESTIONS_TABLE} WHERE id IN {"("+",".join(placeholders)+")"}',
          questions
        )

        for i, question in enumerate(testQuestions):
          testQuestions[i].pop('answ_index', None)

        score = result.get('score')
        answers = json.loads( result.get('answers') )
        score_per_question = json.loads( result.get('score_per_question') )

        test.pop('location_code', None)
        test['questions'] = testQuestions
        test['score'] = score
        test['answers'] = answers
        test['score_per_question'] = score_per_question

        body = { 'result': test }
        header = { **reqHeader, 'code': 200 }
      else:
        body = { 'result': result }
        header = { **reqHeader, 'code': 200 }
    except Exception as e:
      traceback.print_exc()
      body = { 'error_code': 'internal-error', 'error': repr(e) }
      header = { **reqHeader, 'code': 500 }
  else:
    body = { 'error_code': 'missing-params' }
    header = { **reqHeader, 'code': 400 }
    
  return header, body