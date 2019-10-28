import os
import sys
import traceback
from jose import jwt
from datetime import datetime, timedelta
sys.path.append("..")
from db.tables_definitions import USERS_TABLE

SECRET = os.getenv('SECRET', 'secret')

async def signup(reqHeader, reqBody, **server_vars):
    db = server_vars.get('db')

    ci = reqBody.get('ci')
    email = reqBody.get('email')
    phone = reqBody.get('phone')
    name = reqBody.get('name')
    last_name = reqBody.get('last_name')

    body = {}
    header = {}

    if (
      isinstance(ci, int) and
      isinstance(email, str) and
      isinstance(phone, str) and
      isinstance(name, str) and
      isinstance(last_name, str)
    ):
      try:
        # userData = await db.queryOne(
        #   f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?',
        #   [ci, email]
        # )
        # if (userData):
        if False:
          body = { 'error_code': 'user-already-exists' }
          header = { **reqHeader, 'code': 409 }
        else:
          tomorrowUtc = datetime.utcnow() + timedelta(days=1)
          token = jwt.encode(
            {
              'user': { 'ci': ci, 'email': email },
              'exp': tomorrowUtc.isoformat()
            },
            SECRET
          )
          await db.queryOne(
            (f'INSERT INTO {USERS_TABLE} (ci, email, name, last_name, phone, session_token) '
            'VALUES (:ci, :email, :name, :last_name, :phone, :session_token)'),
            {
              'ci': ci,
              'email': email,
              'name': name,
              'last_name': last_name,
              'phone': phone,
              'session_token': token
            }
          )
          
          userData = await db.queryOne(
            f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?',
            [ci, email]
          )

          body = {
            'user': userData,
          }
          header = { **reqHeader, 'code': 200 }

      except Exception as e:
        traceback.print_exc()
        body = { 'error_code': 'internal-error', 'error': repr(e) }
        header = { **reqHeader, 'code': 500 }

    else:
      body = { 'error_code': 'missing-params' }
      header = { **reqHeader, 'code': 400 }
    
    return header, body

# async def getUserByCIorEmail(reqHeader, reqBody, **server_vars):
#     db = server_vars.get('db')

#     ci = reqBody.get('ci')
#     email = reqBody.get('email')

#     body = {}
#     header = {}

#     sql = ''
#     params = []
#     userData = None

#     if ( # body has both params
#       isinstance(ci, int) and
#       isinstance(email, str)
#     ):
#       sql = f'SELECT * FROM {USERS_TABLE} WHERE ci=? OR email=?'
#       params = [ci, email]
#     elif isinstance(ci, int): # body has ci
#       sql = f'SELECT * FROM {USERS_TABLE} WHERE ci=?'
#       params = [ci]
#     elif isinstance(email, str): # body has email
#       sql = f'SELECT * FROM {USERS_TABLE} WHERE email=?'
#       params = [email]

#     if (sql and params):
#       try:
#         userData = await db.queryOne(sql, params) # if no user s found it returns none

#         if (userData):
#           body = { 'user': userData }
#           header = { **reqHeader, 'code': 200 }

#       except Exception as e:
#         traceback.print_exc()
#         body = { 'error_code': 'internal-error', 'error': repr(e) }
#         header = { **reqHeader, 'code': 500 }

#     else:
#       body = { 'error_code': 'missing-params' }
#       header = { **reqHeader, 'code': 400 }
    
#     return header, body