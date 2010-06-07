import dbobject
import MySQLdb
import sys
from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.python import log


log.startLogging(sys.stdout)
log.msg("starting...")


class User(dbobject.DBObject):
    COLS = {'first_name': MySQLdb.STRING,
            'last_name': MySQLdb.STRING,
            'age': MySQLdb.NUMBER}
    

def complete(result):
    log.msg("done: %s" % result)
    reactor.stop()

def problem(error):
    log.msg("error: %s" % error)
    reactor.stop()

dbobject.DBPOOL = adbapi.ConnectionPool('MySQLdb', db='twisteddb', user='twisteddb', passwd='tw1$t3dd8')
#dbobject.DBPOOL.runQuery("show tables").addCallback(complete).addErrback(problem)
#User.createTable() #.addCallback(complete).addErrback(problem)

u = User()
u.first_name = "brian"
u.last_name = "muller"
#u.age = 10
u.save().addCallback(complete).addErrback(problem)

#dbobject.DBPOOL.runQuery("INSERT INTO users (first_name,last_name) VALUES(%s,%s)", ("brian", "muller"))

reactor.callLater(2, reactor.stop)
reactor.run()

