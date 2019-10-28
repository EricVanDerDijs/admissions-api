import os
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
    print('Initializing DB...')
    print('Dropping Tables...')
    conn.execute(f'DROP TABLE IF EXISTS {USERS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {TESTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {USERS_TESTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {QUESTIONS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {QUESTIONS_TESTS_TABLE}')
    conn.execute(f'DROP TABLE IF EXISTS {RESULTS_TABLE}')
    
    print('Creating Tables...')
    conn.execute(USERS_TABLE_DEFINITIONS)
    conn.execute(TESTS_TABLE_DEFINITIONS)
    conn.execute(USERS_TESTS_TABLE_DEFINITIONS)
    conn.execute(QUESTIONS_TABLE_DEFINITIONS)
    conn.execute(QUESTIONS_TESTS_TABLE_DEFINITIONS)
    conn.execute(RESULTS_TABLE_DEFINITIONS)

    # SECRET = os.getenv('SECRET', None)
    # adminPsw = hash_password('admin123456', SECRET)
    print('Populating users with Admin user...')
    conn.executescript(
      f'''INSERT INTO {USERS_TABLE}
      (ci, name, last_name, phone, email, role)
      VALUES (0, "admission", "admin", "0", "admision@ucv.com.ve", "admin")'''
    )
    conn.commit()
