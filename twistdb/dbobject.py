from twisted.python import log
from twisted.internet import defer


DBPOOL = None


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

    def execute(self, query, *args, **kwargs):
        log.msg("query: %s" % query)
        if len(args) > 0:
            log.msg("args: %s" % ",".join(map(lambda x: str(x), *args)))
        return DBPOOL.runQuery(query, *args, **kwargs)

    def getTypes(self, klass, vals):
        valswtype = {}
        for valname in vals.keys():
            valswtype[valname] = klass.COLS[valname]
        return valswtype
    
    def select(self, klass, where="", distinct=False):
        raise NotImplementedError

    def insert(self, klass, vals):
        raise NotImplementedError

    def delete(self, klass, where=""):
        raise NotImplementedError

    def update(self, klass, id, vals, where="", distinct=False):
        raise NotImplementedError

    def createTable(self, klass):
        raise NotImplementedError

    
class MySQLDBConfig(DBConfig):
    def select(self, klass, where="", distinct=False):
        raise NotImplementedError

    def insert(self, klass, vals):      
        args = (klass.tablename(), ",".join(vals.keys()))
        valswtype = self.getTypes(klass, vals)
        q = "INSERT INTO %s (%s) VALUES(" % args + klass.makeParams(valswtype) + ")"
        return self.execute(q, vals.values())

    def delete(self, klass, where=""):
        raise NotImplementedError

    def update(self, klass, id, vals, where="", distinct=False):
        raise NotImplementedError

    def createTable(self, klass, engine="innodb"):
        parts = []
        types = {self.dbapi.STRING: "VARCHAR(255)", self.dbapi.NUMBER: "INT"}
        for name, ctype in klass.COLS.iteritems():
            parts.append(name + " " + types[ctype])
        args = (klass.tablename(), ",".join(parts), engine)
        q = "CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, %s) ENGINE=%s" % args
        return self.execute(q)
        

class DBObject:
    def __init__(self, id=None, initial_values=None):
        self.id = id
        if initial_values is not None:
            cname = initial_values.__class__.__name__
            if cname == 'list' or cname == 'tuple':
                initial_values = self.__class__.columnRowsToHash(initial_values)
            for k, v in initial_values.items():
                setattr(self, k, v)

    @classmethod
    def makeParams(klass, args):
        dbapi = getDBAPI()
        nargs = []        
        if dbapi.paramstyle == 'format':
            argtypes = {dbapi.STRING: '%s', dbapi.NUMBER: '%i'}
            for name, vtype in args.iteritems():
                nargs.append(argtypes[vtype])
        else:
            raise NotImplementedError, "no support for param style %s" % dbapi.paramstyle
        return ",".join(nargs)


    @classmethod
    def tablename(klass):
        if hasattr(klass, 'TABLENAME'):
            return klass.TABLENAME
        else:
            return klass.__name__.lower() + 's'


    @classmethod
    def createTable(klass, *args, **kwargs):
        config = DBConfig.getConfig()
        return config.createTable(klass, *args, **kwargs)


    def save(self):
        config = DBConfig.getConfig()
        setargs = {}
        for name in self.__class__.COLS.keys():
            if hasattr(self, name):
                setargs[name] = getattr(self, name)
        if self.id is None:
            return config.insert(self.__class__, setargs)
        return config.update(self.__class__, self.id, setargs)

                
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
                                                        


