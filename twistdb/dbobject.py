from twisted.python import log
from twisted.internet import defer
from dbconfig import DBConfig
from BermiInflector.Inflector import Inflector

class DBObject(object):
    def __init__(self, initial_values=None):
        self.id = None
        if initial_values is not None:
            for k, v in initial_values.items():
                setattr(self, k, v)
        self.config = DBConfig.getConfig()
        self.infl = Inflector()


    def getMany(self, name, limit=None):
        klassname = self.infl.classify(name)
        klass = DBConfig.getClass(klassname)
        thisname = self.infl.foreignKey(self.__class__.__name__)
        return klass.find(where=["%s = ?" % thisname, self.id], limit=limit)


    def getOne(self, name):
        klassname = self.infl.classify(name)
        klass = DBConfig.getClass(klassname)
        othername = self.infl.foreignKey(name)
        return klass.find(where=["id = ?", getattr(self, othername)], limit=1)


    def __getattribute__(self, name):
        klass = object.__getattribute__(self, "__class__")
        if hasattr(klass, 'HASMANY') and name in klass.HASMANY:
            return self.getMany(name)

        if hasattr(klass, 'BELONGSTO') and name in klass.BELONGSTO:        
            return self.getOne(name)

        if hasattr(klass, 'HASONE') and name in klass.HASONE:
            return self.getMany(name, limit=1)

        return object.__getattribute__(self, name)


    def __setattr__(self, name, value):
        return object.__setattr__(self, name, value)


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


    def __repr__(self):
        return str(self)


    def __str__(self):
        tablename = self.tablename()
        attrs = {}
        if DBConfig.SCHEMAS.has_key(tablename):
            for key in DBConfig.SCHEMAS[tablename]:
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
        config = DBConfig.getConfig()
        return config.select(klass, id, where, group, limit)


    @classmethod
    def all(klass):
        return klass.find()

    @classmethod
    def deleteAll(klass, where=None):
        config = DBConfig.getConfig()
        return config.delete(klass, where)

    def delete(self):
        return self.__class__.deleteAll(where=["id = ?", self.id])

