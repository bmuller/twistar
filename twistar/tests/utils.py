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

class Catalogentry(DBObject):
    BELONGSTO = ['resource:polymorphic=True']

class Article(DBObject):
    HASMANY = ['catalogentries:polymorphic_as=resource']

class Sound(DBObject):
    HASMANY = ['catalogentries:polymorphic_as=resource']

class Image(DBObject):
    HASONE = ['catalogentries:polymorphic_as=resource']

Registry.register(Picture, User, Avatar, FakeObject, FavoriteColor)
Registry.register(Catalogentry, Article, Sound, Image)

