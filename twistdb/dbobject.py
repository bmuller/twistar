from twisted.python import log
from twisted.internet import defer
from dbconfig import DBConfig, Registry
from relationships import HasOne, HasMany, BelongsTo, HasAndBelongsToMany

from BermiInflector.Inflector import Inflector

class DBObject(object):
    def __init__(self, initial_values=None):
        self.id = None
        if initial_values is not None:
            for k, v in initial_values.items():
                setattr(self, k, v)
        self.config = Registry.getConfig()


    def __getattribute__(self, name):
        klass = object.__getattribute__(self, "__class__")
        if hasattr(klass, 'HASMANY') and name in klass.HASMANY:
            return HasMany(self, name)

        if hasattr(klass, 'BELONGSTO') and name in klass.BELONGSTO:
            return BelongsTo(self, name)

        if hasattr(klass, 'HASONE') and name in klass.HASONE:
            return HasOne(self, name)

        return object.__getattribute__(self, name)


    @classmethod
    def tablename(klass):
        if not hasattr(klass, 'TABLENAME'):
            inf = Inflector()
            klass.TABLENAME = inf.tableize(klass.__name__.lower())
        return klass.TABLENAME


    def save(self):
        if self.id is None:
            return self.config.insert(self)
        return self.config.update(self)


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
        return config.delete(klass, where)

    def delete(self):
        return self.__class__.deleteAll(where=["id = ?", self.id])


    __repr__ = __str__
