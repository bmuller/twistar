from dbconfig import DBConfig


class MySQLDBConfig(DBConfig):
    includeBlankInInsert = False

    def insertArgsToString(self, vals):
        if len(vals) > 0:
            return "(" + ",".join(["%s" for _ in vals.items()]) + ")"            
        return "VALUES ()"
    





        
