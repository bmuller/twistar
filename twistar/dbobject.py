"""
Code relating to the base L{DBObject} object.
"""

from twisted.python import log
from twisted.internet import defer

from twistar.registry import Registry
from twistar.relationships import Relationship
from twistar.exceptions import InvalidRelationshipError, DBObjectSaveError, ReferenceNotSavedError
from twistar.utils import createInstances

from BermiInflector.Inflector import Inflector


class DBObject(object):
    """
    A base class for representing objects stored in a RDBMS.

    @cvar HASMANY: A C{list} made up of some number of strings and C{dict}s.  If an element is a string,
    it represents what the class has many of, for instance C{'users'}.  If an element is a C{dict}, then
    it should minimally have a C{name} attribute (with a value the same as if the element were a string)
    and then any additional options.  See L{Relationship} and L{HasMany} for more information.

    @cvar HASONE: A C{list} made up of some number of strings and C{dict}s.  If an element is a string,
    it represents what the class has one of, for instance C{'location'}.  If an element is a C{dict}, then
    it should minimally have a C{name} attribute (with a value the same as if the element were a string)
    and then any additional options.  See L{Relationship} and L{HasOne} for more information.

    @cvar HABTM: A C{list} made up of some number of strings and C{dict}s.  If an element is a string,
    it represents what the class has many of (and which in turn has many of this current object type),
    for instance a teacher has and belongs to many students.  Both the C{Student} and C{Teacher} classes
    should have a class variable that is C{HABTM = ['teachers']} and C{HABTM = ['students']}, respectively.
    If an element is a C{dict}, then
    it should minimally have a C{name} attribute (with a value the same as if the element were a string)
    and then any additional options.  See L{Relationship} and L{HABTM} for more information.    

    @cvar BELONGSTO: A C{list} made up of some number of strings and C{dict}s.  If an element is a string,
    it represents what the class belongs to, for instance C{'user'}.  If an element is a C{dict}, then
    it should minimally have a C{name} attribute (with a value the same as if the element were a string)
    and then any additional options.  See L{Relationship} and L{BelongsTo} for more information.

    @cvar TABLENAME: If specified, use the given tablename as the one for this object.  Otherwise,
    use the lowercase, plural version of this class's name.  See the L{DBObject.tablename}
    method.
    
    @see: L{Relationship}, L{HasMany}, L{HasOne}, L{HABTM}, L{BelongsTo}
    """
    
    HASMANY = []
    HASONE = []
    HABTM = []
    BELONGSTO = []
    # this will just be a hash of relationships for faster property resolution
    # the keys are the name and the values are classes representing the relationship
    # it will be of the form {'othername': <BelongsTo instance>, 'anothername': <HasMany instance>}
    RELATIONSHIP_CACHE = None
    
   
    def __init__(self, **kwargs):
        """
        Constructor.
        
        @param kwargs: An optional dictionary containing the properties that
        should be initially set for this object.  
        """
        self.id = None
        self.deleted = False
        if len(kwargs) != 0:
            for k, v in kwargs.items():
                setattr(self, k, v)
        self.config = Registry.getConfig()

        if self.__class__.RELATIONSHIP_CACHE is None:
            self.__class__.initRelationshipCache()


    def save(self):
        """
        Save this object to the database.

        @return: A C{Deferred} object.  If a callback is added to that deferred
        the value of the saved object will be returned.
        """
        if self.deleted:
            raise DBObjectSaveError, "Cannot save a previously deleted object."
        if self.id is None:
            return self._create()
        return self._update()


    def beforeCreate(self):
        """
        Method called before a new object is created.  Classes can overwrite this method.
        If False is returned, then the object is not saved in the database.  This method
        may return a C{Deferred}.
        """
        return True


    def _create(self):
        """
        Method to actually create an object in the DB.  Handles calling this class's
        L{beforeCreate} method.

        @return: A C{Deferred} object.  If a callback is added to that deferred
        the value of the saved object will be returned (unless the L{beforeCreate}
        method returns false, in which case the unsaved object will be returned).
        """
        def createOnSuccess(result):
            if result != False:
                return self.config.insertObj(self)
            return defer.succeed(self)
        return defer.maybeDeferred(self.beforeCreate).addCallback(createOnSuccess)


    def beforeSave(self):
        """
        Method called before a new object is saved.  Classes can overwrite this method.
        If False is returned, then the object is not saved in the database.  This method
        may return a C{Deferred}.
        """
        return True


    def _update(self):
        """
        Method to actually save an existing object in the DB.  Handles calling this class's
        L{beforeSave} method.

        @return: A C{Deferred} object.  If a callback is added to that deferred
        the value of the saved object will be returned (unless the L{beforeSave}
        method returns false, in which case the unsaved object will be returned).
        """        
        def saveOnSuccess(result):
            if result != False:
                return self.config.updateObj(self)
            return defer.succeed(self)
        return defer.maybeDeferred(self.beforeSave).addCallback(saveOnSuccess)


    def refresh(self):
        """
        Update the properties for this object from the database.

        @return: A C{Deferred} object.
        """        
        return self.config.refreshObj(self)

               
    def toHash(self, cols, includeBlank=False, exclude=None, base=None):
        """
        Convert this object to a dictionary.

        @param includeBlank: Boolean representing whether or not properties that
        have not been set should be included (the initial property list is retrieved
        from the schema of the database for the given class's schema).

        @param exclue: A C{list} of properties to ignore when creating the C{dict} to
        return.

        @param base: An initial base C{dict} to add this objects properties to.

        @return: A C{dict} formed from the properties and values of this object.
        """
        exclude = exclude or []
        h = base or {}
        for col in cols:
            if col in exclude:
                continue
            value = getattr(self, col, None)
            if (value != None or includeBlank):
                h[col] = str(value)
        return h


    def delete(self):
        """
        Delete this instance from the database.

        @return: A C{Deferred}.        
        """        
        oldid = self.id
        self.id = None
        self.deleted = True
        return self.__class__.deleteAll(where=["id = ?", oldid])


    @classmethod
    def addRelation(klass, relation, rtype):
        """
        Add a relationship to the given Class.
        
        @param klass: The class extending this one.
        
        @param relation: Either a string with the name of property to create
        for this class or a dictionary decribing the relationship.  For instance,
        if a User L{HasMany} Pictures then the relation could either by 'pictures'
        or a dictionary with at least one "name" key, as in
        C{{'name': 'pictures', ...}} along with other options.

        @param rtype: The relationship type.  It should be a key value from
        the C{TYPES} class variable in the class L{Relationship}.
        """
        if type(relation) is dict:
            if not relation.has_key('name'):
                msg = "No key 'name' in the relation %s in class %s" % (relation, klass.__name__)
                raise InvalidRelationshipError, msg
            name = relation['name']
            args = relation
        else:
            name = relation
            args = {}
        relationshipKlass = Relationship.TYPES[rtype]
        klass.RELATIONSHIP_CACHE[name] = (relationshipKlass, args)


    @classmethod
    def initRelationshipCache(klass):
        """
        Initialize the cache of relationship objects for this class.
        """
        klass.RELATIONSHIP_CACHE = {}        
        for rtype in Relationship.TYPES.keys():
            for relation in getattr(klass, rtype):
                klass.addRelation(relation, rtype)
        

    @classmethod
    def tablename(klass):
        """
        Get the tablename for the given class.  If the class has a C{TABLENAME}
        variable then that will be used - otherwise, it is is inferred from the
        class name.

        @param klass: The class to get the tablename for.
        """
        if not hasattr(klass, 'TABLENAME'):
            inf = Inflector()
            klass.TABLENAME = inf.tableize(klass.__name__)
        return klass.TABLENAME


    @classmethod
    def find(klass, id=None, where=None, group=None, limit=None, orderby=None):
        """
        Find instances of a given class.

        @param id: The integer of the C{klass} to find.  For instance, C{Klass.find(1)}
        will return an instance of Klass from the row with an id of 1 (unless it isn't
        found, in which case C{None} is returned).

        @param where: A C{list} whose first element is the string version of the
        condition with question marks in place of any parameters.  Further elements
        of the C{list} should be the values of any parameters specified.  For instance,
        C{['first_name = ? AND age > ?', 'Bob', 21]}.

        @param group: A C{str} describing the grouping, like C{group='first_name'}.

        @param limit: An C{int} specifying the limit of the results.  If this is 1,
        then the return value will be either an instance of C{klass} or C{None}.

        @param orderby: A C{str} describing the ordering, like C{orderby='first_name DESC'}.        

        @return: A C{Deferred} which returns the following to a callback:
        If id is specified (or C{limit} is 1) then a single
        instance of C{klass} will be returned if one is found that fits the criteria, C{None}
        otherwise.  If id is not specified and C{limit} is not 1, then a C{list} will
        be returned with all matching results.
        """
        config = Registry.getConfig()
        d = config.select(klass.tablename(), id, where, group, limit, orderby)
        return d.addCallback(createInstances, klass)


    @classmethod
    def all(klass):
        """
        Get all instances of the given class in the database.  Note that this is the
        equivalent of calling L{find} with no arguments.

        @return: A C{Deferred} which returns the following to a callback:
        A C{list} containing all of the instances in the database.
        """
        return klass.find()


    @classmethod
    def deleteAll(klass, where=None):
        """
        Delete all instances of C{klass} in the database.

        @param where: Conditionally delete instances.  This parameter is of the same form
        found in L{find}.

        @return: A C{Deferred}.        
        """
        config = Registry.getConfig()
        tablename = klass.tablename()
        return config.delete(tablename, where)


    @classmethod
    def exists(klass, where=None):
        """
        Find whether or not at least one instance of the given C{klass} exists, optionally
        with specific conditions specified in C{where}.
        
        @param where: Conditionally find instances.  This parameter is of the same form
        found in L{find}.
        
        @return: A C{Deferred} which returns the following to a callback:
        A boolean as to whether or not at least one object was found.
        """
        def _exists(result):
            return result is not None
        return klass.find(where=where, limit=1).addCallback(_exists)


    def __str__(self):
        """
        Get the string version of this object.
        """
        tablename = self.tablename()
        attrs = {}
        if Registry.SCHEMAS.has_key(tablename):
            for key in Registry.SCHEMAS[tablename]:
                attrs[key] = getattr(self, key, None)
        return "<%s object: %s>" % (self.__class__.__name__, str(attrs))

    
    def __getattribute__(self, name):
        """
        Get the given attribute.

        @param name: The name of the property to get.

        @return: If the name is a relationship based property, then a
        L{Relationship} instance will be returned.  Otherwise the set property
        of the class will be returned.
        """
        klass = object.__getattribute__(self, "__class__")
        if not klass.RELATIONSHIP_CACHE is None and klass.RELATIONSHIP_CACHE.has_key(name):
            if object.__getattribute__(self, 'id') is None:
                raise ReferenceNotSavedError, "Cannot get/set relationship on unsaved object"
            relationshipKlass, args = klass.RELATIONSHIP_CACHE[name]
            return relationshipKlass(self, name, args)
        return object.__getattribute__(self, name)        


    def __eq__(self, other):
        """
        Determine if this object is the same as another (only taking
        the type of the other class and it's C{id} into account).

        @param other: The other object to compare this one to.

        @return: A boolean.
        """
        eqclass = self.__class__.__name__ == other.__class__.__name__
        eqid = hasattr(other, 'id') and self.id == other.id
        return eqclass and eqid


    def __neq__(self, other):
        """
        Determine if this object is not the same as another (only taking
        the type of the other class and it's C{id} into account).

        @param other: The other object to compare this one to.

        @return: A boolean.
        """        
        return not self == other


    __repr__ = __str__


Registry.register(DBObject)
