#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
from multiprocessing import RLock
from job_detail import JobDetail
from mt_log.logger import Logger


class JobHolder(object):
    def __init__(self):
        self.__lock = RLock()
        self.__job_list = list()
        self.__job_dict = dict()

    def get_job(self):
        """
        Get one job from job list
        :rtype: JobDetail | None
        """
        try:
            with self.__lock:
                if len(self.__job_list) > 0:
                    return self.__job_list.pop()

                if len(self.__job_list) == 0:
                    return None
        except Exception, e:
            Logger.error(e.message)

    def add_job(self, job):
        """
        Add one job to job list. If the same job is exist in the job_dict, add failed.
        :type job: JobDetail
        :rtype: bool | None
        """
        try:
            with self.__lock:
                job_id = job.get_id()
                if job_id in self.__job_dict:
                    return False
                self.__job_list.append(job)
                self.__job_dict[job_id] = job
                return True
        except Exception, e:
            Logger.error(e.message)

    def del_job(self, job_id):
        """
        Delete a job from job_dict
        :param job_id:
        :rtype: bool | None
        """
        try:
            with self.__lock:
                if job_id in self.__job_dict:
                    del self.__job_dict[job_id]
            return True
        except Exception, e:
            Logger.error(e.message)
