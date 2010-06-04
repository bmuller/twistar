from twisted.python import log
DBPOOL = None
COLTYPE_STRING = 'string'
COLTYPE_INT = 'int'

def getDBAPI():
    if DBPOOL == None:
        msg = "You must set dbobject.DBPOOL to a adbapi.ConnectionPool before calling this method."
        raise RuntimeError, msg
    return DBPOOL.dbapi 


class DBConfig:
    @classmethod
    def getConfig(klass):
        dbapi = getDBAPI()
        if dbapi.__name__ == "MySQLdb":
            return MySQLDBConfig(dbapi)
        else:
            raise NotImplementedError, "twisteddb does not support the %s driver" % dbapi.__name__

    def __init__(self, dbapi):
        self.dbapi = dbapi

    def execute(self, query):
        log.msg("query: %s" % query)
        return DBPOOL.runQuery(query)
        
    def select(klass, where="", distinct=False):
        raise NotImplementedError

    def insert(klass, vals):
        raise NotImplementedError

    def delete(klass, where=""):
        raise NotImplementedError

    def update(klass, vals, where="", distinct=False):
        raise NotImplementedError

    def createTable(klass):
        raise NotImplementedError

    
class MySQLDBConfig(DBConfig):
    def select(klass, where="", distinct=False):
        raise NotImplementedError

    def insert(klass, vals):
        raise NotImplementedError

    def delete(klass, where=""):
        raise NotImplementedError

    def update(klass, vals, where="", distinct=False):
        raise NotImplementedError

    def createTable(klass, engine="innodb"):
        parts = []
        types = {self.dbapi.STRING: "VARCHAR(255)", self.dbapi.NUMBER: "INT"}
        for name, ctype in klass.COLS.iteritems():
            parts.append(name + " " + types[ctype])
        args = (klass.tablename(), parts.join(","), engine)
        q = "CREATE TABLE %s (id INT NOT NULL auto_increment, %s) ENGINE=%s" % args
        return self.execute(q)
        

class DBObject:
    def __init__(self, dbid=None, initial_values=None):
        self.dbid = dbid
        if initial_values is not None:
            cname = initial_values.__class__.__name__
            if cname == 'list' or cname == 'tuple':
                initial_values = self.__class__.columnRowsToHash(initial_values)
            for k, v in initial_values.items():
                setattr(self, k, v)

    @classmethod
    def makeWhereArgs(klass, args):
        dbapi = getDBAPI()
        if dbapi.paramstyle == 'format':
            nargs = []
            argtypes = {dbapi.STRING: '%s', dbapi.NUMBER: '%i'}
            for name, vtype in args.iteritems():
                nargs = name + "=" + argtypes[vtype]
        return nargs.join(",")


    @classmethod
    def tablename(klass):
        if hasattr(klass, 'TABLENAME'):
            tablename = klass.TABLENAME
        else:
            tablename = klass.__name__.lower() + 's'


    @classmethod
    def createTable(klass, *args, **kwargs):
        config = DBConfig.getConfig()
        config.createTable(klass, args, kwargs)

                
    def toHash(self, includeBlank=False, exclude=None, base=None):
        exclude = exclude or []
        h = base or {}
        for col in self.__class__.COLS:
            if col in exclude:
                continue
            value = getattr(self, col, None)
            if (value != None or includeBlank):
                h[col] = str(value)
        return h


    # Values is a row from a db, this method will create a hash with
    # key => value of colname => value based on the child class'
    # COLS class variable that contains the row names in order
    @classmethod
    def columnRowsToHash(klass, values):
        h = {}
        for index in range(len(values)):
            colname = klass.COLS[index]
            colvalue = values[index]
            h[colname] = colvalue
        return h
            

    @classmethod
    def fromValue(klass, dbpool, key, value):
        def _fromValue(txn, dbpool, key, value):
            if hasattr(klass, 'TABLENAME'):
                tablename = klass.TABLENAME
            else:
                tablename = klass.__name__.lower() + 's'
            q = "SELECT * FROM " + tablename + " WHERE " + key + " = %(value)s"
            txn.execute(q, {'value': value})
            rows = txn.fetchall()
            if len(rows) == 0:
                return None
            return klass(dbpool, rows[0][0], rows[0])
        return dbpool.runInteraction(_fromValue, dbpool, key, value)
                                                        


