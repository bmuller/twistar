from twistdb import DBObject
from twistdb.dbconfig import DBConfig

import sys
from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.python import log


log.startLogging(sys.stdout)
log.msg("starting...")


class User(DBObject):
    HASMANY = ['pictures']


class Picture(DBObject):
    BELONGSTO = ['user']

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

DBConfig.DBPOOL = adbapi.ConnectionPool('MySQLdb', db='twisteddb', user='twisteddb', passwd='tw1$t3dd8')
DBConfig.LOG = True

def handlePictures(pictures):
    for pic in pictures:
        log.msg("found picture with id of %i" % pic.id)
    reactor.stop()

def done(user):
    log.msg("user found with id: %i" % user.id)
    user.pictures.addCallback("handlePictures")
    reactor.stop()
    
User.find(1).addCallback(done)


reactor.callLater(2, reactor.stop)
reactor.run()

