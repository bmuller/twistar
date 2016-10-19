import threading
import functools

from twisted.enterprise import adbapi
from twisted.internet.defer import maybeDeferred, Deferred
from twisted.python import threadable

from twistar.registry import Registry
from twistar.exceptions import TransactionError


class TransactionGuard(threading.local):

    def __init__(self):
        self._txn = None

    @property
    def txn(self):
        return self._txn

    @txn.setter
    def txn(self, txn):
        self._txn = txn


class _Transaction(object):
    """Mostly borrowed from sqlalchemy and adapted to adbapi"""

    def __init__(self, parent, thread_check=True):
        # Transactions must be started in db thread unless explicitely permitted
        if thread_check and threading.current_thread() not in Registry.DBPOOL.threadpool.threads:
            raise TransactionError("Transaction must only be started in a db pool thread")

        if parent is None:
            self._root = self
        else:
            self._root = parent._root

        self._actual_parent = parent
        self.is_active = True
        self._threadId = threadable.getThreadID()
        self._savepoint_seq = 0

        if not self._parent.is_active:
            raise TransactionError("Parent transaction is inactive")

        Registry.getConfig().txnGuard.txn = self

    @property
    def _parent(self):
        return self._actual_parent or self

    def _assertCorrectThread(self):
        if threadable.getThreadID() != self._threadId:
            raise TransactionError("Tried to rollback a transaction from a different thread.\n"
                                   "Make sure that you properly use blockingCallFromThread() and\n"
                                   "that you don't add callbacks to Deferreds which get resolved from another thread.")

    def rollback(self):
        self._assertCorrectThread()

        if not self._parent.is_active:
            return

        Registry.getConfig().txnGuard.txn = self._actual_parent
        self._do_rollback()
        self.is_active = False

    def _do_rollback(self):
        self._parent.rollback()

    def commit(self):
        self._assertCorrectThread()

        if not self._parent.is_active:
            raise TransactionError("This transaction is inactive")

        Registry.getConfig().txnGuard.txn = self._actual_parent
        self._do_commit()
        self.is_active = False

    def _do_commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, excType, exc, traceback):
        if excType is not None and issubclass(excType, Exception):
            self.rollback()
        elif self.is_active:
            try:
                self.commit()
            except:
                self.rollback()
                raise

    def __getattr__(self, key):
        return getattr(self._root, key)


class _RootTransaction(adbapi.Transaction, _Transaction):

    def __init__(self, pool, connection, thread_check=True):
        adbapi.Transaction.__init__(self, pool, connection)
        _Transaction.__init__(self, None, thread_check=thread_check)

    def close(self):
        # don't set to None but errorout on subsequent access
        self._cursor.close()

    def _do_rollback(self):
        if self.is_active:
            self._connection.rollback()
            self.close()

    def _do_commit(self):
        if self.is_active:
            self._connection.commit()
            self.close()

    def __getattr__(self, key):
        return getattr(self._cursor, key)


class _SavepointTransaction(_Transaction):

    def __init__(self, parent, thread_check=True):
        super(_SavepointTransaction, self).__init__(parent, thread_check=thread_check)

        self._root._savepoint_seq += 1
        self._name = "twistar_savepoint_{}".format(self._root._savepoint_seq)

        self.execute("SAVEPOINT {}".format(self._name))

    def _do_rollback(self):
        if self.is_active:
            self.execute("ROLLBACK TO SAVEPOINT {}".format(self._name))

    def _do_commit(self):
        if self.is_active:
            self.execute("RELEASE SAVEPOINT {}".format(self._name))


def _transaction_dec(func, create_transaction):

    def _runTransaction(*args, **kwargs):
        txn = create_transaction()

        def on_succcess(result):
            if txn.is_active:
                try:
                    txn.commit()
                except:
                    txn.rollback()
            return result

        def on_error(fail):
            if txn.is_active:
                txn.rollback()

            return fail

        d = maybeDeferred(func, txn, *args, **kwargs)
        d.addCallbacks(on_succcess, on_error)
        d.addErrback(on_error)
        return d

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        d = None  # declare here so that on_result can access it

        def on_result(success, txn_deferred):
            from twisted.internet import reactor
            txn_deferred.addCallbacks(lambda res: reactor.callFromThread(d.callback, res),
                                      lambda fail: reactor.callFromThread(d.errback, fail))

        if threadable.isInIOThread():
            d = Deferred()
            thpool = Registry.DBPOOL.threadpool
            thpool.callInThreadWithCallback(on_result, _runTransaction, *args, **kwargs)
            return d
        else:
            # we are already in a db thread, so just execute the transaction
            return _runTransaction(*args, **kwargs)

    return wrapper


def transaction(func=None, nested=False, thread_check=True):
    """Starts a new transaction.

    A Transaction object returned by this function can be used as a context manager,
    which will atomatically be commited or rolledback if an exception is raised.

    Transactions must only be used in db threads. This behaviour can be overriden by setting the
    'thread_check' to False, allowing transactions to be started in arbitrary threads which is
    useful to e.g simplify testcases.

    If this function is used as decorator, the decorated function will be executed in a db thread and
    gets the Transaction passed as first argument. Decorated functions are allowed to return Deferreds.
    E.g:
        @transaction
        def someFunc(txn, param1):
            # Runs in a db thread

        d = someFunc(1)  # will be calledback (in mainthread) when someFunc returns

    You have to make sure, that you use blockingCallFromThread() or use synchronization if you need to
    interact with code which runs in the mainthread. Also care has to be taken when waiting for Deferreds.
    You must assure that the callbacks will be invoked from the db thread.

    Per default transactions can be nested: Commiting such a "nested" transaction will simply do nothing,
    but a rollback on it will rollback the outermost transaction. This allow creation of functions which will
    either create a new transaction or will participate in an already ongoing tranaction which is handy for library code.

    SAVEPOINT transactions can be used by either setting the 'nested' flag to true or by calling the 'nested_transaction' function.
    """
    if nested and Registry.DBPOOL.dbapi.__name__ == "sqlite3":
        # nees some modification on our side, see: http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
        raise NotImplementedError("sqlite currently not supported")

    if func is None:
        conn_pool = Registry.DBPOOL
        cfg = Registry.getConfig()

        if cfg.txnGuard.txn is None:
            conn = conn_pool.connectionFactory(conn_pool)
            return _RootTransaction(conn_pool, conn, thread_check=thread_check)
        elif nested:
            return _SavepointTransaction(cfg.txnGuard.txn, thread_check=thread_check)
        else:
            return _Transaction(cfg.txnGuard.txn, thread_check=thread_check)
    else:
        return _transaction_dec(func, functools.partial(transaction, nested=nested, thread_check=thread_check))


nested_transaction = functools.partial(transaction, nested=True)
