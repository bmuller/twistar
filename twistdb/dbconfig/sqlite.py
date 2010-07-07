from dbconfig import DBConfig


class SQLiteDBConfig(DBConfig):
    def whereToString(self, where):
        assert(type(where) is list)
        query = where[0] #? will be correct
        args = where[1:]
        return (query, args)



    def getLastInsertID(self, txn):
        q = "SELECT last_insert_rowid()"
        self.executeTxn(txn, q)
        result = txn.fetchall()
        return result[0][0]
                            

    ## Args should be in form of {'name': value, 'othername': value}
    ## Convert to form 'name = ?, othername = ?, ...'
    def updateArgsToString(self, args):
        setstring = ",".join([key + " = ?" for key in vals.keys()])
        return (setstring, args.values())


    def getSchema(self, tablename, txn):
        from registry import Registry
        if not Registry.SCHEMAS.has_key(tablename):
            self.executeTxn(txn, "PRAGMA table_info(%s)" % tablename)
            Registry.SCHEMAS[tablename] = [row[1] for row in txn.fetchall()]
        return Registry.SCHEMAS[tablename]    


    ## Convert {'name': value} to "?,?,?"
    def insertArgsToString(self, vals):
        return ",".join(["?" for _ in vals.items()])        

    





        
