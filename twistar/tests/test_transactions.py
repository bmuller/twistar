from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor

from twistar.exceptions import TransactionNotStartedError, DBObjectSaveError, TransactionAlreadyStartedError

from utils import *

class TransactionTest(unittest.TestCase):    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.config = Registry.getConfig()

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)            

    @inlineCallbacks
    def test_init_start_transaction(self):
        pen = Pen()
        tx = yield pen.startTransaction()
        yield pen.commit()

    @inlineCallbacks
    def test_init_with_transaction(self):
        pen = Pen()
        transaction = yield pen.startTransaction()
        pen2 = Pen(transaction = transaction)
        self.assertEqual(pen._transaction, pen2._transaction)
        yield pen2.commit()

    @inlineCallbacks
    def test_init_multiple_startTransaction(self):
        pen = Pen()
        txn = yield pen.startTransaction()
        self.assertRaises(TransactionAlreadyStartedError, pen.startTransaction)
        yield pen.commit()

    def test_read_not_started_transaction(self):
        pen = Pen()
        self.assertRaises(TransactionNotStartedError, pen.transaction)

    @inlineCallbacks
    def test_inject_transaction(self):
        pen = Pen()
        yield pen.startTransaction()
        another_pen = Pen()
        another_pen.transaction(pen.transaction())
        self.assertEqual(pen.transaction(), another_pen.transaction())
        yield pen.commit()

    @inlineCallbacks
    def test_init_multiple_transaction(self):
        pen = Pen()
        txn = yield pen.startTransaction()
        self.assertEqual(txn, pen.transaction())
        yield pen.commit()

    def test_fail_commit(self):
        pen = Pen(color="red", len=10)
        self.assertRaises(TransactionNotStartedError, pen.commit)

    @inlineCallbacks
    def test_save_with_transaction_no_commit(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)
        
        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        # cleanup, mostly for pgsql
        yield pen.rollback()

    @inlineCallbacks
    def test_find_outside_transaction_commit(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        yield pen.commit()

    @inlineCallbacks
    def test_find_inside_transaction_commit(self):
        pen = Pen(color="red", len=10)
        txn = yield pen.startTransaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        new_pen = yield Pen.find(pen.id, transaction=txn)
        self.assertEqual(new_pen, pen)

        yield pen.commit()

    @inlineCallbacks
    def test_save_with_transaction_commit(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        yield pen.save()
        yield pen.commit()

        self.assertTrue(type(pen.id) == int or type(pen.id) == long)
            
        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

    @inlineCallbacks
    def test_multiple_save_with_transaction_commit(self):
        pen = Pen(color="red", len=10)
        transaction = yield pen.startTransaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        table = yield Table(color="blue", transaction=transaction)
        self.assertEqual(transaction, table._transaction)
        saved_table = yield table.save()
        self.assertTrue(type(table.id) == int or type(table.id) == long)

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        new_table = yield Table.find(table.id)
        self.assertEqual(new_table, None)

        yield pen.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        new_table = yield Table.find(table.id)
        self.assertEqual(new_table.id, table.id )

    @inlineCallbacks
    def test_multiple_save_with_transaction_commit_using_another_obj(self):
        pen = Pen(color="red", age=10)
        transaction = yield pen.startTransaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        table = yield Table(color="blue", transaction=transaction)
        self.assertEqual(transaction, table._transaction)
        saved_table = yield table.save()
        self.assertTrue(type(table.id) == int or type(table.id) == long)

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        new_table = yield Table.find(table.id)
        self.assertEqual(new_table, None)

        yield table.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        new_table = yield Table.find(table.id)
        self.assertEqual(new_table.id, table.id )

    @inlineCallbacks
    def test_already_commited(self):
        pen = Pen(color="red", len=10)
        transaction = yield pen.startTransaction()
        yield pen.save()
        yield pen.commit()

        self.assertEqual(pen._transaction, None)

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.len, 10)
        
        pen.color="yellow"
        self.assertRaises(TransactionNotStartedError, pen.commit)

    @inlineCallbacks
    def test_rollback(self):
        pen = Pen(color="red")
        transaction = yield pen.startTransaction()
        yield pen.save()
        yield pen.rollback()
        self.assertEqual(pen._transaction, None)

        self.assertTrue(type(pen.id) == int or type(pen.id) == long)
        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)
        
    @inlineCallbacks
    def test_concurrent_insert_1(self):
        pen = Pen(color="red")
        another_pen = Pen(color="red")

        transaction = yield pen.startTransaction()
        yield pen.save()
        yield self.failUnlessFailure(another_pen.save(), Exception)
        yield pen.commit()
        another_pen.color = "blue"
        yield another_pen.save()

    @inlineCallbacks
    def test_concurrent_insert_2(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        yield pen.save()

        another_pen = Pen(color="red", len=20)
        yield another_pen.startTransaction()
        yield self.failUnlessFailure(another_pen.save(), Exception)
        yield another_pen.rollback()

        self.assertEqual(another_pen.color, pen.color)
        self.assertNotEqual(another_pen._transaction, pen._transaction)

        yield pen.rollback()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        yield another_pen.startTransaction()
        yield another_pen.save()
        new_pen = yield Pen.find(another_pen.id)
        self.assertEqual(new_pen, None)

        yield another_pen.commit()
        new_pen = yield Pen.find(another_pen.id)
        self.assertEqual(new_pen.len, 20)

    @inlineCallbacks
    def test_delete(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        yield pen.save()
        yield pen.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        yield pen.startTransaction()
        yield pen.delete()
        yield pen.commit()

        new_pen = None
        new_pen = yield Pen.find(pen.id, limit=1)
        self.assertEqual(new_pen, None)

    @inlineCallbacks
    def test_delete_with_rollback(self):
        pen = Pen(color="red", len=10)
        yield pen.startTransaction()
        yield pen.save()
        yield pen.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        yield pen.startTransaction()
        yield pen.delete()

        self.assertRaises(DBObjectSaveError, pen.save)

        yield pen.rollback()

        new_pen = None
        new_pen = yield Pen.find(pen.id, limit=1)
        self.assertEqual(new_pen.color, pen.color)

    @inlineCallbacks
    def test_set_hasmany(self):
        table = yield Table(color="red")
        transaction = yield table.startTransaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)
        yield table.commit()
        self.assertEqual(table._transaction, None)
        results = yield table.rubbers.get()
        resultids = [int(rubber.id) for rubber in results]
        self.assertEqual(rubberids, resultids)

    @inlineCallbacks
    def test_set_hasmany_rollback(self):
        table = yield Table(color="red")
        transaction = yield table.startTransaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)
        yield table.rollback()
        self.assertEqual(table._transaction, None)
        results = yield table.rubbers.get()
        self.assertEqual(results, [])

    @inlineCallbacks
    def test_set_hasmany_no_commit(self):
        table = yield Table(color="red")
        transaction = yield table.startTransaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)
        results = yield table.rubbers.get()
        self.assertEqual(results, [])
        # Needed for pgsql
        yield table.rollback()

    @inlineCallbacks
    def test_count_habtm(self):
        try:
            table = Table(color="blue")
            transaction = yield table.startTransaction()
            table = yield table.save()

            pen = yield Pen(color="red", transaction=transaction).save()
            another_pen = yield Pen(color="green", transaction=transaction).save()

            pensid = [pen.id, another_pen.id]
            pens = [pen, another_pen]
            yield table.pens.set(pens, transaction)

            cnt = yield table.pens.count(transaction=transaction)
            self.assertEqual(cnt, 2)

            cnt = yield table.pens.count()
            self.assertEqual(cnt, 0)

            yield table.commit()

            cnt = yield table.pens.count()
            self.assertEqual(cnt, 2)
        except Exception as e:
            print e

    @inlineCallbacks
    def test_set_habtm(self):
        table = yield Table(color="blue").save()
        pen = yield Pen(color="red").save()
        another_pen = yield Pen(color="green").save()
        pensid = [pen.id, another_pen.id]
        pens = [pen, another_pen]
        transaction = yield table.startTransaction()
        yield table.pens.set(pens, transaction)
        yield table.commit()
        newpens = yield table.pens.get()
        newpensids = [pen.id for pen in newpens]
        self.assertEqual(newpensids, pensid)

    @inlineCallbacks
    def test_set_habtm_no_commit(self):
        table = yield Table(color="blue").save()
        pen = yield Pen(color="red").save()
        another_pen = yield Pen(color="green").save()
        pensid = [pen.id, another_pen.id]
        pens = [pen, another_pen]
        transaction = yield table.startTransaction()
        yield table.pens.set(pens, transaction)
        newpens = yield table.pens.get()
        self.assertEqual(newpens, [])
        #Need for pgsql
        yield table.rollback()

    @inlineCallbacks
    def test_set_habtm_rollback(self):
        table = yield Table(color="blue").save()
        pen = yield Pen(color="red").save()
        another_pen = yield Pen(color="green").save()
        pens = [pen, another_pen]
        transaction = yield table.startTransaction()
        yield table.pens.set(pens, transaction)
        yield table.rollback()
        self.assertEqual(table._transaction, None)
        newpens = yield table.pens.get()
        self.assertEqual(newpens, [])

    @inlineCallbacks
    def test_get_hasmany_outside_transaction(self):
        table = yield Table(color="red")
        transaction = yield table.startTransaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)

        table_rubbers = yield table.rubbers.get()
        self.assertEqual(table_rubbers, [])

        yield table.rollback()

    @inlineCallbacks
    def test_get_hasmany_inside_transaction(self):
        table = yield Table(color="red")
        transaction = yield table.startTransaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)

        table_rubbers = yield table.rubbers.get(transaction=transaction)
        self.assertNotEqual(table_rubbers, [])
        self.assertEqual(len(table_rubbers), 3)

        yield table.rollback()

    @inlineCallbacks
    def test_has_one_inside_transaction(self):
        user = User()
        txn = yield user.startTransaction()
        yield user.save()
        avatar=Avatar()
        avatar.transaction(txn)
        yield avatar.save()
        yield user.avatar.set(avatar, transaction=txn)
        new_avatar = yield user.avatar.get(transaction=txn)
        self.assertEqual(avatar, new_avatar)
        yield user.commit()
        new_avatar = yield user.avatar.get()
        self.assertEqual(avatar, new_avatar)
 
    @inlineCallbacks
    def test_has_one_outside_transaction(self):
        user = User()
        txn = yield user.startTransaction()
        yield user.save()
        avatar=Avatar()
        avatar.transaction(txn)
        yield avatar.save()
        yield user.avatar.set(avatar, transaction=txn)
        new_avatar = yield user.avatar.get()
        self.assertNotEqual(avatar, new_avatar)
        self.assertEqual(new_avatar, None)
        yield user.commit()
        new_avatar = yield user.avatar.get()
        self.assertEqual(avatar, new_avatar)
   
    @inlineCallbacks
    def test_belongsTo_inside_transaction(self):
        pic=Picture()
        txn = yield pic.startTransaction()
        user = User()
        user.transaction(txn)
        yield user.save()
        yield pic.save()
        yield pic.user.set(user, transaction=txn)
        new_user = yield pic.user.get(transaction=txn)
        yield user.commit()
        self.assertEqual(user, new_user)
        new_user = yield pic.user.get()
        self.assertEqual(user, new_user)

    @inlineCallbacks
    def test_belongsTo_outside_transaction(self):
        pic=Picture()
        txn = yield pic.startTransaction()
        user = User()
        user.transaction(txn)
        yield user.save()
        yield pic.save()
        yield pic.user.set(user, transaction=txn)
        new_user = yield User.find(id=1)
        self.assertNotEqual(user, new_user)
        self.assertEqual(new_user, None)
        yield user.commit()
        new_user = yield User.find(id=1)
        self.assertEqual(user, new_user)

    @inlineCallbacks
    def test_findBy(self):
        r = yield User.findBy(first_name="Some", last_name="User", age=20)
        self.assertEqual(r, [])

        user = User(first_name="Some", last_name="User", age=20)
        txn = yield user.startTransaction()
        yield user.save()

        r = yield User.findBy(first_name="Some", last_name="User", age=20, transaction=txn)
        self.assertEqual(r[0], user)

        yield user.commit()

        r = yield User.findBy(first_name="Some", last_name="User", age=20)
        self.assertEqual(r[0], user)

    @inlineCallbacks
    def test_findBy_rollback(self):
        r = yield User.findBy(first_name="Some", last_name="User", age=20)
        self.assertEqual(r, [])

        user = User(first_name="Some", last_name="User", age=20)
        txn = yield user.startTransaction()
        yield user.save()

        r = yield User.findBy(first_name="Some", last_name="User", age=20, transaction=txn)
        self.assertEqual(r[0], user)

        yield user.rollback()

        r = yield User.findBy(first_name="Some", last_name="User", age=20)
        self.assertEqual(r, [])

    @inlineCallbacks
    def test_findOrCreate(self):
        user = User(first_name="First", last_name="Last", age=10)
        txn = yield user.startTransaction()
        yield user.save()

        # make sure we didn't create a new user
        r = yield User.findOrCreate(first_name="First", transaction=txn)
        self.assertEqual(r.id, user.id)

        # make sure we do create a new user
        r = yield User.findOrCreate(first_name="First", last_name="Non", transaction=txn)
        txn_id = r.id
        self.assertTrue(r.id != user.id)

        yield user.commit()

        # make sure we do create a new user
        r = yield User.findOrCreate(first_name="First", last_name="Non")
        self.assertTrue(r.id != user.id)
        self.assertTrue(r.id == txn_id)

    @inlineCallbacks
    def test_findOrCreate_rollback(self):
        user = User(first_name="First", last_name="Last", age=10)
        txn = yield user.startTransaction()
        yield user.save()

        # make sure we didn't create a new user
        r = yield User.findOrCreate(first_name="First", transaction=txn)
        self.assertEqual(r.id, user.id)

        # make sure we do create a new user
        r = yield User.findOrCreate(first_name="First", last_name="Non", transaction=txn)
        txn_id = r.id
        self.assertTrue(r.id != user.id)

        yield user.rollback()

        # make sure we do create a new user
        r = yield User.findOrCreate(first_name="First", last_name="Non")
        self.assertTrue(r.id == user.id)
        self.assertTrue(r.id != txn_id)

    @inlineCallbacks
    def test_transacted_operation_after_commit_raises(self):
        pen = Pen(color="red", len=10)
        transaction = yield pen.startTransaction()
        yield pen.save()
        yield pen.commit()

        new_pen = Pen(color="yellow", len=10)
        new_pen.transaction(transaction)

        yield self.assertFailure(new_pen.save(), TransactionNotStartedError)
