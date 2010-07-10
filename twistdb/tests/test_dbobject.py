from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from twistdb.exceptions import EmtpyOrImaginaryTableError

from utils import *

class DBObjectTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self.mktemp())
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()        


    @inlineCallbacks
    def test_creation(self):
        # test creating blank object 
        u = yield User().save()
        self.assertEqual(type(u.id), int)

        # test creating object with props that don't correspond to columns
        u = yield User(a_fake_column="blech").save()
        self.assertEqual(type(u.id), int)        

        # Test table doesn't exist
        f = FakeObject(blah = "something")
        self.failUnlessFailure(f.save(), EmtpyOrImaginaryTableError)


    @inlineCallbacks
    def test_find(self):
        ids = []
        for _ in range(3):
            user = yield User(first_name="blah").save()
            ids.append(user.id)
        yield User(first_name="not blah").save()
        results = yield User.find(where=["first_name = ?", "blah"])
        resultids = [result.id for result in results]
        self.assertEqual(ids, resultids)


    @inlineCallbacks
    def test_all(self):
        ids = [self.user.id]
        for _ in range(3):
            user = yield User(first_name="blah").save()
            ids.append(user.id)
        results = yield User.all()
        resultids = [result.id for result in results]
        self.assertEqual(ids, resultids)

    
    @inlineCallbacks
    def test_delete(self):
        u = yield User().save()
        yield u.delete()
        result = yield User.find(u.id)
        self.assertEqual(result, None)


    def test_delete_all(self):
        users = yield User.all()
        ids = [user.id for user in users]
        for _ in range(3):
            yield User(first_name="blah").save()
        yield User.deleteAll(["first_name = ?", "blah"])
        users = yield User.all()        
        resultids = [user.id for user in users]
        self.assertEqual(resultids, ids)
