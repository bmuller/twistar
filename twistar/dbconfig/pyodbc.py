from __future__ import absolute_import
from twistar.dbconfig.base import InteractionBase


class PyODBCDBConfig(InteractionBase):

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
