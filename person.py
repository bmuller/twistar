from twistdb import DBObject
import sys
from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.python import log


log.startLogging(sys.stdout)
log.msg("starting...")


class User(twistdb.DBObject):
    pass
    

def complete(users):
    #log.msg("id is: %s" % str(user.id))
    #users.age = 44
    #users.save()
    log.msg("result: %s" % str(users))
    log.msg("done")
    reactor.stop()

def problem(error):
    log.msg("error: %s" % error)
    reactor.stop()

DBObject.DBPOOL = adbapi.ConnectionPool('MySQLdb', db='twisteddb', user='twisteddb', passwd='tw1$t3dd8')
#dbobject.DBPOOL.runQuery("describe users").addCallback(complete).addErrback(problem)
#dbobject.DBPOOL.runQuery("update users set age=%s where id=%s", [69, 58]).addCallback(complete).addErrback(problem)
#User.createTable() #.addCallback(complete).addErrback(problem)

#u = User()
#u.first_name = "brian"
#u.last_name = "muller test again"
#u.age = 20
#u.save().addCallback(complete).addErrback(problem)

#u.first_name = "your mom"
#u.save()
#dbobject.DBPOOL.runQuery("INSERT INTO users (first_name,last_name) VALUES(%s,%s)", ("brian", "muller"))

#User.find(where=['last_name = ?', 'muller test again']).addCallback(complete)

User.deleteAll()

reactor.callLater(2, reactor.stop)
reactor.run()

