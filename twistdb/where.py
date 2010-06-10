    def stringifyWhere(self, where):
        if where.wheretype == GT and where.isnot:
            return "<= " + where.value
        if where.wheretype == GT:
            return "> " + where.value
        if where.wheretype == LT and where.isnot:
            return ">= " + where.value
        if where.wheretype == LT:
            return "< " + where.value
        if where.wheretype == EQ and where.isnot:
            return "!= " + where.value
        if where.wheretype == EQ:
            return "= " + where .value
        
        q = ""
        if where.wheretype == STARTSWITH:
            q = "LIKE " + where.value + "












STARTSWITH, ENDSWITH, CONTAINS, GT, LT, BETWEEN, EQ, IN, ISNULL = range(9)

class Where:
    def __init__(self, wheretype, value, isnot=False):
        self.wheretype = wheretype
        self.value = value
        self.isnot = isnot
        self.colname = None

def startswith(value):
    return Where(STARTSWITH, value)

def endswith(value):
    return Where(ENDSWITH, value)

def contains(value):
    return Where(CONTAINS, value)

def gt(value):
    return Where(GT, value)

def lt(value):
    return Where(LT, value)

def between(first, second):
    return Where(BETWEEN, (first, second))

def eq(value):
    return Where(EQ, value)

def isin(values):
    return Where(IN, values)

def isnull():
    return Where(ISNULL, None)

def nstartswith(value):
    return Where(STARTSWITH, value, True)

def nendswith(value):
    return Where(ENDSWITH, value, True)

def ncontains(value):
    return Where(CONTAINS, value, True)

def ngt(value):
    return Where(GT, value, True)

def nlt(value):
    return Where(LT, value, True)

def nbetween(first, second):
    return Where(BETWEEN, (first, second), True)

def neq(value):
    return Where(EQ, value, True)

def nisin(values):
    return Where(IN, values, True)

def nisnull():
    return Where(ISNULL, None, True)


