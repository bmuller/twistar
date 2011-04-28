from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.dbobject import DBObject
from twistar.registry import Registry

#from sqlite_config import initDB, tearDownDB
from mysql_config import initDB, tearDownDB
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

class Boy(DBObject):
    HASMANY = [{'name': 'nicknames', 'as': 'nicknameable'}]

class Girl(DBObject):
    HASMANY = [{'name': 'nicknames', 'as': 'nicknameable'}]    

class Nickname(DBObject):
    BELONGSTO = [{'name': 'nicknameable', 'polymorphic': True}]

class Pen(DBObject):
    pass

class Table(DBObject):
    pass

Registry.register(Picture, User, Avatar, FakeObject, FavoriteColor)
Registry.register(Boy, Girl, Nickname)
Registry.register(Pen, Table)
