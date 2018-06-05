#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-

import os
import gevent
from config import config
import signal
from multiprocessing.managers import BaseManager
from multiprocessing import Process
from mt_log.logger import Logger
from job_runner import JobRunner
from job_loder import JobLoader
from job_holder import JobHolder
from status_holder import StatusHolder


class Controller(object):
    job_holder = None
    """:type: JobHolder"""
    status_holder = None
    """:type: StatusHolder"""
    process_list = list()
    """:type: list[]"""
    # tornado server
    instance = None
    # quit flag for worker process
    quit_flag = False

    # Signal handler for master process
    @staticmethod
    def master_signal_handler(signum, stack):
        Logger.info("master[%s] received SIGTERM signal" % os.getpid())
        Logger.info("master[%s] is stopping" % os.getpid())

        # Shutdown worker process
        for p in Controller.process_list:
            p.terminate()
        for p in Controller.process_list:
            p.join()

        # Shutdown flask server
        if Controller.instance is not None:
            Controller.instance.stop()
        Logger.info("master[%s] is stopped" % os.getpid())

    @staticmethod
    # Signal handler for slave process
    def slave_signal_handler(signum, stack):
        Logger.info("slave[%s] received SIGTERM signal" % os.getpid())
        Logger.info("slave[%s] is stopping" % os.getpid())
        Controller.quit_flag = True

    # Worker process
    @staticmethod
    def worker_process_func(job_holder, status_holder):
        """ Worker process
        :type job_holder: JobHolder
        :type status_holder: StatusHolder
        """
        signal.signal(signal.SIGTERM, Controller.slave_signal_handler)
        while not Controller.quit_flag:
            a_job = job_holder.get_job()
            if a_job is None:
                gevent.sleep(1)
                continue

            runner = JobRunner(a_job, job_holder, status_holder)
            runner.start()

    # Dispatch process
    @staticmethod
    def dispatch_process_func(job_holder):
        """ Dispatch process
        :type job_holder: JobHolder
        :return:
        """
        signal.signal(signal.SIGTERM, Controller.slave_signal_handler)
        job_loader = JobLoader(job_holder)

        # start a thread to load job from mysql
        gevent.spawn(JobLoader.lod_job_from_mysql, job_loader)

        # dispatch job every 1 seconds
        while not Controller.quit_flag:
            job_loader.dispatch()
            gevent.sleep(1)
        job_loader.set_quit()

    # Start worker process
    @staticmethod
    def start_worker_process():
        """
        Start worker process and dispatch process
        :return:
        """
        # register class
        BaseManager.register("JobHolder", JobHolder)
        BaseManager.register("StatusHolder", StatusHolder)
        manager = BaseManager()
        manager.start()

        # all job hodler
        Controller.job_holder = manager.JobHolder()
        """:type: JobHolder"""

        # all job status holder
        Controller.status_holder = manager.StatusHolder()
        """:type: StatusHolder"""

        # start worker process
        for i in xrange(config.worker_process_count):
            p = Process(target=Controller.worker_process_func, args=[Controller.job_holder, Controller.status_holder])
            p.start()
            Controller.process_list.append(p)

        # start dispatch process
        p = Process(target=Controller.dispatch_process_func, args=[Controller.job_holder])
        p.start()
        Controller.process_list.append(p)
