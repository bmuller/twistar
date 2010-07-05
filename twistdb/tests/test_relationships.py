from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from utils import *

class RelationshipTest(unittest.TestCase):
    
    @inlineCallback
    def setUp(self):
        yield initDB(self.mktemp())
        self.u = yield User({'first_name': "First", 'last_name': "Last", 'age': 10}).save()

    def test_belongs_to(self):
        print self.u
