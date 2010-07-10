from BermiInflector.Inflector import Inflector

from twistar.dbconfig import DBConfig, Registry

from exceptions import *

class Relationship:   
    def __init__(self, inst, propname, givenargs):
        self.infl = Inflector()
        self.inst = inst
        self.dbconfig = Registry.getConfig()

        ## Set args
        self.args = { 'class_name': propname,
                      'association_foreign_key': self.infl.foreignKey(self.infl.singularize(propname)),
                      'foreign_key': self.infl.foreignKey(self.inst.__class__.__name__)}
        self.args.update(givenargs)
        
        klassname = self.infl.classify(self.args['class_name'])
        self.otherklass = Registry.getClass(klassname)
        self.othername = self.args['association_foreign_key']
        self.thisclass = self.inst.__class__
        self.thisname = self.args['foreign_key']


class BelongsTo(Relationship):       
    def get(self):
        return self.otherklass.find(where=["id = ?", getattr(self.inst, self.othername)], limit=1)


    def set(self, other):
        setattr(self.inst, self.othername, other.id)
        return self.inst.save()


class HasMany(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id])

    def _update(self, _, others):
        tablename = self.otherklass.tablename()
        args = {self.thisname: self.inst.id}
        ids = []
        for other in others:
            if other.id is None:
                msg = "You must save all other instances before defining a relationship"
                raise ReferenceNotSavedError, msg
            ids.append(str(other.id))
        where = ["id IN (%s)" % ",".join(ids)]                
        return self.dbconfig.update(tablename, args, where)


    def set(self, others):
        tablename = self.otherklass.tablename()
        args = {self.thisname: None}
        where = ["%s = ?" % self.thisname, self.inst.id]        
        return self.dbconfig.update(tablename, args, where).addCallback(self._update, others)
        

class HasOne(Relationship):
    def get(self):
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id], limit=1)

    def set(self, other):
        tablename = self.otherklass.tablename()
        args = {self.thisname: self.inst.id}
        where = ["id = ?", other.id]        
        return self.dbconfig.update(tablename, args, where)


class HABTM(Relationship):
    def tablename(self):
        # if specified by user
        if self.args.has_key('join_table'):
            return self.args['join_table']

        # otherwise, create and cache
        if not hasattr(self, '_tablename'):
            thistable = self.infl.tableize(self.thisclass.__name__)
            othertable = self.infl.tableize(self.otherklass.__name__)
            tables = [thistable, othertable]
            tables.sort()
            self._tablename = "_".join(tables)
        return self._tablename
    
    
    def get(self):
        def _get(rows):
            ids = [str(getattr(row, self.othername)) for row in rows]
            where = ["id IN (%s)" % ",".join(ids)]
            return self.dbconfig.select(self.otherklass, where=where)
        tablename = self.tablename()
        where = ["%s = ?" % self.thisname, self.inst.id]
        klass = Registry.getClass('DBObject')
        return self.dbconfig.select(klass, where=where, tablename=tablename).addCallback(_get)


    def _set(self, _, others):
        args = []
        for other in others:
            if other.id is None:
                msg = "You must save all other instances before defining a relationship"
                raise ReferenceNotSavedError, msg                
            args.append({self.thisname: self.inst.id, self.othername: other.id})
        return self.dbconfig.insertMany(self.tablename(), args)
        

    def set(self, others):
        where = ["%s = ?" % self.thisname, self.inst.id]        
        return self.dbconfig.delete(self.tablename(), where=where).addCallback(self._set, others)

Relationship.TYPES = {'HASMANY': HasMany, 'HASONE': HasOne, 'BELONGSTO': BelongsTo, 'HABTM': HABTM}
