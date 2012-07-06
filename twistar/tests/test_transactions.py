from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks, DeferredList

from twistar.exceptions import ReferenceNotSavedError
from twistar.utils import transaction
from twistar.exceptions import TransactionError

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
    def test_findOrCreate(self):
        @transaction
        def interaction(txn):
            ds = []
            ds.append(Transaction.findOrCreate(name="a name"))
            ds.append(Transaction.findOrCreate(name="a name"))
            return DeferredList(ds)

        yield interaction()
        count = yield Transaction.count()
        self.assertEqual(count, 1)


    @inlineCallbacks
    def test_doubleInsert(self):

        @transaction
        def interaction(txn):
            def finish(trans):
                return Transaction(name="unique name").save()
            return Transaction(name="unique name").save().addCallback(finish)
        
        try:
            yield interaction()
        except TransactionError:
            pass

        # there should be no transaction records stored at all
        count = yield Transaction.count()
        self.assertEqual(count, 0)


    @inlineCallbacks
    def test_success(self):

        @transaction
        def interaction(txn):
            def finish(trans):
                return Transaction(name="unique name two").save()
            return Transaction(name="unique name").save().addCallback(finish)

        result = yield interaction()
        self.assertEqual(result.id, 2)

        count = yield Transaction.count()
        self.assertEqual(count, 2)
