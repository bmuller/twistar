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
        getResult = lambda results: [r[1] for r in results] # ignore failures for now
        return defer.DeferredList(ds).addCallback(getResult)
    
    if props is not None:
        return defer.maybeDeferred(klass(**props).afterInit)

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
    statement = ["%s %s %s" % (wone[0], joiner, wtwo[0])]
    args = wone[1:] + wtwo[1:]
    return statement + args
                
