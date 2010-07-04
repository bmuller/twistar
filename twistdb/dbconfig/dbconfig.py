from twisted.python import log

class DBConfig:
    DBPOOL = None
    LOG = False
    
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
        one = False
        if id is not None:
            where = ["id = ?", id]
            one = True
        if limit is not None and int(limit) == 1:
            one = True
        q = "SELECT * FROM %s" % klass.tablename()
        args = None
        if where is not None:
            wherestr, args = self.whereToString(where)
            q += " WHERE " + wherestr
        if group is not None:
            q += " GROUP BY " + group
        if limit is not None:
            q += " LIMIT " + str(limit)
        return DBConfig.DBPOOL.runInteraction(self._doselect, klass, q, args, one)



    ## Vals should be in form of {'name': value, 'othername': value}
    ## This func should return id of new row
    def insert(self, tablename, vals, txn):
        params = ",".join(["%s" for _ in vals.items()])
        colnames = ",".join(vals.keys())
        q = "INSERT INTO %s (%s) " % (tablename, colnames)
        q += "VALUES(" + params + ")"
        self.executeTxn(txn, q, vals.values())
        q = "SELECT LAST_INSERT_ID()"
        self.executeTxn(txn, q)            
        result = txn.fetchall()
        return result[0][0]


    def delete(self, klass, where=None):
        q = "DELETE FROM %s" % klass.tablename()
        args = []
        if where is not None:
            wherestr, args = self.whereToString(where)
            q += " WHERE " + wherestr
        self.execute(q, args)


    ## Args should be in form of {'name': value, 'othername': value}
    def update(self, tablename, args, where=None, txn=None):
        setstring, args = self.updateArgsToString(args)
        q = "UPDATE %s " % tablename + " SET " + setstring
        if where is not None:
            wherestr, whereargs = self.whereToString(where)
            q += " WHERE " + wherestr
            args += whereargs
            
        if txn is not None:
            return self.executeTxn(txn, q, args)
        return DBConfig.DBPOOL.runQuery(q, args)


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
        from registry import Registry
        if not Registry.SCHEMAS.has_key(tablename):
            self.executeTxn(txn, "DESCRIBE %s" % tablename)
            Registry.SCHEMAS[tablename] = [row[0] for row in txn.fetchall()]
        return Registry.SCHEMAS[tablename]
            

    def insertObj(self, obj):
        def _doinsert(txn):
            klass = obj.__class__
            tablename = klass.tablename()
            cols = self.getSchema(tablename, txn)
            vals = obj.toHash(cols)
            obj.id = self.insert(tablename, vals, txn)
        return DBConfig.DBPOOL.runInteraction(_doinsert)


    def updateObj(self, obj):
        def _doupdate(txn):
            klass = obj.__class__
            tablename = klass.tablename()
            cols = self.getSchema(tablename, txn)
            vals = obj.toHash(cols, exclude=['id'])
            return self.update(tablename, vals, where=['id = ?', obj.id], txn=txn)
        return DBConfig.DBPOOL.runInteraction(_doupdate)    


    def whereToString(self, where):
        assert(type(where) is list)
        query = where[0].replace("?", "%s")
        args = where[1:]
        return (query, args)


    ## Args should be in form of {'name': value, 'othername': value}
    ## Convert to form 'name = %s, othername = %s, ...'
    def updateArgsToString(self, args):
        setstring = ",".join([key + " = %s" for key in vals.keys()])
        return (setstring, args.values())
