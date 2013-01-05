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


    def count(self, tablename, where=None):
        d = self.select(tablename, where=where, select='count(*)')
        d.addCallback(lambda res: res[0]['count'])
        return d

    def escapeColNames(self, colnames):
        """
        Escape column names for insertion into SQL statement.

        @param colnames: A C{List} of string column names.

        @return: A C{List} of string escaped column names.
        """
        return map(lambda x: '"%s"' % x, colnames)
