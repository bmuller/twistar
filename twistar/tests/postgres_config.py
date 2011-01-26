from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.registry import Registry

CONNECTION = Registry.DBPOOL = adbapi.ConnectionPool('psycopg2', "dbname=twistar")

def initDB(testKlass):
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id SERIAL PRIMARY KEY,
                       first_name VARCHAR(255), last_name VARCHAR(255), age INT, dob DATE)""")
        txn.execute("""CREATE TABLE avatars (id SERIAL PRIMARY KEY, name VARCHAR(255),
                       color VARCHAR(255), user_id INT)""")        
        txn.execute("""CREATE TABLE pictures (id SERIAL PRIMARY KEY, name VARCHAR(255),
                       size INT, user_id INT)""") 
        txn.execute("""CREATE TABLE favorite_colors (id SERIAL PRIMARY KEY, name VARCHAR(255))""")
        txn.execute("""CREATE TABLE favorite_colors_users (favorite_color_id INT, user_id INT)""")
        txn.execute("""CREATE TABLE coltests (id SERIAL PRIMARY KEY, `select` VARCHAR(255), `where` VARCHAR(255))""")
        # tables used for polymorphic tests
        txn.execute("""CREATE TABLE catalogentries (id SERIAL PRIMARY KEY, name VARCHAR(255), resource_id INT, resource_type VARCHAR(32))""")
        txn.execute("""CREATE TABLE articles (id SERIAL PRIMARY KEY, name VARCHAR(255))""")
        txn.execute("""CREATE TABLE sounds (id SERIAL PRIMARY KEY, name VARCHAR(255))""")
        txn.execute("""CREATE TABLE images (id SERIAL PRIMARY KEY, name VARCHAR(255))""")
    return CONNECTION.runInteraction(runInitTxn)


def tearDownDB(self):
    def runTearDownDB(txn):
        txn.execute("DROP SEQUENCE users_id_seq CASCADE")        
        txn.execute("DROP TABLE users")

        txn.execute("DROP SEQUENCE avatars_id_seq CASCADE")        
        txn.execute("DROP TABLE avatars")

        txn.execute("DROP SEQUENCE pictures_id_seq CASCADE")        
        txn.execute("DROP TABLE pictures")
        
        txn.execute("DROP SEQUENCE favorite_colors_id_seq CASCADE")        
        txn.execute("DROP TABLE favorite_colors")

        txn.execute("DROP TABLE favorite_colors_users")

        txn.execute("DROP SEQUENCE coltests_id_seq CASCADE")
        txn.execute("DROP TABLE coltests")

        txn.execute("DROP SEQUENCE catalogentries_id_seq CASCADE")
        txn.execute("DROP TABLE catalogentries")

        txn.execute("DROP SEQUENCE article_id_seq CASCADE")
        txn.execute("DROP TABLE article")

        txn.execute("DROP SEQUENCE sound_id_seq CASCADE")
        txn.execute("DROP TABLE sound")

        txn.execute("DROP SEQUENCE images_id_seq CASCADE")
        txn.execute("DROP TABLE images")
    return CONNECTION.runInteraction(runTearDownDB)
                
