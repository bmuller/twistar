from twistar.dbconfig.base import InteractionBase


class PostgreSQLDBConfig(InteractionBase):
    includeBlankInInsert = False

    def getLastInsertID(self, txn):
        q = "SELECT lastval()"
        self.executeTxn(txn, q)
        result = txn.fetchall()
        return result[0][0]


    def insertArgsToString(self, vals):
        if len(vals) > 0:
            return "(" + ",".join(["%s" for _ in vals.items()]) + ")"
        return "DEFAULT VALUES"


    def escapeColNames(self, colnames):
        return map(lambda x: '"%s"' % x, colnames)

