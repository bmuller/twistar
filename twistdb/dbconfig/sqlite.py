from dbconfig import DBConfig


class SQLiteDBConfig(DBConfig):
    def whereToString(self, where):
        assert(type(where) is list)
        query = where[0] #? will be correct
        args = where[1:]
        return (query, args)

    ## Args should be in form of {'name': value, 'othername': value}
    ## Convert to form 'name = ?, othername = ?, ...'
    def updateArgsToString(self, args):
        setstring = ",".join([key + " = ?" for key in vals.keys()])
        return (setstring, args.values())


    def getSchema(self, tablename, txn):
        from registry import Registry
        if not Registry.SCHEMAS.has_key(tablename):
            self.executeTxn(txn, "SELECT * FROM sqlite_master") # % tablename)
            x = txn.fetchall()
            print x
            Registry.SCHEMAS[tablename] = [row[0] for row in x]
        return Registry.SCHEMAS[tablename]    



    





        
