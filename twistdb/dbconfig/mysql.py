from twisted.python import log

class MySQLDBConfig(DBConfig):
    def select(self, klass, id=None, where=None, group=None, limit=None):
        one = False
        if id is not None:
            where = ["id = ?", id]
            one = True
        q = "SELECT * FROM %s" % klass.tablename()
        args = None
        if where is not None:
            wherestr, args = self.whereToString(where)
            q += " WHERE " + wherestr
        return DBPOOL.runInteraction(self._doselect, klass, q, args, one)


    def whereToString(self, where):
        query = where[0].replace("?", "%s")
        args = where[1:]
        return (query, args)
        

    def insert(self, obj):
        def _doinsert(txn):
            klass = obj.__class__
            tablename = klass.tablename()
            cols = self.getSchema(tablename, txn)
            vals = obj.toHash(cols)
            args = (tablename, ",".join(vals.keys()))
            params = ",".join(["%s" for _ in vals.items()])
            q = "INSERT INTO %s (%s) VALUES(" % args + params + ")"
            self.executeTxn(txn, q, vals.values())            
            q = "SELECT LAST_INSERT_ID()"
            self.executeTxn(txn, q)            
            result = txn.fetchall()
            obj.id = result[0][0]
            return obj
        return DBPOOL.runInteraction(_doinsert)


    def delete(self, klass, where=None):
        q = "DELETE FROM %s" % klass.tablename()
        args = []
        if where is not None:
            wherestr, args = self.whereToString(where)
            q += " WHERE " + wherestr
        self.execute(q, args)


    def update(self, obj):
        def _doupdate(txn):
            klass = obj.__class__
            tablename = klass.tablename()
            cols = self.getSchema(tablename, txn)
            vals = obj.toHash(cols, exclude=['id'])
            args = ",".join([key + " = %s" for key in vals.keys()])
            q = "UPDATE %s " % tablename + "SET " + args + " WHERE id = %s"
            self.executeTxn(txn, q, vals.values() + [obj.id])
            return obj
        return DBPOOL.runInteraction(_doupdate)


class DBObject:
    def __init__(self, initial_values=None):
        self.id = None
        if initial_values is not None:
            for k, v in initial_values.items():
                setattr(self, k, v)
        self.config = DBConfig.getConfig()


    @classmethod
    def tablename(klass):
        if not hasattr(klass, 'TABLENAME'):
            klass.TABLENAME = klass.__name__.lower() + 's'
        return klass.TABLENAME


    def save(self):
        if self.id is None:
            return self.config.insert(self)
        return self.config.update(self)


    def __repr__(self):
        return str(self)


    def __str__(self):
        tablename = self.tablename()
        attrs = {}
        log.msg(str(SCHEMAS))
        if SCHEMAS.has_key(tablename):
            for key in SCHEMAS[tablename]:
                attrs[key] = getattr(self, key, None)
        return "<%s object: %s>" % (self.__class__.__name__, str(attrs))

                
    def toHash(self, cols, includeBlank=False, exclude=None, base=None):
        exclude = exclude or []
        h = base or {}
        for col in cols:
            if col in exclude:
                continue
            value = getattr(self, col, None)
            if (value != None or includeBlank):
                h[col] = str(value)
        return h
            

    @classmethod
    def find(klass, id=None, where=None, group=None, limit=None):
        config = DBConfig.getConfig()
        return config.select(klass, id, where, group, limit)


    @classmethod
    def all(klass):
        return klass.find()

    @classmethod
    def deleteAll(klass, where=None):
        config = DBConfig.getConfig()
        return config.delete(klass, where)

    def delete(self):
        return self.__class__.deleteAll(where=["id = ?", self.id])

