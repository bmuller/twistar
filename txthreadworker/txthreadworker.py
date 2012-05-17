# vim: ts=4:sw=4:nu:fdc=4:nospell:expandtab

from Queue import Queue

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python.constants import Names, NamedConstant


class ThreadWorkerState(Names):
    STOPPED = NamedConstant()
    RUNNING = NamedConstant()


class TxThreadWorker(object):
    """
    Thread worker which executes all submitted jobs in a single thread.

    All public methods must be called from the reactor's thread.
    """

    # this class defines a work queue to which thread's job will be submitted.
    # The only task this thread will do is try to empty the work queue.
    # It runs until a stop() is called from the reactor thread, in which case it
    # will stop as soon as all jobs are completed.

    _STOP = object()   # dummmy object to represent the stop command (a job that
                       # when enqueued will stop the ThreadWorker)

    def __init__(self, threadpool=reactor):
        self.threadpool = threadpool
        self._current_state = ThreadWorkerState.STOPPED
        self._work_queue = None

        # deferred to be fired when stop() has completed
        self._stop_finished = None

    def start(self):
        """
        Start this ThreadWorker and make it ready to accept work.
        """
        if self._current_state != ThreadWorkerState.STOPPED:
            return

        self._work_queue = Queue()
        self._current_state = ThreadWorkerState.RUNNING

        self.threadpool.callInThread(self._start)  

    def stop(self):
        """
        Start this ThreadWorker.

        @returns: a deferred which will fire when ThreadWorker has been stopped.
        @rtype: a C{Defer}
        """
        if self._current_state != ThreadWorkerState.RUNNING:
            return

        self._stop_finished = defer.Deferred()
        self._work_queue.put(self._STOP)

        return self._stop_finished

    def submit(self, job, *args, **kwargs):
        """
        Submit a callable to be run in the ThreadWorker.

        @param job: the job to run
        @type job: a C{callable} object

        @returns: a deferred which will fire with the job result
        @rtype: a C{Defer}
        """
        if self._current_state != ThreadWorkerState.RUNNING:
            raise RuntimeError('Cannot submit jobs to a stopped ThreadWorker')
        d = defer.Deferred()
        self._work_queue.put((d, job, args, kwargs))
        return d

    def _start(self):
        while True:
            job = self._work_queue.get()
            if job is self._STOP:
                reactor.callFromThread(self._stop)
                return

            self._completeJob(*job)

    def _stop(self):
        self._work_queue = None
        self._current_state = ThreadWorkerState.STOPPED
        d = self._stop_finished
        d.callback(None)
        self._stop_finished = None

    def _completeJob(self, deferred, job, args, kwargs):
        try:
            res = job(*args, **kwargs)
        except Exception as e:
            reactor.callFromThread(deferred.errback, e)
        else:
            reactor.callFromThread(deferred.callback, res)

    def __repr__(self):
        object_memory_address = hex(id(self))
        return "<%s ThreadWorker object at %s>" % (self._current_state,
                                                   object_memory_address)

