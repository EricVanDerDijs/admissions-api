import os
import sys
import traceback
import jwt
from datetime import datetime, timedelta
sys.path.append("..")
from db.tables_definitions import USERS_TABLE

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