from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.registry import Registry

from txconnectionpool.txconnectionpool import TxConnectionPool

CONNECTION = Registry.DBPOOL = TxConnectionPool('psycopg2', "dbname=twistar")

def initDB(testKlass):
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id SERIAL PRIMARY KEY,
                       first_name VARCHAR(255), last_name VARCHAR(255), age INT, dob DATE)""")
        txn.execute("""CREATE TABLE avatars (id SERIAL PRIMARY KEY, name VARCHAR(255),
                       color VARCHAR(255), user_id INT)""")        
        txn.execute("""CREATE TABLE pictures (id SERIAL PRIMARY KEY, name VARCHAR(255),
                       size INT, user_id INT)""") 
        txn.execute("""CREATE TABLE comments (id SERIAL PRIMARY KEY, subject VARCHAR(255),
                       body TEXT, user_id INT)""") 
        txn.execute("""CREATE TABLE favorite_colors (id SERIAL PRIMARY KEY, name VARCHAR(255))""")
        txn.execute("""CREATE TABLE favorite_colors_users (favorite_color_id INT, user_id INT)""")
        txn.execute("""CREATE TABLE coltests (id SERIAL PRIMARY KEY, "select" VARCHAR(255), "where" VARCHAR(255))""")

        txn.execute("""CREATE TABLE boys (id SERIAL PRIMARY KEY, "name" VARCHAR(255))""")
        txn.execute("""CREATE TABLE girls (id SERIAL PRIMARY KEY, "name" VARCHAR(255))""")
        txn.execute("""CREATE TABLE nicknames (id SERIAL PRIMARY KEY, "value" VARCHAR(255), "nicknameable_id" INT,
                       "nicknameable_type" VARCHAR(255))""")
        txn.execute("""CREATE TABLE blogposts (id SERIAL PRIMARY KEY,
                       title VARCHAR(255), text VARCHAR(255))""")
        txn.execute("""CREATE TABLE categories (id SERIAL PRIMARY KEY,
                       name VARCHAR(255))""")
        txn.execute("""CREATE TABLE posts_categories (category_id INT, blogpost_id INT)""")

        txn.execute("""CREATE TABLE pens (id SERIAL PRIMARY KEY, color VARCHAR(255) UNIQUE, len INT)""");
        txn.execute("""CREATE TABLE tables (id SERIAL PRIMARY KEY, color VARCHAR(255) UNIQUE, weight INT)""");
        txn.execute("""CREATE TABLE pens_tables (pen_id INT, table_id INT)""")
        txn.execute("""CREATE TABLE rubbers (id SERIAL PRIMARY KEY, color VARCHAR(255), table_id INT)""");


    return CONNECTION.runInteraction(runInitTxn)


def tearDownDB(self):
    def runTearDownDB(txn):
        txn.execute("DROP SEQUENCE users_id_seq CASCADE")        
        txn.execute("DROP TABLE users")

        txn.execute("DROP SEQUENCE avatars_id_seq CASCADE")        
        txn.execute("DROP TABLE avatars")

        txn.execute("DROP SEQUENCE pictures_id_seq CASCADE")        
        txn.execute("DROP TABLE pictures")
        
        txn.execute("DROP SEQUENCE comments_id_seq CASCADE")        
        txn.execute("DROP TABLE comments")
        
        txn.execute("DROP SEQUENCE favorite_colors_id_seq CASCADE")        
        txn.execute("DROP TABLE favorite_colors")

        txn.execute("DROP TABLE favorite_colors_users")

        txn.execute("DROP SEQUENCE coltests_id_seq CASCADE")
        txn.execute("DROP TABLE coltests")

        txn.execute("DROP SEQUENCE boys_id_seq CASCADE")
        txn.execute("DROP TABLE boys")

        txn.execute("DROP SEQUENCE girls_id_seq CASCADE")
        txn.execute("DROP TABLE girls")

        txn.execute("DROP SEQUENCE nicknames_id_seq CASCADE")
        txn.execute("DROP TABLE nicknames")
        
        txn.execute("DROP SEQUENCE blogposts_id_seq CASCADE")
        txn.execute("DROP TABLE blogposts")
        
        txn.execute("DROP SEQUENCE categories_id_seq CASCADE")
        txn.execute("DROP TABLE categories")
        
        txn.execute("DROP TABLE posts_categories")
        
        txn.execute("DROP SEQUENCE pens_id_seq CASCADE")
        txn.execute("DROP TABLE pens")
        
        txn.execute("DROP SEQUENCE tables_id_seq CASCADE")
        txn.execute("DROP TABLE tables")
        
        txn.execute("DROP SEQUENCE rubbers_id_seq CASCADE")
        txn.execute("DROP TABLE rubbers")
        
        txn.execute("DROP TABLE pens_tables")
        
    return CONNECTION.runInteraction(runTearDownDB)
                
