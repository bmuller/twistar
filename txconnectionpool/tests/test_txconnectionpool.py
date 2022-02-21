from twisted.internet import defer
from twisted.trial import unittest

from txconnectionpool.txconnectionpool import TxConnectionPool


class FakeTxnError(Exception):
    pass


class FailingToStartConnection(object):
    def __init__(self, _pool):
        raise FakeTxnError('fake connection excpected failure')


class FakeCursor(object):
    def close(self):
        pass


class FailingToCommitOrRollbackConnection(object):
    def __init__(self, _pool):
        pass

    def cursor(self):
        return FakeCursor()

    def reconnect(self):
        pass

    def rollback(self):
        raise FakeTxnError('fake connection expected failure')

    def commit(self):
        raise FakeTxnError('fake connection expected failure')


class TxConnectionPoolTest(unittest.TestCase):
    def test_failure_to_start_txn_will_release_thread(self):
        cp = TxConnectionPool('sqlite3')
        cp.max = 1
        cp.connectionFactory = FailingToStartConnection

        d = cp.startTransaction()
        self.assertFailure(d, FakeTxnError)

        d = cp.startTransaction()
        self.assertFailure(d, FakeTxnError)

        return d

    @defer.inlineCallbacks
    def test_failure_to_commit_will_release_thread(self):
        cp = TxConnectionPool('sqlite3')
        cp.max = 1
        cp.connectionFactory = FailingToCommitOrRollbackConnection

        txn = yield cp.startTransaction()
        d = cp.commitTransaction(txn)
        self.assertFailure(d, FakeTxnError)

        yield d

        txn = yield cp.startTransaction()
        d = cp.commitTransaction(txn)
        self.assertFailure(d, FakeTxnError)

        yield d

    @defer.inlineCallbacks
    def test_failure_to_rollback_will_release_thread(self):
        cp = TxConnectionPool('sqlite3')
        cp.max = 1
        cp.connectionFactory = FailingToCommitOrRollbackConnection

        txn = yield cp.startTransaction()
        d = cp.rollbackTransaction(txn)
        self.assertFailure(d, FakeTxnError)

        yield d

        txn = yield cp.startTransaction()
        d = cp.rollbackTransaction(txn)
        self.assertFailure(d, FakeTxnError)

        yield d
