"""
Package providing validation support for L{DBObject}s.
"""

from __future__ import absolute_import
from twisted.internet import defer
from BermiInflector.Inflector import Inflector
from twistar.utils import joinWheres, deferredDict
import six


def presenceOf(obj, names, kwargs):
    """
    A validator to test whether or not some named properties are set.
    For those named properties that are not set, an error will
    be recorded in C{obj.errors}.

    @param obj: The object whose properties need to be tested.
    @param names: The names of the properties to test.
    @param kwargs: Keyword arguments.  Right now, all but a
    C{message} value are ignored.
    """
    message = kwargs.get('message', "cannot be blank.")
    for name in names:
        if getattr(obj, name, "") in ("", None):
            obj.errors.add(name, message)


def lengthOf(obj, names, kwargs):
    """
    A validator to test whether or not some named properties have a
    specific length.  The length is specified in one of two ways: either
    a C{range} keyword set with a C{range} / C{xrange} / C{list} object
    containing valid values, or a C{length} keyword with the exact length
    allowed.

    For those named properties that do not have the specified length
    (or that are C{None}), an error will be recorded in C{obj.errors}.

    @param obj: The object whose properties need to be tested.
    @param names: The names of the properties to test.
    @param kwargs: Keyword arguments.  Right now, all but
    C{message}, C{range}, and C{length} values are ignored.
    """
    # create a range object representing acceptable values.  If
    # no range is given (which could be an xrange, range, or list)
    # then length is used.  If length is not given, a length of 1 is
    # assumed
    xr = kwargs.get('range', [kwargs.get('length', 1)])
    minmax = (str(min(xr)), str(max(xr)))
    if minmax[0] == minmax[1]:
        message = kwargs.get('message', "must have a length of %s." % minmax[0])
    else:
        message = kwargs.get('message', "must have a length between %s and %s (inclusive)." % minmax)
    for name in names:
        val = getattr(obj, name, "")
        if val is None or not len(val) in xr:
            obj.errors.add(name, message)


def uniquenessOf(obj, names, kwargs):
    """
    A validator to test whether or not some named properties are unique.
    For those named properties that are not unique, an error will
    be recorded in C{obj.errors}.

    @param obj: The object whose properties need to be tested.
    @param names: The names of the properties to test.
    @param kwargs: Keyword arguments.  Right now, all but a
    C{message} value are ignored.
    """
    message = kwargs.get('message', "is not unique.")

    def handle(results):
        for propname, value in results.items():
            if value is not None:
                obj.errors.add(propname, message)
    ds = {}
    for name in names:
        where = ["%s = ?" % name, getattr(obj, name, "")]
        if obj.id is not None:
            where = joinWheres(where, ["id != ?", obj.id])
        d = obj.__class__.find(where=where, limit=1)
        ds[name] = d
    return deferredDict(ds).addCallback(handle)



class Validator(object):
    """
    A mixin class to handle validating objects before they are saved.

    @cvar VALIDATIONS: A C{list} of functions to call when testing whether or
    not a particular instance is valid.
    """
    # list of validation methods to call for this class
    VALIDATIONS = []

    @classmethod
    def clearValidations(klass):
        """
        Clear the given class's validations.
        """
        klass.VALIDATIONS = []


    @classmethod
    def addValidator(klass, func):
        """
        Add a function to the given classes validation list.

        @param klass: The Class to add the validator to.
        @param func: A function that accepts a single parameter that is the object
        to test for validity.  If the object is invalid, then this function should
        add errors to it's C{errors} property.

        @see: L{Errors}
        """
        # Why do this instead of append? you ask.  Because, I want a new
        # array to be created and assigned (otherwise, all classes will have
        # this validator added).
        klass.VALIDATIONS = klass.VALIDATIONS + [func]


    @classmethod
    def validatesPresenceOf(klass, *names, **kwargs):
        """
        A validator to test whether or not some named properties are set.
        For those named properties that are not set, an error will
        be recorded in C{obj.errors}.

        @param klass: The klass whose properties need to be tested.
        @param names: The names of the properties to test.
        @param kwargs: Keyword arguments.  Right now, all but a
        C{message} value are ignored.
        """
        def vfunc(obj):
            return presenceOf(obj, names, kwargs)
        klass.addValidator(vfunc)


    @classmethod
    def validatesUniquenessOf(klass, *names, **kwargs):
        """
        A validator to test whether or not some named properties are unique.
        For those named properties that are not unique, an error will
        be recorded in C{obj.errors}.

        @param klass: The klass whose properties need to be tested.
        @param names: The names of the properties to test.
        @param kwargs: Keyword arguments.  Right now, all but a
        C{message} value are ignored.
        """
        def vfunc(obj):
            return uniquenessOf(obj, names, kwargs)
        klass.addValidator(vfunc)


    @classmethod
    def validatesLengthOf(klass, *names, **kwargs):
        """
        A validator to test whether or not some named properties have a
        specific length.  The length is specified in one of two ways: either
        a C{range} keyword set with a C{range} / C{xrange} / C{list} object
        containing valid values, or a C{length} keyword with the exact length
        allowed.

        For those named properties that do not have
        the specified length, an error will be recorded in the instance of C{klass}'s
        C{errors} parameter.

        @param klass: The klass whose properties need to be tested.
        @param names: The names of the properties to test.
        @param kwargs: Keyword arguments.  Right now, all but
        C{message}, C{range}, and C{length} values are ignored.
        """
        def vfunc(obj):
            return lengthOf(obj, names, kwargs)
        klass.addValidator(vfunc)


    @classmethod
    def _validate(klass, obj):
        """
        Validate a given object using all of the set validators for the objects class.
        If errors are found, they will be recorded in the objects C{errors} property.

        @return: A C{Deferred} whose callback will receive the given object.

        @see: L{Errors}
        """
        ds = [defer.maybeDeferred(func, obj) for func in klass.VALIDATIONS]
        # Return the object when finished
        return defer.DeferredList(ds).addCallback(lambda results: obj)



class Errors(dict):
    """
    A class to hold errors found during validation of a L{DBObject}.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.infl = Inflector()


    def add(self, prop, error):
        """
        Add an error to a property.  The error message stored for this property will be formed
        from the humanized name of the property followed by the error message given.  For instance,
        C{errors.add('first_name', 'cannot be empty')} will result in an error message of
        "First Name cannot be empty" being stored for this property.

        @param prop: The name of a property to add an error to.
        @param error: A string error to associate with the given property.
        """
        self[prop] = self.get(prop, [])
        msg = "%s %s" % (self.infl.humanize(prop), str(error))
        if msg not in self[prop]:
            self[prop].append(msg)


    def isEmpty(self):
        """
        Returns C{True} if there are any errors associated with any properties,
        C{False} otherwise.
        """
        for value in six.itervalues(self):
            if len(value) > 0:
                return False
        return True


    def errorsFor(self, prop):
        """
        Get the errors for a specific property.

        @param prop: The property to fetch errors for.

        @return: A C{list} of errors for the given property.  If there are none,
        then the returned C{list} will have a length of 0.
        """
        return self.get(prop, [])


    def __str__(self):
        """
        Return all errors as a single string.
        """
        s = []
        for values in six.itervalues(self):
            for value in values:
                s.append(value)
        if len(s) == 0:
            return "No errors."
        return "  ".join(s)


    def __len__(self):
        """
        Get the sum of all errors for all properties.
        """
        return sum([len(value) for value in six.itervalues(self)])
