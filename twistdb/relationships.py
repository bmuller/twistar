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


class BelongsTo(Relationship):       
    def get(self):
        return self.otherklass.find(where=["id = ?", getattr(self.inst, self.othername)], limit=1)


    def set(self, other):
        setattr(self.inst, self.othername, other.id)
        return self.inst.save()


class HasMany(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id])

    def update(self, _):
        pass

    def set(self, others):
        self.
        
        return self.otherklass.delete(where=["%s = ?" % self.thisname, self.inst.id]).addCallback(self.update, others)


class HasOne(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id], limit=1)        

    def set(self, other):
        pass


class HABTM(Relationship):
    def get(self):
        pass

    def set(self, other):
        pass
