from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import TransactionNotStartedError, TransactionAlreadyStartedError, DBObjectSaveError

from utils import *

class TransactionTest(unittest.TestCase):    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.config = Registry.getConfig()


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)            


    def test_init_start_transaction(self):
        pen = Pen()
        transaction = pen.transaction()
        self.assertTrue(isinstance(transaction, adbapi.Transaction))
        self.assertTrue(isinstance(transaction._connection, adbapi.Connection))


    def test_init_with_transaction(self):
        pen = Pen()
        transaction = pen.transaction()
        pen2 = Pen(transaction = transaction)
        self.assertEqual(pen._transaction, pen2._transaction)


    def test_init_multiple_transaction(self):
        pen = Pen()
        transaction = pen.transaction()
        self.assertRaises(TransactionAlreadyStartedError, pen.transaction)


    def test_fail_commit(self):
        pen = Pen(color="red", len=10)
        self.assertRaises(TransactionNotStartedError, pen.commit)


    @inlineCallbacks
    def test_save_with_transaction_no_commit(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)
        
        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        # cleanup, mostly for pgsql
        yield pen.rollback()


    @inlineCallbacks
    def test_find_outside_transaction_commit(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        yield pen.commit()


    @inlineCallbacks
    def test_find_inside_transaction_commit(self):
        pen = Pen(color="red", len=10)
        txn = pen.transaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        new_pen = yield Pen.find(pen.id, transaction=txn)
        self.assertEqual(new_pen, pen)

        yield pen.commit()


    @inlineCallbacks
    def test_save_with_transaction_commit(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        saved_pen = yield pen.save()
        self.assertTrue(type(pen.id) == int or type(pen.id) == long)
        yield pen.commit()
        
        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        
    @inlineCallbacks
    def test_multiple_save_with_transaction_commit(self):
        pen = Pen(color="red", len=10)
        transaction = pen.transaction()
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
        transaction = pen.transaction()
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
        transaction = pen.transaction()
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
        transaction = pen.transaction()
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

        transaction = pen.transaction()
        yield pen.save()
        yield self.failUnlessFailure(another_pen.save(), Exception)
        yield pen.commit()
        another_pen.color = "blue"
        yield another_pen.save()


    @inlineCallbacks
    def test_concurrent_insert_2(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        yield pen.save()

        another_pen = Pen(color="red", len=20)
        another_pen.transaction()
        yield self.failUnlessFailure(another_pen.save(), Exception)

        self.assertEqual(another_pen.color, pen.color)
        self.assertNotEqual(another_pen._transaction, pen._transaction)

        yield pen.rollback()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen, None)

        yield another_pen.save()
        new_pen = yield Pen.find(another_pen.id)
        self.assertEqual(new_pen, None)

        yield another_pen.commit()
        new_pen = yield Pen.find(another_pen.id)
        self.assertEqual(new_pen.len, 20)

    @inlineCallbacks
    def test_delete(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        yield pen.save()
        yield pen.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        pen.transaction()
        yield pen.delete()
        yield pen.commit()

        new_pen = None
        new_pen = yield Pen.find(pen.id, limit=1)
        self.assertEqual(new_pen, None)


    @inlineCallbacks
    def test_delete_with_rollback(self):
        pen = Pen(color="red", len=10)
        pen.transaction()
        yield pen.save()
        yield pen.commit()

        new_pen = yield Pen.find(pen.id)
        self.assertEqual(new_pen.id, pen.id)

        pen.transaction()
        yield pen.delete()

        self.assertRaises(DBObjectSaveError, pen.save)

        yield pen.rollback()

        new_pen = None
        new_pen = yield Pen.find(pen.id, limit=1)
        self.assertEqual(new_pen.color, pen.color)


    @inlineCallbacks
    def test_set_hasmany(self):
        table = yield Table(color="red")
        transaction = table.transaction()
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
        transaction = table.transaction()
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
        transaction = table.transaction()
        yield table.save()
        rubbers = []
        for _ in range(3):
            rubber = yield Rubber(color="green", transaction=transaction).save()
            rubbers.append(rubber)
        rubberids = [int(rubber.id) for rubber in rubbers]
        yield table.rubbers.set(rubbers, transaction)
        results = yield table.rubbers.get()
        self.assertEqual(results, [])
        #Need for pgsql
        yield table.rollback()


    @inlineCallbacks
    def test_set_habtm(self):
        table = yield Table(color="blue").save()
        pen = yield Pen(color="red").save()
        another_pen = yield Pen(color="green").save()
        pensid = [pen.id, another_pen.id]
        pens = [pen, another_pen]
        transaction = table.transaction()
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
        transaction = table.transaction()
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
        transaction = table.transaction()
        yield table.pens.set(pens, transaction)
        yield table.rollback()
        self.assertEqual(table._transaction, None)
        newpens = yield table.pens.get()
        self.assertEqual(newpens, [])


    @inlineCallbacks
    def test_get_hasmany_outside_transaction(self):
        table = yield Table(color="red")
        transaction = table.transaction()
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
        transaction = table.transaction()
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
