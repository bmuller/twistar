from threading import Lock

from twisted.python import log
from twisted.enterprise.adbapi import ConnectionPool
from twistar.exceptions import TransactionNotStartedError

from txthreadworker.txthreadworker import TxThreadWorker

class TxConnectionPool(ConnectionPool):

    txWorkers = {}
    txWorkersLock = None

    def startTransaction(self):
        """Open a new database Transaction.

        @return: a Deferred which will fire the Transaction or a Failure.

        Since this connection will be in use until the Transaction is
        completed, the thread that we call the function in gets blocked
        until then.  The Semaphore it is waiting on is stored in
        the self.transLock dictionary.
        """

        warning_limit = self.threadpool.max / 10
        if len(self.threadpool.working) >= self.threadpool.max:
            log.msg('Warning! asking for a new thread, but all slots are busy')
            log.msg(self.dumpThreadPoolStats())
        elif ( len(self.threadpool.working)
               >= self.threadpool.max - warning_limit ):
            log.msg('Warning! threadpool is quite full')
            log.msg(self.dumpThreadPoolStats())

        worker = TxThreadWorker(self.threadpool)
        worker.start()
        if not self.txWorkersLock:
            self.txWorkersLock = Lock()

        def initTx():
            conn = self.connectionFactory(self)
            t = self.transactionFactory(self, conn)

            self.txWorkersLock.acquire()
            self.txWorkers[t] = worker
            self.txWorkersLock.release()

            return t

        def stopWorkerOnError(err):
            # stop the thread if initTx fails
            return self._stopTxWorker(worker).addCallback(lambda _: err)

        d = worker.submit(initTx)
        return d.addErrback(stopWorkerOnError)

    def runQueryInTransaction(self, trans, *args, **kw):
        """Execute an SQL query in the specified Transaction and return the result.

        This function is similar to runQuery but uses a previously created
        Transaction and does not commit or rollback the connection upon
        completion.
        """
        return self._deferToTrans(self._runQueryInTransaction, trans, *args, **kw)

    def executeOperationInTransaction(self, f, trans, *args, **kw):
        """
        Execute the specified function into the transaction thread and return result
        """
        return self._deferToTrans(f, trans, *args, **kw)

    def runOperationInTransaction(self, trans, *args, **kw):
        """Execute an SQL query in the specified Transaction and return None.

        This function is similar to runOperation but uses a previously created
        Transaction and does not commit or rollback the connection upon
        completion.
        """
        return self._deferToTrans(self._runOperationInTransaction, trans, *args, **kw)

    def commitTransaction(self, trans):
        """Commit the transaction to the database."""
        d = self._deferToTrans(self._commitTransaction, trans)
        d.addCallback(self._stopTxWorker)
        return d

    def rollbackTransaction(self, trans):
        """Exit the transaction without committing."""

        d = self._deferToTrans(self._rollbackTransaction, trans)
        d.addCallback(self._stopTxWorker)
        return d

    def dumpThreadPoolStats(self):
        return '\t'.join([ 'waiters: %s' % len(self.threadpool.waiters),
                           'workers: %s' % len(self.threadpool.working),
                           'total: %s'   % len(self.threadpool.threads),
                         ])

    def _stopTxWorker(self, worker):
        return worker.stop()

    def _runQueryInTransaction(self, trans, *args, **kwargs):
        try:
            trans.execute(*args, **kwargs)
            if(trans.rowcount != 0):
                result = trans.fetchall()
            else:
                result = []
            return result
        except:
            log.msg('Exception in SQL query %s'%args)
            log.deferr()
            raise

    def _runOperationInTransaction(self, trans, *args, **kwargs):
        try:
            return trans.execute(*args, **kwargs)
        except:
            log.msg('Exception in SQL operation %s %s'%(trans, args))
            log.deferr()
            raise

    def _commitTransaction(self, trans):
        if trans._cursor is None:
            raise TransactionNotStartedError("Cannot call commit without a transaction")

        worker = self._removeWorkerFromDict(trans)

        try:
            conn = trans._connection
            trans.close()
            conn.commit()
        except Exception as e:
            log.err("commit error %r", e)
            self._stopTxWorker(worker)
            raise e

        return worker

    def _rollbackTransaction(self, trans):
        if trans._cursor is None:
            raise TransactionNotStartedError("Cannot call rollback without a transaction")

        worker = self._removeWorkerFromDict(trans)

        try:
            conn = trans._connection
            conn.rollback()
        except Exception, e:
            log.err("Rollback error %s"%(e))
            self._stopTxWorker(worker)
            raise e

        return worker

    def _removeWorkerFromDict(self, trans):
        self.txWorkersLock.acquire()
        try:
            worker = self.txWorkers[trans]
            del self.txWorkers[trans]
        except Exception as e:
            raise e
        finally:
            self.txWorkersLock.release()

        return worker

    def _deferToTrans(self, f, trans, *args, **kwargs):
        """Internal function.

        Push f onto the transaction's work queue.
        """
        d = None
        self.txWorkersLock.acquire()

        try:
            worker = self.txWorkers.get(trans)
            if not worker:
                err = "Cannot execute operation in the given transaction"
                raise TransactionNotStartedError(err)
            d = worker.submit(f, trans, *args, **kwargs)
        except Exception as e:
            raise e
        finally:
            self.txWorkersLock.release()

        return d
