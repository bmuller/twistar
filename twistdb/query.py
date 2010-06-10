class Q:
    def __init__(self, key, where):
        self.key = key
        self.where = where
        self.where.colname = self.key
        self.ored = []
        self.anded = []


    def __or__(self, other):
        self.ored.append(other)
        return self


    def __and__(self, other):
        self.anded.append(other)
        return self


    def __str__(self):
        q = "(" + str(self.where)
        
        for query in self.ored:
            q += " OR " + str(query)

        for query in self.anded:
            q += " AND " + str(query)

        return q + ")"
