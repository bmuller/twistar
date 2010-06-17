from BermiInflector.Inflector import Inflector

from dbconfig import DBConfig, Registry

class Relationship:
    def __init__(self, inst, propname):
        self.infl = Inflector()
        self.inst = inst
        klassname = self.infl.classify(propname)
        self.otherklass = Registry.getClass(klassname)
        self.othername = self.infl.foreignKey(propname)
        self.thisname = self.infl.foreignKey(self.inst.__class__.__name__)
        self.dbconfig = Registry.getConfig()


class BelongsTo(Relationship):       
    def get(self):
        return self.otherklass.find(where=["id = ?", getattr(self.inst, self.othername)], limit=1)


    def set(self, other):
        setattr(self.inst, self.othername, other.id)
        return self.inst.save()


class HasMany(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id])

    def update(self, _, others):
        tablename = self.otherclass.tablename()
#HERE
        args = {self.thisname: }
        where = ["%s = ?" % self.thisname, self.inst.id]                
        self.config.update(tablename, 

    def set(self, others):
        tablename = self.otherclass.tablename()
        args = {self.thisname: None}
        where = ["%s = ?" % self.thisname, self.inst.id]        
        return self.dbconfig.update(tablename, args, where).addCallback(self.update, others)
        

class HasOne(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id], limit=1)        

    def set(self, other):
        tablename = self.otherclass.tablename()
        args = {self.thisname: other.id}
        where = ["%s = ?" % self.thisname, self.inst.id]        
        return self.dbconfig.update(tablename, args, where)


class HABTM(Relationship):
    def get(self):
        pass

    def set(self, other):
        pass
