"""
All C{Exception} classes.
"""


class ClassNotRegisteredError(Exception):
    """
    Error resulting from the attempted fetching of a class from the L{Registry} that was
    never registered.
    """


class ImaginaryTableError(Exception):
    """
    Error resulting from the attempted use of a table that doesn't exist.
    """


class ReferenceNotSavedError(Exception):
    """
    Error resulting from the attempted use of an object as a reference that hasn't been
    saved yet.
    """    


class CannotRefreshError(Exception):
    """
    Error resulting from the attempted refreshing of an object that hasn't been
    saved yet.
    """
    

class InvalidRelationshipError(Exception):
    """
    Error resulting from the misspecification of a relationship dictionary.
    """    


class DBObjectSaveError(Exception):
    """
    Error saving a DBObject.
    """

class TransactionNotStartedError(Exception):
   """
   Error resulting from the attempt of using a method which needs a transaction started
   """

class TransactionAlreadyStartedError(Exception):
   """
   Error resulting from the attempt of starting another transaction on same object
   """
