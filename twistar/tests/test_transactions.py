import sys
from threading import Event

from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue, maybeDeferred
from twisted.python import threadable

from twistar.transaction import transaction
from twistar.exceptions import TransactionError

from twistar.tests.utils import initDB, tearDownDB, Registry, Transaction, DBTYPE


class TransactionTests(unittest.TestCase):

    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.config = Registry.getConfig()

    @inlineCallbacks
    def tearDown(self):
        d_tearDown = tearDownDB(self)
        delayed = reactor.callLater(2, d_tearDown.cancel)

        try:
            yield d_tearDown
            delayed.cancel()
        except:
            print "db cleanup timed out"

    @inlineCallbacks
    def _assertRaises(self, deferred, *excTypes):
        # required for downward compatibility

        excType = None
        try:
            yield deferred
        except:
            excType, exc, tb = sys.exc_info()

        msgFormat = "Deferred expected to fail with " + ", ".join(str(expType) for expType in excTypes) + "; instead got {}"
        if not excType:
            self.fail(msgFormat.format("Nothing"))
        else:
            self.failIf(not issubclass(excType, *excTypes), msgFormat.format(excType))

    @transaction
    def test_set_cfg_txn(txn, self):
        """Verify that the transaction is actually being set correctly"""
        self.assertIs(txn, Registry.getConfig().txnGuard.txn)

        with transaction() as txn2:
            self.assertIs(txn2, Registry.getConfig().txnGuard.txn)

        self.assertIs(txn, Registry.getConfig().txnGuard.txn)

    @inlineCallbacks
    def test_commit(self):
        barrier = Event()

        @transaction
        @inlineCallbacks
        def trans(txn):
            self.assertFalse(threadable.isInIOThread(), "Transactions must not run in main thread")

            yield Transaction(name="TEST1").save()
            yield Transaction(name="TEST2").save()

            barrier.wait()  # wait here to delay commit
            returnValue("return value")

        d = trans()

        count = yield Transaction.count()
        self.assertEqual(count, 0)

        barrier.set()
        res = yield d
        self.assertEqual(res, "return value")

        count = yield Transaction.count()
        self.assertEqual(count, 2)

    @inlineCallbacks
    def test_rollback(self):
        barrier = Event()

        @transaction
        @inlineCallbacks
        def trans(txn):
            yield Transaction(name="TEST1").save()
            yield Transaction(name="TEST2").save()

            barrier.wait()  # wait here to delay commit
            raise ZeroDivisionError()

        d = trans()

        barrier.set()
        yield self._assertRaises(d, ZeroDivisionError)

        count = yield Transaction.count()
        self.assertEqual(count, 0)

    @inlineCallbacks
    def test_fake_nesting_commit(self):
        barrier = Event()
        threadIds = []

        @transaction
        @inlineCallbacks
        def trans1(txn):
            threadIds.append(threadable.getThreadID())
            yield Transaction(name="TEST1").save()

        @transaction
        @inlineCallbacks
        def trans2(txn):
            threadIds.append(threadable.getThreadID())
            yield trans1()
            yield Transaction(name="TEST2").save()
            barrier.wait()  # wait here to delay commit

        d = trans2()

        count = yield Transaction.count()
        self.assertEqual(count, 0)

        barrier.set()
        yield d

        self.assertEqual(threadIds[0], threadIds[1], "Nested transactions don't run in same thread")

        count = yield Transaction.count()
        self.assertEqual(count, 2)

    @inlineCallbacks
    def test_fake_nesting_rollback(self):
        barrier = Event()

        @transaction
        @inlineCallbacks
        def trans1(txn):
            yield Transaction(name="TEST1").save()
            txn.rollback()  # should propagate to the root transaction

        @transaction
        @inlineCallbacks
        def trans2(txn):
            yield Transaction(name="TEST2").save()
            yield trans1()

            barrier.wait()  # wait here to delay commit

        d = trans2()

        count = yield Transaction.count()
        self.assertEqual(count, 0)

        barrier.set()

        yield d

        count = yield Transaction.count()
        self.assertEqual(count, 0)

    @inlineCallbacks
    def test_fake_nesting_ctxmgr(self):
        @transaction
        @inlineCallbacks
        def trans1(txn):
            yield Transaction(name="TEST1").save()
            with transaction() as txn2:
                yield Transaction(name="TEST2").save()
                txn2.rollback()

        yield trans1()

        count = yield Transaction.count()
        self.assertEqual(count, 0)

    @inlineCallbacks
    def test_parallel_transactions(self):
        if DBTYPE == "sqlite":
            raise unittest.SkipTest("Parallel connections are not supported by sqlite")

        threadIds = []

        # trans1 is supposed to pass, trans2 is supposed to fail due to unique constraint
        # regarding synchronization: trans1 has to start INSERT before trans2,
        # because otherwise it would wait for trans2 to finish due to postgres synchronization strategy

        on_trans1_insert = Event()
        barrier1, barrier2 = Event(), Event()

        @transaction
        @inlineCallbacks
        def trans1(txn):
            threadIds.append(threadable.getThreadID())
            yield Transaction(name="TEST1").save()
            on_trans1_insert.set()
            barrier1.wait()  # wait here to delay commit)

        @transaction
        @inlineCallbacks
        def trans2(txn):
            threadIds.append(threadable.getThreadID())
            on_trans1_insert.wait()
            yield Transaction(name="TEST1").save()
            barrier2.wait()  # wait here to delay commit

        d1 = trans1()
        d2 = trans2()

        # commit tran1, should pass:
        barrier1.set()
        yield d1

        count = yield Transaction.count()
        self.assertEqual(count, 1)

        # commit trans2:
        barrier2.set()

        # should fail due to unique constraint violation
        yield self._assertRaises(d2, Exception)

        self.assertNotEqual(threadIds[0], threadIds[1], "Parallel transactions don't run in different threads")

        count = yield Transaction.count()
        self.assertEqual(count, 1)

    @inlineCallbacks
    def test_sanity_checks(self):
        # Already rollbacked/commited:
        @transaction
        def trans1(txn):
            txn.rollback()
            txn.commit()

        yield self._assertRaises(trans1(), TransactionError)

        # With nesting:
        @transaction
        def trans2(txn):
            with transaction() as txn2:
                txn2.rollback()
            txn.commit()

        yield self._assertRaises(trans2(), TransactionError)

        # Error if started in main thread:
        yield self._assertRaises(maybeDeferred(transaction), TransactionError)

        # Error if rollbacked/commited in another thread:
        main_thread_d = Deferred()
        on_cb_added = Event()
        on_callbacked = Event()

        @transaction
        def trans3(txn):
            def from_mainthread(do_commit):
                if do_commit:
                    txn.commit()
                else:
                    txn.rollback()

            main_thread_d.addCallback(from_mainthread)
            on_cb_added.set()
            on_callbacked.wait()  # don't return (which would cause commit) until main thread executed callbacks
            return main_thread_d  # deferred will fail if from_mainthread() raised an Exception

        d = trans3()
        on_cb_added.wait()  # we need to wait for the callback to be registered otherwise it would be executed in db thread
        main_thread_d.callback(True)  # will commit the transaction in main thread
        on_callbacked.set()
        yield self._assertRaises(d, TransactionError)

        main_thread_d = Deferred()
        on_cb_added.clear()
        on_callbacked.clear()

        d = trans3()
        on_cb_added.wait()
        main_thread_d.callback(False)  # will rollback the transaction in main thread
        on_callbacked.set()
        yield self._assertRaises(d, TransactionError)
