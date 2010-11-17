"""
Module descripting different types of object relationships.
"""

from twisted.internet import defer

from BermiInflector.Inflector import Inflector

from twistar.registry import Registry
from twistar.utils import createInstances, joinWheres
from twistar.exceptions import ReferenceNotSavedError


class Relationship:
    """
    Base class that all specific relationship type classes extend.

    @see: L{HABTM}, L{HasOne}, L{HasMany}, L{BelongsTo}
    """
    
    def __init__(self, inst, propname, givenargs):
        """
        Constructor.

        @param inst: The L{DBObject} instance.
        
        @param propname: The property name in the L{DBObject} instance that
        results in this class being created.

        @param givenargs: Any arguments given (through the use of a C{dict}
        in the class variable in L{DBObject} rather than a string to describe
        the relationship).  The given args can include, for all relationships,
        a C{class_name}.  Depending on the relationship, C{association_foreign_key}
        and C{foreign_key} might also be used.
        """
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
    """
    Class representing a belongs-to relationship.
    """
    
    def get(self):
        """
        Get the object that belong to the caller.

        @return: A C{Deferred} with a callback value of either the matching class or
        None (if not set).
        """
        return self.otherklass.find(where=["id = ?", getattr(self.inst, self.othername)], limit=1)


    def set(self, other):
        """
        Set the object that belongs to the caller.

        @return: A C{Deferred} with a callback value of the caller.
        """        
        setattr(self.inst, self.othername, other.id)
        return self.inst.save()


    def clear(self):
        """
        Remove the relationship linking the object that belongs to the caller.

        @return: A C{Deferred} with a callback value of the caller.
        """                
        setattr(self.inst, self.othername, None)
        return self.inst.save()



class HasMany(Relationship):
    """
    A class representing the has many relationship.
    """
    
    def get(self, **kwargs):
        """
        Get the objects that caller has.

        @param kwargs: These could include C{limit}, C{orderby}, or any others included in
        C{DBObject.find}.  If a C{where} parameter is included, the conditions will
        be added to the ones already imposed by default in this method.

        @return: A C{Deferred} with a callback value of a list of objects.
        """
        where = ["%s = ?" % self.thisname, self.inst.id]
        if kwargs.has_key('where'):
            kwargs['where'] = joinWheres(where, kwargs['where'])
        else:
            kwargs['where'] = where
        return self.otherklass.find(**kwargs)


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
        """
        Set the objects that caller has.

        @return: A C{Deferred}.
        """                
        tablename = self.otherklass.tablename()
        args = {self.thisname: None}
        where = ["%s = ?" % self.thisname, self.inst.id]        
        d = self.dbconfig.update(tablename, args, where)
        if len(others) > 0:
            d.addCallback(self._update, others)
        return d


    def clear(self):
        """
        Clear the list of all of the objects that this one has.
        """
        return self.set([])
        

class HasOne(Relationship):
    """
    A class representing the has one relationship.
    """
    
    def get(self):
        """
        Get the object that caller has.

        @return: A C{Deferred} with a callback value of the object this one has (or c{None}).
        """                
        return self.otherklass.find(where=["%s = ?" % self.thisname, self.inst.id], limit=1)


    def set(self, other):
        """
        Set the object that caller has.

        @return: A C{Deferred}.
        """                        
        tablename = self.otherklass.tablename()
        args = {self.thisname: self.inst.id}
        where = ["id = ?", other.id]        
        return self.dbconfig.update(tablename, args, where)


class HABTM(Relationship):
    """
    A class representing the "has and bleongs to many" relationship.  One additional argument
    this class uses in the L{Relationship.__init__} argument list is C{join_table}.
    """
    
    def tablename(self):
        """
        Get the tablename (specified either in the C{join_table} relationship property
        or by calculating the tablename).  If not specified, the table name is calculated
        by sorting the table name versions of the two class names and joining them with a '_').
        For instance, given the classes C{Teacher} and C{Student}, the resulting table name would
        be C{student_teacher}.
        """
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
    
    
    def get(self, **kwargs):
        """
        Get the objects that caller has.

        @param kwargs: These could include C{limit}, C{orderby}, or any others included in
        C{InteractionBase.select}.  If a C{where} parameter is included, the conditions will
        be added to the ones already imposed by default in this method.

        @return: A C{Deferred} with a callback value of a list of objects.
        """
        def _get(rows):
            if len(rows) == 0:
                return defer.succeed([])
            ids = [str(row[self.othername]) for row in rows]
            where = ["id IN (%s)" % ",".join(ids)]
            if kwargs.has_key('where'):
                kwargs['where'] = joinWheres(where, kwargs['where'])
            d = self.dbconfig.select(self.otherklass.tablename(), **kwargs)
            return d.addCallback(createInstances, self.otherklass)

        tablename = self.tablename()
        where = ["%s = ?" % self.thisname, self.inst.id]
        return self.dbconfig.select(tablename, where=where).addCallback(_get)


    def _set(self, _, others):
        args = []
        for other in others:
            if other.id is None:
                msg = "You must save all other instances before defining a relationship"
                raise ReferenceNotSavedError, msg                
            args.append({self.thisname: self.inst.id, self.othername: other.id})
        return self.dbconfig.insertMany(self.tablename(), args)
        

    def set(self, others):
        """
        Set the objects that caller has.

        @return: A C{Deferred}.
        """                        
        where = ["%s = ?" % self.thisname, self.inst.id]
        d = self.dbconfig.delete(self.tablename(), where=where)
        if len(others) > 0:
            d.addCallback(self._set, others)
        return d


    def clear(self):
        """
        Clear the list of all of the objects that this one has.
        """        
        return self.set([])


Relationship.TYPES = {'HASMANY': HasMany, 'HASONE': HasOne, 'BELONGSTO': BelongsTo, 'HABTM': HABTM}
