USERS_TABLE = 'users'
TESTS_TABLE = 'tests'
USERS_TESTS_TABLE = 'users_tests'
QUESTIONS_TABLE = 'questions'
QUESTIONS_TESTS_TABLE = 'questions_tests'
RESULTS_TABLE = 'results'

USERS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
    ci INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    session_token TEXT,
    data_version INTEGER DEFAULT 0,
    role TEXT DEFAULT 'user'
  )
'''

TESTS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {TESTS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    location_code TEXT NOT NULL,
    inscription_start INTEGER NOT NULL,
    inscription_end INTEGER NOT NULL,
    test_start INTEGER NOT NULL,
    test_end INTEGER NOT NULL
  )
'''

USERS_TESTS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {USERS_TESTS_TABLE} (
    user_ci INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    FOREIGN KEY(user_ci) REFERENCES users(ci),
    FOREIGN KEY(test_id) REFERENCES tests(id)
    PRIMARY KEY (user_ci, test_id)
  )
'''

QUESTIONS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {QUESTIONS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    options TEXT NOT NULL,
    answ_index INTEGER NOT NULL,
    score REAL NOT NULL,
    knowledge_area TEXT NOT NULL
  )
'''

QUESTIONS_TESTS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {QUESTIONS_TESTS_TABLE} (
    question_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    FOREIGN KEY(question_id) REFERENCES questions(id),
    FOREIGN KEY(test_id) REFERENCES tests(id)
    PRIMARY KEY (question_id, test_id)
  )
'''

RESULTS_TABLE_DEFINITIONS = f'''
  CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} (
    questions TEXT NOT NULL DEFAULT '[]',
    answers TEXT NOT NULL DEFAULT '[]',
    score_per_question TEXT NOT NULL DEFAULT '[]',
    score REAL NOT NULL DEFAULT 0.0,
    user_ci INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    FOREIGN KEY(user_ci) REFERENCES users(ci),
    FOREIGN KEY(test_id) REFERENCES tests(id)
    PRIMARY KEY (user_ci, test_id)
  )
'''


