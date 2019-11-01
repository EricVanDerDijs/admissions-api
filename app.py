import os
from socketserver.server import Server
from db.database import Database
from reqhandlers.sync import (sync_getUser, sync_insertUser,
sync_deleteUser, sync_upsertUser, sync_getUserTests,
sync_upsertUserTests, sync_getUserResults, sync_upsertUserResults)
from reqhandlers.auth import signup, signin, logout
from reqhandlers.tests import getTest, enroll, generateTest
from reqhandlers.results import calcResult, getResult

INIT_DB = os.getenv('INIT_DB', False)
db = Database('./storage/admissions.db', initialize = INIT_DB)

serv = Server(host='0.0.0.0', port = 80)

serv.use('db', db)

serv.get('/sync_user', sync_getUser)
serv.post('/sync_user', sync_insertUser)
serv.delete('/sync_user', sync_deleteUser)
serv.put('/sync_user', sync_upsertUser)

serv.get('/sync_user/tests', sync_getUserTests)
serv.put('/sync_user/tests', sync_upsertUserTests)

serv.get('/sync_user/results', sync_getUserResults)
serv.put('/sync_user/results', sync_upsertUserResults)

serv.post('/signup', signup)
serv.post('/signin', signin)
serv.post('/logout', logout)

serv.get('/tests/user', getTest)
serv.post('/tests/user/enroll', enroll)
serv.get('/tests/new', generateTest)

serv.post('/results', calcResult)
serv.get('/results/test', getResult)

serv.run()
