import os
from socketserver.server import Server
from db.database import Database
from reqhandlers.sync import sync_getUser, sync_insertUser, sync_deleteUser
from reqhandlers.auth import signup, signin, logout
from reqhandlers.tests import getTest, enroll, generateTest

INIT_DB = os.getenv('INIT_DB', False)
db = Database('./storage/admissions.db', initialize = INIT_DB)

serv = Server(host='0.0.0.0', port = 80)

serv.use('db', db)

serv.get('/sync_user', sync_getUser)
serv.post('/sync_user', sync_insertUser)
serv.delete('/sync_user', sync_deleteUser)

serv.post('/signup', signup)
serv.post('/signin', signin)
serv.post('/logout', logout)

serv.get('/tests/user', getTest)
serv.post('/tests/user/enroll', enroll)
serv.get('/tests/new', generateTest)

serv.run()
