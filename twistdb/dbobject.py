from twisted.python import log
from twisted.internet import defer
from dbconfig.dbconfigbase import DBConfigBase

class DBObject:
    def __init__(self, initial_values=None):
        self.id = None
        if initial_values is not None:
            for k, v in initial_values.items():
                setattr(self, k, v)
        self.config = DBConfigBase.getConfig()


    @classmethod
    def tablename(klass):
        if not hasattr(klass, 'TABLENAME'):
            klass.TABLENAME = klass.__name__.lower() + 's'
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
        log.msg(str(SCHEMAS))
        if SCHEMAS.has_key(tablename):
            for key in SCHEMAS[tablename]:
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
        config = DBConfigBase.getConfig()
        return config.select(klass, id, where, group, limit)


    @classmethod
    def all(klass):
        return klass.find()

    @classmethod
    def deleteAll(klass, where=None):
        config = DBConfigBase.getConfig()
        return config.delete(klass, where)

    def delete(self):
        return self.__class__.deleteAll(where=["id = ?", self.id])

