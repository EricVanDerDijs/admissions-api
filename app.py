import os
from socketserver.server import Server
from db.database import Database
from reqhandlers.auth import signup

INIT_DB = os.getenv('INIT_DB', False)
db = Database('./storage/admissions.db', initialize = INIT_DB)

serv = Server(host='0.0.0.0', port = 80)

serv.use('db', db)

serv.post('/signup', signup)

serv.run()
