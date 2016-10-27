from __future__ import absolute_import
from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase


class SQLiteDBConfig(InteractionBase):
    def whereToString(self, where):
        assert(isinstance(where, list))
        query = where[0]
        args = where[1:]
        return (query, args)


    def updateArgsToString(self, args):
        colnames = self.escapeColNames(args.keys())
        setstring = ",".join([key + " = ?" for key in colnames])
        return (setstring, list(args.values()))


    def insertArgsToString(self, vals):
        return "(" + ",".join(["?" for _ in vals.items()]) + ")"


    # retarded sqlite can't handle multiple row inserts
    def insertMany(self, tablename, vals):
        def _insertMany(txn):
            for val in vals:
                self.insert(tablename, val, txn)
        return Registry.DBPOOL.runInteraction(_insertMany)
