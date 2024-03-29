import os, random
from datetime import datetime, timedelta
from socketserver.utils import hash_password
from .tables_definitions import (USERS_TABLE,
TESTS_TABLE,
USERS_TESTS_TABLE,
QUESTIONS_TABLE,
QUESTIONS_TESTS_TABLE,
RESULTS_TABLE,
USERS_TABLE_DEFINITIONS,
TESTS_TABLE_DEFINITIONS,
USERS_TESTS_TABLE_DEFINITIONS,
QUESTIONS_TABLE_DEFINITIONS,
QUESTIONS_TESTS_TABLE_DEFINITIONS,
RESULTS_TABLE_DEFINITIONS)

def init_db(conn):
  with conn:
    print('')
    print('Initializing DB...')
    print('Dropping Tables...')
    conn.execute(f'DROP TABLE IF EXISTS {USERS_TESTS_TABLE}') # relationships first
    conn.execute(f'DROP TABLE IF EXISTS {QUESTIONS_TESTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {RESULTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {USERS_TABLE}')# data tables later
    conn.execute(f'DROP TABLE IF EXISTS {TESTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {QUESTIONS_TABLE}')
    
    print('Creating Tables...')
    conn.execute(USERS_TABLE_DEFINITIONS)
    conn.execute(TESTS_TABLE_DEFINITIONS)
    conn.execute(USERS_TESTS_TABLE_DEFINITIONS)
    conn.execute(QUESTIONS_TABLE_DEFINITIONS)
    conn.execute(QUESTIONS_TESTS_TABLE_DEFINITIONS)
    conn.execute(RESULTS_TABLE_DEFINITIONS)
    conn.commit()

    print('Populating users with Admin user...')
    sqlInserAdmin = f'''
      INSERT INTO {USERS_TABLE} (ci, name, last_name, phone, email, role)
      VALUES (0, "admission", "admin", "0", "admision@ucv.com.ve", "admin")
    '''
    conn.execute(sqlInserAdmin)

    print('Populating test with 2 tests...')
    test_1_insc_start = int(datetime.utcnow().timestamp())
    test_1_insc_end = int( (datetime.utcnow() + timedelta(minutes=30)).timestamp() )
    test_1_start = int(datetime.utcnow().timestamp())
    test_1_end = int( (datetime.utcnow() + timedelta(minutes=90)).timestamp() )

    test_2_insc_start = int(datetime.utcnow().timestamp())
    test_2_insc_end = int( (datetime.utcnow() + timedelta(minutes=90)).timestamp() )
    test_2_start = int( (datetime.utcnow() + timedelta(minutes=120)).timestamp() )
    test_2_end = int( (datetime.utcnow() + timedelta(minutes=150)).timestamp() )
    sqlInserTests = f'''
      INSERT INTO {TESTS_TABLE} (
        type,
        location_code,
        inscription_start,
        inscription_end,
        test_start,
        test_end
      ) VALUES (
        'Humanidades',
        'LOC_HUM_1',
        {test_1_insc_start},
        {test_1_insc_end},
        {test_1_start},
        {test_1_end}
      );

      INSERT INTO {TESTS_TABLE} (
        type,
        location_code,
        inscription_start,
        inscription_end,
        test_start,
        test_end
      ) VALUES (
        'Ciencias',
        'LOC_CIENC_1',
        {test_2_insc_start},
        {test_2_insc_end},
        {test_2_start},
        {test_2_end}
      );
    '''
    conn.executescript(sqlInserTests)

    print('Populating questions with 100 questions...')
    sqlInsertQuestions = ''
    for i in range(1, 101):
      answ_index = 1
      area = 'math' if (random.random() > 0.5) else 'language'
      sqlInsertQuestions += f'''
        INSERT INTO {QUESTIONS_TABLE} (question, options, answ_index, score, knowledge_area)
        VALUES (
          "Question {i}.",
          "[""Option {i}.1"", ""Option {i}.2"", ""Option {i}.3"", ""Option {i}.4""]",
          "{answ_index}",
          4.0,
          "{area}"
        );
      '''
    conn.executescript(sqlInsertQuestions)
    
    print('Adding questions to tests (50 each)...')
    sqlInsertQuestionsTest = ''
    for i in range(1, 101):
      if (i < 51):
        sqlInsertQuestionsTest += f'''
        INSERT INTO {QUESTIONS_TESTS_TABLE} (question_id, test_id)
        VALUES ({i}, 1);

        '''
      else:
        sqlInsertQuestionsTest += f'''
        INSERT INTO {QUESTIONS_TESTS_TABLE} (question_id, test_id)
        VALUES ({i}, 2);

        '''
    conn.executescript(sqlInsertQuestionsTest)
    print('Finishing...')
    conn.commit()
    print('')