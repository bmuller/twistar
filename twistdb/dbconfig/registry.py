from BermiInflector.Inflector import Inflector

# might be able to use 'twisted.python.reflect.namedAny' instead of registering classes

class Registry:
    SCHEMAS = {}
    REGISTRATION = {}
    IMPL = None
    DBPOOL = None

    @classmethod
    def register(_, *klasses):
        for klass in klasses:
            Registry.REGISTRATION[klass.__name__] = klass


    @classmethod
    def getClass(_, name):
        if not Registry.REGISTRATION.has_key(name):
            raise RuntimeError, "You never registered the class named %s" % name
        return Registry.REGISTRATION[name]
    
    
    @classmethod
    def getConfig(klass):
        if Registry.IMPL is not None:
            return Registry.IMPL
        
        if Registry.DBPOOL is None:
            msg = "You must set Registry.DBPOOL to a adbapi.ConnectionPool before calling this method."
            raise RuntimeError, msg
        dbapi = Registry.DBPOOL.dbapi
        if dbapi.__name__ == "MySQLdb":
            from mysql import MySQLDBConfig            
            Registry.IMPL = MySQLDBConfig(dbapi)
        elif dbapi.__name__ == "sqlite3":
            from sqlite import SQLiteDBConfig            
            Registry.IMPL = SQLiteDBConfig(dbapi)
        else:
            raise NotImplementedError, "twisteddb does not support the %s driver" % dbapi.__name__
        
        return Registry.IMPL


