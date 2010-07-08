from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from utils import *

class DBObjectTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self.mktemp())
        #self.user = yield User(first_name="First", last_name="Last", age=10).save()
        #self.ptype = yield PictureType(name="a pic type").save()
        #self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id, type_id=self.ptype.id).save()


#    @inlineCallbacks
#    def test_creation(self):
        # test creating blank object 
        #u = yield User().save()
        #self.assertEqual(type(u.id), int)

        # test creating object with props that don't correspond to columns
        #u = yield User(a_fake_column="blech").save()
        #self.assertEqual(type(u.id), int)        

# Test table doesn't exist
