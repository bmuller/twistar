from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import EmtpyOrImaginaryTableError
from twistar.dbconfig import Registry

from utils import *

class DBConfigTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()        
        self.dbconfig = Registry.getConfig()


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)


    @inlineCallbacks
    def test_select(self):
        # make a fake user
        user = yield User(first_name="Another First").save()
        tablename = User.tablename()
        
        where = ['first_name = ?', "First"]
        result = yield self.dbconfig.select(tablename, where=where, limit=1, orderby="first_name ASC")
        self.assertTrue(result is not None)
        self.assertEqual(result['id'], self.user.id)

        result = yield self.dbconfig.select(tablename, limit=100, orderby="first_name ASC" )       
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]['id'] == user.id and result[1]['id'] == self.user.id)


    @inlineCallbacks
    def test_delete(self):
        tablename = User.tablename()
        
        yield User(first_name="Another First").save()
        yield self.dbconfig.delete(tablename, ['first_name like ?', "%nother Fir%"])
        
        result = yield self.dbconfig.select(tablename)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['id'] == self.user.id)
        

    def test_update(self):
        pass


    def test_insert(self):
        pass    
