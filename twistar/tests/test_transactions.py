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
	txn = pen.transaction()
	self.assertTrue(isinstance(txn['transaction'], adbapi.Transaction))
	self.assertTrue(isinstance(txn['connection'], adbapi.Connection))


    def test_init_with_transaction(self):
	pen = Pen()
	txn = pen.transaction()
	pen2 = Pen(transaction = txn)
	self.assertEqual(pen._txn, pen2._txn)


    def test_init_multiple_transaction(self):
	pen = Pen()
	txn = pen.transaction()
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
	txn = pen.transaction()
	saved_pen = yield pen.save()
	self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        table = yield Table(color="blue", transaction=txn)
	self.assertEqual(txn, table._txn)
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
	txn = pen.transaction()
	saved_pen = yield pen.save()
	self.assertTrue(type(pen.id) == int or type(pen.id) == long)

        table = yield Table(color="blue", transaction=txn)
	self.assertEqual(txn, table._txn)
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
	txn = pen.transaction()
	yield pen.save()
	yield pen.commit()

	self.assertEqual(pen._txn, None)

	new_pen = yield Pen.find(pen.id)
	self.assertEqual(new_pen.len, 10)
	
	pen.color="yellow"
	self.assertRaises(TransactionNotStartedError, pen.commit)


    @inlineCallbacks
    def test_rollback(self):
    	pen = Pen(color="red")
	txn = pen.transaction()
	yield pen.save()
	yield pen.rollback()
	self.assertEqual(pen._txn, None)

	self.assertTrue(type(pen.id) == int or type(pen.id) == long)
	new_pen = yield Pen.find(pen.id)
	self.assertEqual(new_pen, None)
	

    @inlineCallbacks
    def test_concurrent_insert_1(self):
    	pen = Pen(color="red")
    	another_pen = Pen(color="red")

	txn = pen.transaction()
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
	self.assertNotEqual(another_pen._txn, pen._txn)

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
