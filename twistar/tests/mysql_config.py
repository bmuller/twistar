from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.registry import Registry

CONNECTION = Registry.DBPOOL = adbapi.ConnectionPool('MySQLdb', user="", passwd="", host="localhost", db="twistar")

def initDB(testKlass):
    def runInitTxn(txn):
        txn.execute("""CREATE TABLE users (id INT AUTO_INCREMENT,
                       first_name VARCHAR(255), last_name VARCHAR(255), age INT, dob DATE, PRIMARY KEY (id))""")
        txn.execute("""CREATE TABLE avatars (id INT AUTO_INCREMENT, name VARCHAR(255),
                       color VARCHAR(255), user_id INT, PRIMARY KEY (id))""")        
        txn.execute("""CREATE TABLE pictures (id INT AUTO_INCREMENT, name VARCHAR(255),
                       size INT, user_id INT, PRIMARY KEY (id))""") 
        txn.execute("""CREATE TABLE comments (id INT AUTO_INCREMENT, subject VARCHAR(255),
                       body TEXT, user_id INT, PRIMARY KEY (id))""") 
        txn.execute("""CREATE TABLE favorite_colors (id INT AUTO_INCREMENT, name VARCHAR(255), PRIMARY KEY (id))""")
        txn.execute("""CREATE TABLE favorite_colors_users (favorite_color_id INT, user_id INT)""")
        txn.execute("""CREATE TABLE coltests (id INT AUTO_INCREMENT, `select` VARCHAR(255), `where` VARCHAR(255), PRIMARY KEY (id))""")

        txn.execute("""CREATE TABLE boys (id INT AUTO_INCREMENT, `name` VARCHAR(255), PRIMARY KEY (id))""")
        txn.execute("""CREATE TABLE girls (id INT AUTO_INCREMENT, `name` VARCHAR(255), PRIMARY KEY (id))""")
        txn.execute("""CREATE TABLE nicknames (id INT AUTO_INCREMENT, `value` VARCHAR(255), `nicknameable_id` INT,
                       `nicknameable_type` VARCHAR(255), PRIMARY KEY(id))""")

        txn.execute("""CREATE TABLE pens (id INT AUTO_INCREMENT,
                       color VARCHAR(255), len INT, PRIMARY KEY (id), UNIQUE(color)) ENGINE=INNODB""")
        txn.execute("""CREATE TABLE tables (id INT AUTO_INCREMENT,
                       color VARCHAR(255), weight INT, PRIMARY KEY (id), UNIQUE(color)) ENGINE=INNODB""")

    return CONNECTION.runInteraction(runInitTxn)


def tearDownDB(self):
    def runTearDownDB(txn):
        txn.execute("DROP TABLE users")
        txn.execute("DROP TABLE avatars")
        txn.execute("DROP TABLE pictures")
        txn.execute("DROP TABLE comments")
        txn.execute("DROP TABLE favorite_colors")
        txn.execute("DROP TABLE favorite_colors_users")
        txn.execute("DROP TABLE coltests")
        txn.execute("DROP TABLE boys")
        txn.execute("DROP TABLE girls")
        txn.execute("DROP TABLE nicknames")
        txn.execute("DROP TABLE pens")
        txn.execute("DROP TABLE tables")
    return CONNECTION.runInteraction(runTearDownDB)
                
