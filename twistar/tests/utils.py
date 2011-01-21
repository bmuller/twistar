from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.dbobject import DBObject
from twistar.registry import Registry

from sqlite_config import initDB, tearDownDB
#from mysql_config import initDB, tearDownDB
#from postgres_config import initDB, tearDownDB

class User(DBObject):
    HASMANY = ['pictures']
    HASONE = ['avatar']
    HABTM = ['favorite_colors']

class Picture(DBObject):
    BELONGSTO = ['user']

class Avatar(DBObject):
    pass

class FavoriteColor(DBObject):
    HABTM = ['users']    

class FakeObject(DBObject):
    pass

class Coltest(DBObject):
    pass

class Child(DBObject):
    BELONGSTO = ['parent']

class Mother(DBObject):
    HAS_MANY = ['childs']

class Father(DBObject):
    HAS_MANY = ['childs']

Registry.register(Picture, User, Avatar, FakeObject, FavoriteColor)
Registry.register(Pen, Mother, Father)

