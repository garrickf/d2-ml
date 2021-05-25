"""
threadpool.py
author: garrick

Threadpool utility for parallelizing network requests. Rate-limits the number
of jobs that may be initiated each second.
"""
import logging
import threading
from threading import Condition, Event, Semaphore

from tqdm import tqdm

logger = logging.getLogger(__name__)


N_REQUESTS_PER_SECOND = 25
NUM_WORKERS = 100


class ThreadPool:
    def __init__(self):
        # Synchronize over whether jobs may be initiated
        self.cv = threading.Condition()
        self.n_requests_available = N_REQUESTS_PER_SECOND

        # Synchronize over whether jobs are available
        self.jobs = []
        self.n_jobs = Semaphore(0)

        # Synchronize when threadpool is done with all outstanding jobs
        self.done_cv = Condition()
        self.completed_jobs = 0
        self.outstanding_jobs = 0

        # Synchronize when threadpool is shutting down
        self.stopped = Event()

        # Create workers
        self.workers = []
        for i in range(NUM_WORKERS):
            t = threading.Thread(target=self._worker, args=(i,))
            t.start()
            self.workers.append(t)

        self.rate_limiter = threading.Thread(target=self._rate_limiter)
        self.rate_limiter.start()

    def _worker(self, i):
        while True:
            # Wait for a job
            self.n_jobs.acquire()

            # When signalled, one of two things may be true: (1) there are
            # actually no jobs, and the thread must exit, or (2) there are jobs.
            # Handle case (1) first to prevent accessing the empty list.
            if self.stopped.is_set():
                break

            func = self.jobs.pop(0)

            # Make sure we can fire request according to rate-limiter
            with self.cv:
                while not self.n_requests_available:
                    self.cv.wait()
                self.n_requests_available -= 1

            func()

            with self.done_cv:
                self.completed_jobs += 1
                self.done_cv.notify_all()

    def _rate_limiter(self):
        while not self.stopped.wait(1):
            # Acquire lock and update requests allowed
            with self.cv:
                self.n_requests_available = N_REQUESTS_PER_SECOND
                self.cv.notify_all()

    def _progress_updater(self):
        while not self.stopped.wait(0.25):
            if self.pbar:
                # Progress is difference between jobs completed and previous n
                self.pbar.update(self.completed_jobs - self.pbar.n)

    def schedule(self, func):
        self.jobs.append(func)
        self.outstanding_jobs += 1
        self.n_jobs.release()

    def wait(self):
        logger.debug("Waiting for jobs to finish...")

        self.pbar = tqdm(total=self.outstanding_jobs)
        self.progress_updater = threading.Thread(target=self._progress_updater)
        self.progress_updater.start()

        with self.done_cv:
            while self.outstanding_jobs != self.completed_jobs:
                self.done_cv.wait()

        self.pbar.update(self.outstanding_jobs - self.pbar.n)
        self.pbar.close()

    def shutdown(self):
        self.wait()
        
        logger.debug("All jobs done. Shutting down...")
        self.stopped.set()
        for _ in range(len(self.workers)):
            self.n_jobs.release()

        # Wait for threads to terminiate
        for t in self.workers:
            t.join()
        self.rate_limiter.join()
        self.progress_updater.join()

        logger.debug("Shut down!")
