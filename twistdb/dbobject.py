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

    def log(self, query, args, kwargs):
        log.msg("query: %s" % query)
        if len(args) > 0:
            log.msg("args: %s" % ",".join(map(lambda x: str(x), *args)))
        elif len(kwargs) > 0:
            log.msg("kargs: %s" % str(kwargs))        

    def execute(self, query, *args, **kwargs):
        self.log(query, args, kwargs)
        return DBPOOL.runQuery(query, *args, **kwargs)

    def executeTxn(self, txn, query, *args, **kwargs):
        self.log(query, args, kwargs)
        return txn.execute(query, *args, **kwargs)

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

    def whereToString(self, where):
        w = WHERESTRS[where.wheretype]
        if where.isnot:
            w = "NOT " + w
        value = where.value
        if where.wheretype == STARTSWITH:
            value = self.FORMATCHAR + "%%"
        elif where.wheretype == ENDSWITH:
            value = "%%" + self.FORMATCHAR
        elif where.wheretype == CONTAINS:
            value = "%%" + self.FORMATCHAR + "%%"
        else:
            value = self.FORMATCHAR
        return (where, w, value)
    
class MySQLDBConfig(DBConfig):
    def select(self, klass, where="", distinct=False):
        def _doselect(txn, q):
            results = []
            self.executeTxn(txn, q)
            for result in txn.fetchall():
                results.append(klass(initial_values=result))
            return defer.succeed(results)
            
        if distinct:
            distinct = "DISTINCT "
        else:
            distinct = ""
        q = "SELECT %s* FROM %s" % (distinct, klass.tablename())
        if where != "":
            q += " WHERE %s" % where
        return DBPOOL.runInteraction(_doselect, q)


    def insert(self, obj, vals):
        def _doinsert(txn):
            klass = obj.__class__
            args = (klass.tablename(), ",".join(vals.keys()))
            valswtype = self.getTypes(klass, vals)
            params, values = klass.makeArgList(valswtype, vals)
            q = "INSERT INTO %s (%s) VALUES(" % args + params + ")"
            self.executeTxn(txn, q, values)            
            q = "SELECT LAST_INSERT_ID()"
            self.executeTxn(txn, q)            
            result = txn.fetchall()
            obj.id = result[0][0]
        return DBPOOL.runInteraction(_doinsert)


    def delete(self, klass, where=""):
        raise NotImplementedError


    def update(self, obj, vals):
        klass = obj.__class__
        args = (klass.tablename(), ",".join(vals.keys()))
        valswtype = self.getTypes(klass, vals)
        params, values = klass.makeArgList(valswtype, vals)
        q = "UPDATE %s SET (%s) VALUES(" % args + params + ")"
        return self.execute(q)


    def createTable(self, klass, engine="innodb"):
        parts = []
        types = {self.dbapi.STRING: "VARCHAR(255)", self.dbapi.NUMBER: "INT"}
        for name, ctype in klass.COLS.iteritems():
            parts.append(name + " " + types[ctype])
        args = (klass.tablename(), ",".join(parts), engine)
        q = "CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, %s) ENGINE=%s" % args
        return self.execute(q)
        

class DBObject:
    def __init__(self, initial_values=None):
        self.id = id
        if initial_values is not None:
            cname = initial_values.__class__.__name__
            if cname == 'list' or cname == 'tuple':
                initial_values = self.__class__.columnRowsToHash(initial_values)
            for k, v in initial_values.items():
                setattr(self, k, v)

    ## args is a dictionary {argname: type}
    ## values is a dictionary {argname: value}
    ## returns (arglist, values) where values is a
    ## list for all but pyformat, and a dictionary then
    @classmethod
    def makeArgList(klass, args, values):
        dbapi = getDBAPI()
        arglist = []        
        if dbapi.paramstyle == 'format':
            # yes, dbapi.NUMBER is %s - MySQLdb converts to string literal for numbers
            argtypes = {dbapi.STRING: '%s', dbapi.NUMBER: '%s'}
            for name, vtype in args.iteritems():
                arglist.append(argtypes[vtype])
            values = values.values()
        else:
            raise NotImplementedError, "no support for param style %s" % dbapi.paramstyle
        return (",".join(arglist), values)


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
            return config.insert(self, setargs)
        return config.update(self, setargs)

                
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
    def find(klass, where):
        config = DBConfig.getConfig()
        return config.select(klass, where)


    @classmethod
    def all(klass):
        return klass.find("")


    @classmethod
    def findByKey(klass, key, value):
        return klass.find("%s = %s" % (key, value))
