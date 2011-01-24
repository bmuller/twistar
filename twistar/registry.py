"""
Module handling global registration of variables and classes.
"""

from twisted.python import reflect

from BermiInflector.Inflector import Inflector

from twistar.exceptions import ClassNotRegisteredError

class Registry:
    """
    A data store containing mostly class variables that act as constants.

    @cvar DBPOOL: This should be set to the C{twisted.enterprise.dbapi.ConnectionPool} to
    use for all database interaction.
    """
    SCHEMAS = {}
    REGISTRATION = {}
    IMPL = None
    DBPOOL = None


    @classmethod
    def register(_, *klasses):
        """
        Register some number of classes in the registy.  This is necessary so that when objects
        are created on the fly (specifically, as a result of relationship C{get}s) the package
        knows how to find them.

        @param klasses: Any number of parameters, each of which is a class.
        """        
        for klass in klasses:
            Registry.REGISTRATION[klass.__name__] = klass

            def _aliasize(relations):
                for relation in relations:
                    is_poly_as = relation.partition(':')[2].partition('=')
                    if ( is_poly_as[0] == 'polymorphic_as' ):
                        Registry.REGISTRATION[klass.__name__+is_poly_as[2]] = klass

            # register the alias, used in poly relations, right now
            if hasattr(klass, 'HAS_MANY'):
                _aliasize(klass.HAS_MANY)


    @classmethod
    def getClass(klass, name):
        """
        Get a registered class by the given name.
        """        
        if not Registry.REGISTRATION.has_key(name):
            raise ClassNotRegisteredError, "You never registered the class named %s" % name
        return Registry.REGISTRATION[name]

    
    @classmethod
    def getDBAPIClass(klass, name):
        """
        Per U{http://www.python.org/dev/peps/pep-0249/} each DBAPI driver must implement it's
        own Date/Time/Timestamp/etc classes.  This method provides a generalized way to get them
        from whatever DB driver is being used.
        """        
        driver = Registry.DBPOOL.dbapi.__name__
        path = "%s.%s" % (driver, name)
        return reflect.namedAny(path)

    
    @classmethod
    def getConfig(klass):
        """
        Get the current DB config object being used for DB interaction.  This is one of the classes
        that extends L{base.InteractionBase}.
        """
        if Registry.IMPL is not None:
            return Registry.IMPL
        
        if Registry.DBPOOL is None:
            msg = "You must set Registry.DBPOOL to a adbapi.ConnectionPool before calling this method."
            raise RuntimeError, msg
        dbapi = Registry.DBPOOL.dbapi
        if dbapi.__name__ == "MySQLdb":
            from twistar.dbconfig.mysql import MySQLDBConfig                        
            Registry.IMPL = MySQLDBConfig()
        elif dbapi.__name__ == "sqlite3":
            from twistar.dbconfig.sqlite import SQLiteDBConfig                        
            Registry.IMPL = SQLiteDBConfig()
        elif dbapi.__name__ == "psycopg2":
            from twistar.dbconfig.postgres import PostgreSQLDBConfig            
            Registry.IMPL = PostgreSQLDBConfig()
        else:
            raise NotImplementedError, "twisteddb does not support the %s driver" % dbapi.__name__
        
        return Registry.IMPL


