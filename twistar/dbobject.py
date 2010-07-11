"""
Code relating to the base L{DBObject} object.
"""

from twisted.python import log
from twisted.internet import defer

from dbconfig import DBConfig, Registry
from relationships import Relationship
from exceptions import InvalidRelationshipError, DBObjectSaveError

from BermiInflector.Inflector import Inflector

class DBObject(object):
    HASMANY = []
    HASONE = []
    HABTM = []
    BELONGSTO = []
    # this will just be a hash of relationships for faster property resolution
    # the keys are the name and the values are classes representing the relationship
    # it will be of the form {'othername': <BelongsTo instance>, 'anothername': <HasMany instance>}
    RELATIONSHIP_CACHE = None

    """
    A base class for representing objects stored in a RDBMS.
    """
    
    def __init__(self, **kwargs):
        """
        @param kwargs: A dictionary containing the properties that
        should be set for this object.

        @type initial_values: C{dict}
        """
        self.id = None
        self.deleted = False
        if len(kwargs) != 0:
            for k, v in kwargs.items():
                setattr(self, k, v)
        self.config = Registry.getConfig()

        if self.__class__.RELATIONSHIP_CACHE is None:
            self.__class__.initRelationshipCache()


    # relation is either string or dict with 'name' key
    # rtype is one of the keys from Relationship.TYPES
    @classmethod
    def addRelation(klass, relation, rtype):
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
        klass.RELATIONSHIP_CACHE = {}        
        for rtype in Relationship.TYPES.keys():
            for relation in getattr(klass, rtype):
                klass.addRelation(relation, rtype)
        

    def __getattribute__(self, name):
        klass = object.__getattribute__(self, "__class__")
        if not klass.RELATIONSHIP_CACHE is None and klass.RELATIONSHIP_CACHE.has_key(name):
            relationshipKlass, args = klass.RELATIONSHIP_CACHE[name]
            return relationshipKlass(self, name, args)
        return object.__getattribute__(self, name)


    @classmethod
    def tablename(klass):
        if not hasattr(klass, 'TABLENAME'):
            inf = Inflector()
            klass.TABLENAME = inf.tableize(klass.__name__)
        return klass.TABLENAME


    def save(self):
        if self.deleted:
            raise DBObjectSaveError, "Cannot save a previously deleted object."
        if self.id is None:
            return self.config.insertObj(self)
        return self.config.updateObj(self)


    def refresh(self):
        return self.config.refreshObj(self)


    def __str__(self):
        tablename = self.tablename()
        attrs = {}
        if Registry.SCHEMAS.has_key(tablename):
            for key in Registry.SCHEMAS[tablename]:
                attrs[key] = getattr(self, key, None)
        return "<%s object: %s>" % (self.__class__.__name__, str(attrs))

                
    def toHash(self, cols, includeBlank=False, exclude=None, base=None):
        exclude = exclude or []
        h = base or {}
        for col in cols:
            if col in exclude:
                continue
            value = getattr(self, col, None)
            if (value != None or includeBlank):
                h[col] = str(value)
        return h


    @classmethod
    def find(klass, id=None, where=None, group=None, limit=None):
        config = Registry.getConfig()
        return config.select(klass, id, where, group, limit)


    @classmethod
    def all(klass):
        return klass.find()

    @classmethod
    def deleteAll(klass, where=None):
        config = Registry.getConfig()
        tablename = klass.tablename()
        return config.delete(tablename, where)


    def delete(self):
        oldid = self.id
        self.id = None
        self.deleted = True
        return self.__class__.deleteAll(where=["id = ?", oldid])


    def __eq__(self, other):
        eqclass = self.__class__.__name__ == other.__class__.__name__
        eqid = hasattr(other, 'id') and self.id == other.id
        return eqclass and eqid


    def __neq__(self, other):
        return not self == other


    __repr__ = __str__


Registry.register(DBObject)
