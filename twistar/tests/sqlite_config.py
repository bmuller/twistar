from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.registry import Registry

def initDB(testKlass):
    location = testKlass.mktemp()
    Registry.DBPOOL = adbapi.ConnectionPool('sqlite3', location, check_same_thread=False)
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT, last_name TEXT, age INTEGER, dob DATE)""")
        txn.execute("""CREATE TABLE avatars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                       color TEXT, user_id INTEGER)""")        
        txn.execute("""CREATE TABLE pictures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                       size INTEGER, user_id INTEGER)""") 
        txn.execute("""CREATE TABLE favorite_colors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)""")
        txn.execute("""CREATE TABLE favorite_colors_users (favorite_color_id INTEGER, user_id INTEGER)""")
        txn.execute("""CREATE TABLE coltests (id INTEGER PRIMARY KEY AUTOINCREMENT, `select` TEXT, `where` TEXT)""")
    return Registry.DBPOOL.runInteraction(runInitTxn)


def tearDownDB(self):
    return defer.succeed(True)
                                                               
