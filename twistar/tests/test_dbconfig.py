from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import EmtpyOrImaginaryTableError
from twistar.dbconfig import Registry

from utils import *

class DBConfigTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self.mktemp())
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()        


    def test_select(self):
        pass


    def test_delete(self):
        pass


    def test_update(self):
        pass


    def test_insert(self):
        pass    
