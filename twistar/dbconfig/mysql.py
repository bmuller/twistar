from twistar.dbconfig.base import InteractionBase


class MySQLDBConfig(InteractionBase):
    includeBlankInInsert = False

    def insertArgsToString(self, vals):
        if len(vals) > 0:
            return "(" + ",".join(["%s" for _ in vals.items()]) + ")"            
        return "VALUES ()"
    





        
