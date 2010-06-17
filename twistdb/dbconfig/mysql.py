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
        assert(type(where) is list)
        query = where[0].replace("?", "%s")
        args = where[1:]
        return (query, args)


    ## Args should be in form of {'name': value, 'othername': value}
    ## Convert to form 'name = %s, othername = %s, ...'
    def updateArgsToString(self, args):
        setstring = ",".join([key + " = %s" for key in vals.keys()])
        return (setstring, args.values())


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
        
