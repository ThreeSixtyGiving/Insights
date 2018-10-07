"""
Generic worker.py for enabling background workers to run
long jobs.  Nothing to change or modify here.
"""
import os
from rq import Worker, Queue, Connection
from rq_win import WindowsWorker
from cache import redis_cache

listen = ['high', 'default', 'low']

conn = redis_cache()

if __name__ == '__main__':
    with Connection(conn):
        if hasattr(os, 'fork'):
            worker = Worker(map(Queue, listen))
        else:
            worker = WindowsWorker(map(Queue, listen))
        worker.work()
