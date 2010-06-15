from twisted.python import log

class DBConfig:
    DBPOOL = None
    IMPL = None
    LOG = False
    SCHEMAS = {}
    REGISTRATION = {}

    @classmethod
    def register(_, *klasses):
        for klass in klasses:
            DBConfig.REGISTRATION[klass.__name__] = klass


    @classmethod
    def getClass(_, name):
        if not DBConfig.REGISTRATION.has_key(name):
            raise RuntimeError, "You never registered the class named %s" % name
        return DBConfig.REGISTRATION[name]
    
    
    @classmethod
    def getConfig(klass):
        if DBConfig.IMPL is not None:
            return DBConfig.IMPL
        
        if DBConfig.DBPOOL is None:
            msg = "You must set DBObject.DBPOOL to a adbapi.ConnectionPool before calling this method."
            raise RuntimeError, msg
        dbapi = DBConfig.DBPOOL.dbapi
        if dbapi.__name__ == "MySQLdb":
            from mysql import MySQLDBConfig            
            DBConfig.IMPL = MySQLDBConfig(dbapi)
        else:
            raise NotImplementedError, "twisteddb does not support the %s driver" % dbapi.__name__
        
        return DBConfig.IMPL

    def __init__(self, dbapi):
        self.dbapi = dbapi

    def log(self, query, args, kwargs):
        if not DBConfig.LOG:
            return
        log.msg("TWISTDB query: %s" % query)
        if len(args) > 0:
            log.msg("TWISTDB args: %s" % ",".join(map(lambda x: str(x), *args)))
        elif len(kwargs) > 0:
            log.msg("TWISTDB kargs: %s" % str(kwargs))        

    def execute(self, query, *args, **kwargs):
        self.log(query, args, kwargs)
        return DBConfig.DBPOOL.runQuery(query, *args, **kwargs)

    def executeTxn(self, txn, query, *args, **kwargs):
        self.log(query, args, kwargs)
        return txn.execute(query, *args, **kwargs)

    def select(self, klass, id=None, where=None, group=None, limit=None):
        raise NotImplementedError

    def insert(self, klass, vals):
        raise NotImplementedError

    def delete(self, klass, where):
        raise NotImplementedError

    def update(self, obj):
        raise NotImplementedError

    # Values is a row from a db, this method will create a hash with
    # key => value of colname => value based on the table description
    def valuesToHash(self, klass, txn, values):
        cols = self.getSchema(klass.tablename(), txn)
        h = {}
        for index in range(len(values)):
            colname = cols[index]
            h[colname] = values[index]
        return h


    def _doselect(self, txn, klass, q, args, one=False):
        self.executeTxn(txn, q, args)

        if one:
            vals = self.valuesToHash(klass, txn, txn.fetchone())
            return klass(vals)

        results = []
        for result in txn.fetchall():
            vals = self.valuesToHash(klass, txn, result)
            results.append(klass(vals))            
        return results    


    def getSchema(self, tablename, txn):
        if not DBConfig.SCHEMAS.has_key(tablename):
            self.executeTxn(txn, "DESCRIBE %s" % tablename)
            DBConfig.SCHEMAS[tablename] = [row[0] for row in txn.fetchall()]
        return DBConfig.SCHEMAS[tablename]
            

