from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

class SQLiteDBConfig(InteractionBase):
    
    def whereToString(self, where):
        assert(type(where) is list)
        query = where[0] #? will be correct
        args = where[1:]
        return (query, args)


    def getLastInsertID(self, transaction):
        q = "SELECT last_insert_rowid()"
        self.executeTxn(transaction, q)
        result = transaction.fetchall()
        return result[0][0]
                            

    def updateArgsToString(self, args):
        colnames = self.escapeColNames(args.keys())
        setstring = ",".join([key + " = ?" for key in colnames])
        return (setstring, args.values())


    def insertArgsToString(self, vals):
        return "(" + ",".join(["?" for _ in vals.items()]) + ")"

    
    ## retarded sqlite can't handle multiple row inserts
    def insertMany(self, tablename, vals, transaction=None):
        def _insertMany(transaction):
            for val in vals:
                self.insert(tablename, val, transaction)
        if transaction is not None:
            return self.runWithTransaction(_insertMany, transaction)
        else:
            return Registry.DBPOOL.runInteraction(_insertMany)



        
