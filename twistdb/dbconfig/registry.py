from BermiInflector.Inflector import Inflector
from dbconfig import DBConfig

class Registry:
    SCHEMAS = {}
    REGISTRATION = {}
    IMPL = None

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
        
        if DBConfig.DBPOOL is None:
            msg = "You must set DBConfig.DBPOOL to a adbapi.ConnectionPool before calling this method."
            raise RuntimeError, msg
        dbapi = DBConfig.DBPOOL.dbapi
        if dbapi.__name__ == "MySQLdb":
            from mysql import MySQLDBConfig            
            Registry.IMPL = MySQLDBConfig(dbapi)
        else:
            raise NotImplementedError, "twisteddb does not support the %s driver" % dbapi.__name__
        
        return Registry.IMPL


