import dbobject
import MySQLdb
from twisted.enterprise import adbapi

class Person(dbobject.DBObject):
    COLS = {'first_name': MySQLdb.STRING,
            'last_name': MySQLdb.STRING,
            'age': MySQLdb.NUMBER}
    


dbobject.DBPOOL = adbapi.ConnectionPool('MySQLdb', 'twisteddb', 'twisteddb', 'tw1$t3dd8')
Person.createTable()
