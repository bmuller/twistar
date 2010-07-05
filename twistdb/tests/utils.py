from twisted.enterprise import adbapi

from twistdb import DBObject
from twistdb.dbconfig import Registry, DBConfig


class User(DBObject):
    HASMANY = ['pictures']

class Picture(DBObject):
    BELONGSTO = ['user']
    HASONE = ['type']

class Type(DBObject):
    pass

Registry.register(Picture, User, Type)


def initDB(location):
    DBConfig.DBPOOL = adbapi.ConnectionPool('sqlite3', location, check_same_thread=False)
    DBConfig.LOG = True
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT, last_name TEXT, age INTEGER)""")
        txn.execute("CREATE TABLE types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")        
        txn.execute("""CREATE TABLE pictures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                       size INTEGER, user_id INTEGER, type_id INTEGER)""")
    return DBConfig.DBPOOL.runInteraction(runInitTxn)
