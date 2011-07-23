"""
General catchall for functions that don't make sense as methods.
"""

from twisted.internet import defer


def createInstances(props, klass):
    """
    Create an instance of C{list} of instances of a given class
    using the given properties.
    
    @param props: One of:
      1. A dict, in which case return an instance of klass
      2. A list of dicts, in which case return a list of klass instances

    @return: A C{Deferred} that will pass the result to a callback
    """
    if type(props) is list:
        ks = [klass(**prop) for prop in props]
        ds = [defer.maybeDeferred(k.afterInit) for k in ks]
        return defer.DeferredList(ds).addCallback(lambda _: ks)
    
    if props is not None:
        k = klass(**props)
        return defer.maybeDeferred(k.afterInit).addCallback(lambda _: k)

    return defer.succeed(None)

                            
def joinWheres(wone, wtwo, joiner="AND"):
    """
    Take two wheres (of the same format as the C{where} parameter in the function
    L{DBObject.find}) and join them.

    @param wone: First where C{list}

    @param wone: Second where C{list}

    @param joiner: Optional text for joining the two wheres.

    @return: A joined version of the two given wheres.
    """
    statement = ["(%s) %s (%s)" % (wone[0], joiner, wtwo[0])]
    args = wone[1:] + wtwo[1:]
    return statement + args


def joinMultipleWheres(wheres, joiner="AND"):
    """
    Take a list of wheres (of the same format as the C{where} parameter in the
    function L{DBObject.find}) and join them.

    @param wheres: List of where clauses to join C{list}

    @param joiner: Optional text for joining the two wheres.

    @return: A joined version of the list of th given wheres.
    """
    wheres = [w for w in wheres if w]   # discard empty wheres
    if not wheres:
        return []

    f = lambda x, y: joinWheres(x, y, joiner)
    return reduce(f, wheres)


def deferredDict(d):
    """
    Just like a C{defer.DeferredList} but instead accepts and returns a C{dict}.

    @param d: A C{dict} whose values are all C{Deferred} objects.

    @return: A C{DeferredList} whose callback will be given a dictionary whose
    keys are the same as the parameter C{d}'s and whose values are the results
    of each individual deferred call.
    """
    if len(d) == 0:
        return defer.succeed({})

    def handle(results, names):
        rvalue = {}
        for index in range(len(results)):
            rvalue[names[index]] = results[index][1]
        return rvalue
    
    dl = defer.DeferredList(d.values())
    return dl.addCallback(handle, d.keys())
