#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
import time
import copy
from multiprocessing import RLock
from job_status import JobStatus, StatusCode
from job_detail import JobDetail
from mt_log.logger import Logger


class StatusHolder(object):
    def __init__(self):
        # multiprocess lock for all job status
        self.lock = RLock()
        # all job status
        self.job_status_dict = dict()
        """:type: dict[int, JobStatus]"""
        # check_cmd status

    def clear_one_status(self, job_id):
        """
        Clear status for one job
        :param job_id: int
        :return:
        """
        try:
            with self.lock:
                if job_id in self.job_status_dict:
                    del self.job_status_dict[job_id]
        except Exception, e:
            Logger.error(e.message)

    def set_one_status(self, job_id, healthy_code, check_cmd_healthy_code):
        """
        Set status for one job
        :type job_id: int
        :type healthy_code: int
        :type check_cmd_healthy_code: dict[int, bool]
        :rtype: None
        """
        try:
            checker_healthy_code = copy.deepcopy(check_cmd_healthy_code)
            with self.lock:
                job_status = self.job_status_dict.get(job_id, None)
                if job_status is not None:
                    job_status.set_status(healthy_code, checker_healthy_code)
                    return
                self.job_status_dict[job_id] = JobStatus(healthy_code, checker_healthy_code)
        except Exception, e:
            Logger.error(e.message)

    def get_one_status(self, job_id):
        """
        Get status for one job
        :type job_id: int
        :return: (int, float) | None
        """
        try:
            with self.lock:
                job_status = self.job_status_dict.get(job_id, None)
                if job_status is None:
                    return None
                return job_status.get_status()
        except Exception, e:
            Logger.error(e.message)

    def get_one_full_status(self, job_id):
        """
        Get status for one job
        :type job_id: int
        :return: (int, dict[int, int], float) | None
        """
        try:
            with self.lock:
                job_status = self.job_status_dict.get(job_id, None)
                if job_status is None:
                    return None
                return job_status.get_full_status()
        except Exception, e:
            Logger.error(e.message)

    def is_group_healthy(self, job_id_set, span=60):
        """
        Check whether a group of job are all healthy
        :type job_id_set: set[int]
        :type span: int
        :rtype: int | None
        """
        try:
            with self.lock:
                now = time.time()
                for job_id in job_id_set:
                    job_status = self.job_status_dict.get(job_id, None)
                    if job_status is None:
                        return False

                    healthy_code, last = job_status.get_status()
                    if abs(now - last) > span:
                        return False

                    if healthy_code != StatusCode.GREEN_CODE:
                        return False
                return True
        except Exception, e:
            Logger.error(e.message)

    def get_group_status(self, job_id_set):
        """
        Get status for a group of jobs
        :type job_id_set: set[int]
        :rtype: dict[int, (int, float)]
        """
        try:
            a_dict = dict()
            """:type: list[(int, float, float)]"""
            with self.lock:
                for job_id in job_id_set:
                    job_status = self.job_status_dict.get(job_id, None)
                    if job_status is None:
                        continue

                    a_dict[job_id] = job_status.get_status()
            return a_dict
        except Exception, e:
            Logger.error(e.message)
