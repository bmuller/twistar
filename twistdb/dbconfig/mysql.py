from twisted.python import log
from dbconfig import DBConfig

class MySQLDBConfig(DBConfig):
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
        return DBConfig.DBPOOL.runInteraction(_doinsert)


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
        return DBConfig.DBPOOL.runInteraction(_doupdate)


