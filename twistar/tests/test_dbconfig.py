from __future__ import absolute_import
from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

from .utils import User, Picture, Avatar, initDB, tearDownDB, Coltest
from six.moves import range


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

        result = yield self.dbconfig.select(tablename, limit=100, orderby="first_name ASC")
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]['id'] == user.id and result[1]['id'] == self.user.id)


    @inlineCallbacks
    def test_select_id(self):
        tablename = User.tablename()

        result = yield self.dbconfig.select(tablename, self.user.id, where=None, limit=1, orderby="first_name ASC")
        self.assertTrue(result is not None)

        where = ['first_name = ?', "DNE"]
        result = yield self.dbconfig.select(tablename, self.user.id, where=where, limit=1, orderby="first_name ASC")
        self.assertTrue(result is None)


    @inlineCallbacks
    def test_delete(self):
        tablename = User.tablename()

        yield User(first_name="Another First").save()
        yield self.dbconfig.delete(tablename, ['first_name like ?', "%nother Fir%"])

        result = yield self.dbconfig.select(tablename)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['id'] == self.user.id)


    @inlineCallbacks
    def test_update(self):
        tablename = User.tablename()
        user = yield User(first_name="Another First").save()

        args = {'first_name': "test", "last_name": "foo", "age": 91}
        yield self.dbconfig.update(tablename, args, ['id = ?', user.id])
        yield user.refresh()
        for key, value in args.items():
            self.assertEqual(value, getattr(user, key))


    @inlineCallbacks
    def test_insert(self):
        tablename = User.tablename()
        args = {'first_name': "test", "last_name": "foo", "age": 91}
        id = yield self.dbconfig.insert(tablename, args)

        where = ['first_name = ? AND last_name = ? AND age = ?']
        where = where + ["test", "foo", 91]
        users = yield User.find(where=where)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, id)
        for key, value in args.items():
            self.assertEqual(value, getattr(users[0], key))


    def test_insertWithTx(self):
        def run(txn):
            tablename = User.tablename()
            args = {'first_name': "test", "last_name": "foo", "age": 91}
            objid = self.dbconfig.insert(tablename, args, txn)
            users = self.dbconfig._doselect(txn, "select * from %s" % User.tablename(), [], User.tablename())
            self.assertEqual(len(users), 2)
            self.assertEqual(users[1]['id'], objid)
            for key, value in args.items():
                self.assertEqual(value, users[1][key])
        return self.dbconfig.runInteraction(run)


    @inlineCallbacks
    def test_insert_many(self):
        tablename = User.tablename()

        args = []
        for counter in range(10):
            args.append({'first_name': "test_insert_many", "last_name": "foo", "age": counter})
        yield self.dbconfig.insertMany(tablename, args)

        users = yield User.find(where=['first_name = ?', "test_insert_many"], orderby="age ASC")

        for counter in range(10):
            for key, value in args[counter].items():
                self.assertEqual(value, getattr(users[counter], key))


    @inlineCallbacks
    def test_insert_obj(self):
        args = {'first_name': "test_insert_obj", "last_name": "foo", "age": 91}
        user = User(**args)

        saved = yield self.dbconfig.insertObj(user)
        user = yield User.find(where=['first_name = ?', "test_insert_obj"], limit=1)
        # ensure that id was set on save
        self.assertEqual(saved.id, user.id)
        # and all values are still the same
        self.assertEqual(saved, user)

        for key, value in args.items():
            self.assertEqual(value, getattr(user, key))


    @inlineCallbacks
    def test_update_obj(self):
        args = {'first_name': "test_insert_obj", "last_name": "foo", "age": 91}
        user = yield User(**args).save()

        args = {'first_name': "test_insert_obj_foo", "last_name": "bar", "age": 191}
        for key, value in args.items():
            setattr(user, key, value)

        yield self.dbconfig.updateObj(user)
        user = yield User.find(user.id)

        for key, value in args.items():
            self.assertEqual(value, getattr(user, key))


    @inlineCallbacks
    def test_colname_escaping(self):
        args = {'select': "some text", 'where': "other text"}
        coltest = Coltest(**args)
        yield self.dbconfig.insertObj(coltest)

        args = {'select': "other text", 'where': "some text"}
        for key, value in args.items():
            setattr(coltest, key, value)
        yield self.dbconfig.updateObj(coltest)

        tablename = Coltest.tablename()
        colnames = self.dbconfig.escapeColNames(["select"])
        ctest = yield self.dbconfig.select(tablename, where=['%s = ?' % colnames[0], args['select']], limit=1)

        for key, value in args.items():
            self.assertEqual(value, ctest[key])


    def test_unicode_logging(self):
        InteractionBase.LOG = True

        ustr = u'\N{SNOWMAN}'
        InteractionBase().log(ustr, [ustr], {ustr: ustr})

        ustr = '\xc3\xa8'
        InteractionBase().log(ustr, [ustr], {ustr: ustr})
        InteractionBase().log(ustr, [], {ustr: ustr})

        InteractionBase.LOG = False
