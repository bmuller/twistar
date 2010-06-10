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
    

def complete(result, user):
    log.msg("id is: %s" % str(user.id))
    log.msg("done")
    reactor.stop()

def problem(error):
    log.msg("error: %s" % error)
    reactor.stop()

dbobject.DBPOOL = adbapi.ConnectionPool('MySQLdb', db='twisteddb', user='twisteddb', passwd='tw1$t3dd8')
#dbobject.DBPOOL.runQuery("show tables").addCallback(complete).addErrback(problem)
#User.createTable() #.addCallback(complete).addErrback(problem)

u = User()
u.first_name = "another"
u.last_name = "namer"
u.age = 20
#u.save().addCallback(complete, u).addErrback(problem)

u.first_name = "your mom"
#u.save()
#dbobject.DBPOOL.runQuery("INSERT INTO users (first_name,last_name) VALUES(%s,%s)", ("brian", "muller"))

User.find("id = 51").addCallback(complete)

reactor.callLater(2, reactor.stop)
reactor.run()

