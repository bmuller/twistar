import threading
import functools

from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks, maybeDeferred, returnValue, Deferred
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

    def __init__(self, parent):
        self._actual_parent = parent
        self.is_active = True

        if not self._parent.is_active:
            raise TransactionError("Parent transaction is inactive")

        Registry.getConfig().txnGuard.txn = self

    @property
    def _parent(self):
        return self._actual_parent or self

    def rollback(self):
        if not self._parent.is_active:
            return

        Registry.getConfig().txnGuard.txn = self._actual_parent
        self._do_rollback()
        self.is_active = False

    def _do_rollback(self):
        self._parent.rollback()

    def commit(self):
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
        return getattr(self._parent, key)


class _RootTransaction(adbapi.Transaction, _Transaction):

    def __init__(self, pool, connection):
        adbapi.Transaction.__init__(self, pool, connection)
        _Transaction.__init__(self, None)

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


class _SavepointTransaction(object):
    pass


def _transaction_dec(func, create_transaction):
    @inlineCallbacks
    def _runTransaction(*args, **kwargs):
        with create_transaction() as txn:
            res = yield maybeDeferred(func, txn, *args, **kwargs)
            returnValue(res)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        d = None  # declare here so that on_result can acces it

        def on_result(success, result):
            from twisted.internet import reactor

            if not success:
                reactor.callFromThread(d.errback, result)
            elif isinstance(result, Deferred):
                result.addCallbacks(lambda res: reactor.callFromThread(d.callback, res),
                                    lambda res: reactor.callFromThread(d.errback, res))
            else:
                reactor.callFromThread(d.callback, result)

        if threadable.isInIOThread():
            d = Deferred()
            thpool = Registry.DBPOOL.threadpool
            thpool.callInThreadWithCallback(on_result, _runTransaction, *args, **kwargs)
            return d
        else:
            # we are already in a db thread, so just execute the transaction
            return _runTransaction(*args, **kwargs)

    return wrapper


def transaction(func=None):
    if func is None:
        conn_pool = Registry.DBPOOL
        cfg = Registry.getConfig()

        if cfg.txnGuard.txn is None:
            conn = conn_pool.connectionFactory(conn_pool)
            return _RootTransaction(conn_pool, conn)
        else:
            return _Transaction(cfg.txnGuard.txn)
    else:
        return _transaction_dec(func, transaction)


def nested_transaction(func=None):
    if func is None:
        pass
    else:
        _transaction_dec(func, nested_transaction)
