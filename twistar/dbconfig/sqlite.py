from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

class SQLiteDBConfig(InteractionBase):
    
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
                            

    def updateArgsToString(self, args):
        colnames = self.escapeColNames(args.keys())
        setstring = ",".join([key + " = ?" for key in colnames])
        return (setstring, args.values())


    def insertArgsToString(self, vals):
        return "(" + ",".join(["?" for _ in vals.items()]) + ")"

    
    ## retarded sqlite can't handle multiple row inserts
    def insertMany(self, tablename, vals):
        def _insertMany(txn):
            for val in vals:
                self.insert(tablename, val, txn)
        return Registry.DBPOOL.runInteraction(_insertMany)




        
