"""
All C{Exception} classes.
"""


class TransactionError(Exception):
    """
    Error while running a transaction.
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
