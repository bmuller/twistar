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

def problem(error):
    log.msg("error: %s" % error)
    reactor.stop()

DBConfig.DBPOOL = adbapi.ConnectionPool('MySQLdb', db='twisteddb', user='twisteddb', passwd='tw1$t3dd8')
DBConfig.LOG = True

def handlePictures(pictures):
    for pic in pictures:
        log.msg("found picture: %s" % str(pic))
    log.msg("finale")
    reactor.stop()

def done(*args):
    pic = args[0][0][1]
    user = args[0][1][1]
    pic.user.set(user).addCallback(complete)
    #User.find(1)
    #pic.user.get().addCallback(complete)
    

#d = DeferredList([Picture.find(1), User.find(1)]).addCallback(done)
User.find(1).addCallback(complete)

reactor.callLater(2, reactor.stop)
reactor.run()

