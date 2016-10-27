from __future__ import absolute_import
from __future__ import print_function
from twistar.dbobject import DBObject
from twistar.registry import Registry

import os

DBTYPE = os.environ.get('DBTYPE', 'sqlite')
if DBTYPE == 'mysql':
    print("Using MySQL for tests")
    from . import mysql_config
    initDB = mysql_config.initDB
    tearDownDB = mysql_config.tearDownDB
elif DBTYPE == 'postgres':
    print("Using PostgreSQL for tests")
    from . import postgres_config
    initDB = postgres_config.initDB
    tearDownDB = postgres_config.tearDownDB
else:
    print("Using SQLite for tests")
    from . import sqlite_config
    initDB = sqlite_config.initDB
    tearDownDB = sqlite_config.initDB


class User(DBObject):
    HASMANY = ['pictures', 'comments']
    HASONE = ['avatar']
    HABTM = ['favorite_colors']


class Picture(DBObject):
    BELONGSTO = ['user']


class Comment(DBObject):
    BELONGSTO = ['user']


class Avatar(DBObject):
    pass


class FavoriteColor(DBObject):
    HABTM = ['users']


class Blogpost(DBObject):
    HABTM = [dict(name='categories', join_table='posts_categories')]


class Category(DBObject):
    HABTM = [dict(name='blogposts', join_table='posts_categories')]


class FakeObject(DBObject):
    pass


class Coltest(DBObject):
    pass


class Transaction(DBObject):
    pass


class Boy(DBObject):
    HASMANY = [{'name': 'nicknames', 'as': 'nicknameable'}]


class Girl(DBObject):
    HASMANY = [{'name': 'nicknames', 'as': 'nicknameable'}]


class Nickname(DBObject):
    BELONGSTO = [{'name': 'nicknameable', 'polymorphic': True}]


Registry.register(Picture, User, Comment, Avatar, FakeObject, FavoriteColor)
Registry.register(Boy, Girl, Nickname)
Registry.register(Blogpost, Category)
