from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.registry import Registry
from txconnectionpool.txconnectionpool import TxConnectionPool

def initDB(testKlass):
    location = testKlass.mktemp()
    Registry.DBPOOL = TxConnectionPool('sqlite3', location, check_same_thread=False)
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT, last_name TEXT, age INTEGER, dob DATE)""")
        txn.execute("""CREATE TABLE avatars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                       color TEXT, user_id INTEGER)""")        
        txn.execute("""CREATE TABLE pictures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                       size INTEGER, user_id INTEGER)""") 
        txn.execute("""CREATE TABLE comments (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT,
                       body TEXT, user_id INTEGER)""") 
        txn.execute("""CREATE TABLE favorite_colors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)""")
        txn.execute("""CREATE TABLE favorite_colors_users (favorite_color_id INTEGER, user_id INTEGER)""")
        txn.execute("""CREATE TABLE coltests (id INTEGER PRIMARY KEY AUTOINCREMENT, `select` TEXT, `where` TEXT)""")

        txn.execute("""CREATE TABLE boys (id INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT)""")
        txn.execute("""CREATE TABLE girls (id INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT)""")        
        txn.execute("""CREATE TABLE nicknames (id INTEGER PRIMARY KEY AUTOINCREMENT, `value` TEXT, `nicknameable_id` INTEGER,
                       `nicknameable_type` TEXT)""")
        txn.execute("""CREATE TABLE blogposts (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       title TEXT, text TEXT)""")
        txn.execute("""CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT)""")
        txn.execute("""CREATE TABLE posts_categories (category_id INTEGER, blogpost_id INTEGER)""")

        txn.execute("""CREATE TABLE pens (id INTEGER PRIMARY KEY AUTOINCREMENT, color TEXT UNIQUE, len INTEGER)""");
        txn.execute("""CREATE TABLE tables (id INTEGER PRIMARY KEY AUTOINCREMENT, color TEXT UNIQUE, weight INTEGER)""");
        txn.execute("""CREATE TABLE pens_tables (pen_id INT, table_id INT)""")
        txn.execute("""CREATE TABLE rubbers (id INTEGER PRIMARY KEY AUTOINCREMENT, color TEXT, table_id INTEGER)""")
        
    return Registry.DBPOOL.runInteraction(runInitTxn)


def tearDownDB(self):
    return defer.succeed(True)
                                                               
