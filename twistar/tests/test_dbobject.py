from __future__ import absolute_import
from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import ImaginaryTableError
from twistar.registry import Registry

from .utils import User, Avatar, Picture, tearDownDB, initDB, FakeObject, DBObject
from six.moves import range


class DBObjectTest(unittest.TestCase):
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)


    @inlineCallbacks
    def test_findBy(self):
        r = yield User.findBy(first_name="Non", last_name="Existant")
        self.assertEqual(r, [])

        r = yield User.findBy(first_name="First", last_name="Last", age=11)
        self.assertEqual(r, [])

        r = yield User.findBy(first_name="First", last_name="Last", age=10)
        self.assertEqual(r[0], self.user)

        r = yield User.findBy(first_name="First", last_name="Last")
        self.assertEqual(r[0], self.user)

        yield User(first_name="Bob").save()
        r = yield User.findBy()
        self.assertEqual(len(r), 2)

        yield User(first_name=None).save()
        r = yield User.findBy(first_name=None)
        self.assertEqual(len(r), 1)


    @inlineCallbacks
    def test_findOrCreate(self):
        # make sure we didn't create a new user
        r = yield User.findOrCreate(first_name="First")
        self.assertEqual(r.id, self.user.id)

        # make sure we do create a new user
        r = yield User.findOrCreate(first_name="First", last_name="Non")
        self.assertTrue(r.id != self.user.id)


    @inlineCallbacks
    def test_creation(self):
        # test creating blank object
        u = yield User().save()
        self.assertTrue(type(u.id) == int or type(u.id) == int)

        # test creating object with props that don't correspond to columns
        u = yield User(a_fake_column="blech").save()
        self.assertTrue(type(u.id) == int or type(u.id) == int)

        # Test table doesn't exist
        f = FakeObject(blah="something")
        self.failUnlessFailure(f.save(), ImaginaryTableError)

        dateklass = Registry.getDBAPIClass("Date")
        args = {'first_name': "a", "last_name": "b", "age": 10, "dob": dateklass(2000, 1, 1)}
        u = yield User(**args).save()
        for key, value in args.items():
            self.assertEqual(getattr(u, key), value)


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
    def test_count(self):
        ids = []
        for _ in range(3):
            user = yield User(first_name="blah").save()
            ids.append(user.id)
        yield User(first_name="not blah").save()
        results = yield User.count(where=["first_name = ?", "blah"])
        self.assertEqual(3, results)


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
    def test_count_all(self):
        ids = [self.user.id]
        for _ in range(3):
            user = yield User(first_name="blah").save()
            ids.append(user.id)
        results = yield User.count()
        self.assertEqual(4, results)


    @inlineCallbacks
    def test_delete(self):
        u = yield User().save()
        oldid = u.id
        yield u.delete()
        result = yield User.find(oldid)
        self.assertEqual(result, None)


    @inlineCallbacks
    def test_delete_all(self):
        users = yield User.all()
        ids = [user.id for user in users]
        for _ in range(3):
            yield User(first_name="blah").save()
        yield User.deleteAll(["first_name = ?", "blah"])
        users = yield User.all()
        resultids = [user.id for user in users]
        self.assertEqual(resultids, ids)


    @inlineCallbacks
    def test_update(self):
        args = {'first_name': "a", "last_name": "b", "age": 10}
        u = yield User(**args).save()

        args = {'first_name': "b", "last_name": "a", "age": 100}
        for key, value in args.items():
            setattr(u, key, value)
        yield u.save()

        u = yield User.find(u.id)
        for key, value in args.items():
            self.assertEqual(getattr(u, key), value)


    @inlineCallbacks
    def test_refresh(self):
        args = {'first_name': "a", "last_name": "b", "age": 10}
        u = yield User(**args).save()

        # mess up the props, then refresh
        u.first_name = "something different"
        u.last_name = "another thing"
        yield u.refresh()

        for key, value in args.items():
            self.assertEqual(getattr(u, key), value)


    @inlineCallbacks
    def test_validation(self):
        User.validatesPresenceOf('first_name', message='cannot be blank, fool.')
        User.validatesLengthOf('last_name', range=range(1, 101))
        User.validatesUniquenessOf('first_name')

        u = User()
        yield u.validate()
        self.assertEqual(len(u.errors), 2)

        first = yield User(first_name="not unique", last_name="not unique").save()
        u = yield User(first_name="not unique", last_name="not unique").save()
        self.assertEqual(len(u.errors), 1)
        self.assertEqual(u.id, None)

        # make sure first can be updated
        yield first.save()
        self.assertEqual(len(first.errors), 0)
        User.clearValidations()


    @inlineCallbacks
    def test_validation_function(self):
        def adult(user):
            if user.age < 18:
                user.errors.add('age', "must be over 18.")
        User.addValidator(adult)

        u = User(age=10)
        valid = yield u.isValid()
        self.assertEqual(valid, False)
        yield u.save()
        self.assertEqual(len(u.errors), 1)
        self.assertEqual(len(u.errors.errorsFor('age')), 1)
        self.assertEqual(len(u.errors.errorsFor('first_name')), 0)
        User.clearValidations()

        u = User(age=10)
        valid = yield u.isValid()
        self.assertEqual(valid, True)
        User.clearValidations()


    @inlineCallbacks
    def test_afterInit(self):
        def afterInit(user):
            user.blah = "foobar"
        User.afterInit = afterInit
        u = yield User.find(limit=1)
        self.assertTrue(hasattr(u, 'blah'))
        self.assertEqual(u.blah, 'foobar')

        # restore user's afterInit
        User.afterInit = DBObject.afterInit


    @inlineCallbacks
    def test_beforeDelete(self):
        User.beforeDelete = lambda user: False
        u = yield User().save()
        oldid = u.id
        yield u.delete()
        result = yield User.find(oldid)
        self.assertEqual(result, u)

        User.beforeDelete = lambda user: True
        yield u.delete()
        result = yield User.find(oldid)
        self.assertEqual(result, None)

        # restore user's beforeDelete
        User.beforeDelete = DBObject.beforeDelete

    @inlineCallbacks
    def test_loadRelations(self):
        user = yield User.find(limit=1)
        all = yield user.loadRelations()

        pictures = yield user.pictures.get()
        self.assertEqual(pictures, all['pictures'])

        avatar = yield user.avatar.get()
        self.assertEqual(avatar, all['avatar'])

        suball = yield user.loadRelations('pictures')
        self.assertTrue('avatar' not in suball)
        self.assertEqual(pictures, suball['pictures'])
