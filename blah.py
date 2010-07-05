from twistdb import DBObject
from twistdb.dbconfig import Registry, DBConfig

import sys
from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from twisted.python import log


log.startLogging(sys.stdout)
log.msg("starting...")


class User(DBObject):
    HASMANY = ['pictures']

class Picture(DBObject):
    BELONGSTO = ['user']
    HASONE = ['type']

class Type(DBObject):
    pass

Registry.register(Picture, User, Type)

def complete(user):
    #log.msg("id is: %s" % str(user.id))
    #users.age = 44
    #users.save()
    log.msg("user: %s" % str(user))
    log.msg("done")
    reactor.stop()

def stop(r):
    reactor.stop()

def problem(error):
    log.msg("error: %s" % error)
    reactor.stop()

DBConfig.DBPOOL = adbapi.ConnectionPool('sqlite3', '/tmp/yourmom.db', check_same_thread=False)
DBConfig.LOG = True

def initDB():
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT, last_name TEXT, age INTEGER)""")
        #txn.execute("CREATE TABLE types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        #txn.execute("""CREATE TABLE pictures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
        #size INTEGER, user_id INTEGER, type_id INTEGER)""")
    return DBConfig.DBPOOL.runInteraction(runInitTxn)

def makeUser(result):
    u = User({'first_name': "First", 'last_name': "Last", 'age': 10})
    u.save()    

initDB().addCallback(makeUser)


reactor.callLater(2, reactor.stop)
reactor.run()

