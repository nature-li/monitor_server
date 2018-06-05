#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
import traceback
import MySQLdb
from gevent import Greenlet
import gevent.lock
from config import config
from mt_log.logger import Logger
from job_detail import JobDetail
from check_cmd import CheckCmd


class JobLoader(object):
    def __init__(self, job_holder):
        self.job_holder = job_holder
        """:type: JobHolder"""
        self.conn = None
        """:type: MySQLdb.Connection"""
        self.cur = None
        """:type: MySQLdb.Cursor"""
        self.job_list = list()
        """:type: list[JobDetail]"""
        self.lock = gevent.lock.RLock()
        # quit falg
        self.quit = False

    def set_quit(self):
        try:
            with self.lock:
                self.quit = True
        except Exception, e:
            Logger.error(e.message)

    def is_quit(self):
        try:
            with self.lock:
                return self.quit
        except Exception, e:
            Logger.error(e.message)

    def load_job(self):
        try:
            with self.__open() as client:
                client.__load_jobs()
        except Exception, e:
            Logger.error(e.message)

    @staticmethod
    def lod_job_from_mysql(job_loader):
        """
        :type job_loader: JobLoader
        :return:
        """
        try:
            Logger.info("into lod job from mysql")
            job_loader.load_job()
            gevent.sleep(1)
            gevent.spawn(JobLoader.lod_job_from_mysql, job_loader)
        except Exception, e:
            Logger.error(e.message)

    def dispatch(self):
        """
        :return:
        """
        try:
            with self.lock:
                for a_job in self.job_list:
                    self.job_holder.add_job(a_job)
        except Exception, e:
            Logger.error(e.message)

    def __open(self):
        self.conn = MySQLdb.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            passwd=config.mysql_pwd,
            db=config.mysql_db)
        self.cur = self.conn.cursor()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cur:
            self.cur.close()

        if self.conn:
            self.conn.close()

    def __load_jobs(self):
        try:
            a_dict = dict()
            sql = "SELECT services.id, services.service_name, machines.ssh_user, machines.ssh_ip, machines.ssh_port," \
                  "services.start_cmd, services.stop_cmd, services.is_active, services.auto_recover, services.mail_receiver " \
                  "FROM services,machines WHERE services.machine_id = machines.id"
            Logger.info(sql)
            self.cur.execute(sql)
            results = self.cur.fetchall()
            for row in results:
                (job_id, service_name, ssh_user, ssh_ip, ssh_port,
                 start_cmd, stop_cmd, is_active, auto_recover, mail_receiver) = row
                a_dict[job_id] = JobDetail(job_id, service_name, ssh_user, ssh_ip, ssh_port,
                                           start_cmd, stop_cmd, is_active, auto_recover, mail_receiver)

            if not self.__load_checks(a_dict):
                return None

            if not self.__load_relies(a_dict):
                return None

            with self.lock:
                self.job_list = list()
                for a_id, a_job in a_dict.items():
                    self.job_list.append(a_job)
            return True
        except:
            Logger.error(traceback.format_exc())
            return None

    def __load_checks(self, a_dict):
        """
        :type a_dict: dict[int, Job]
        :return: dict[int, Job] | None
        """
        try:
            sql = "SELECT id,service_id,local_check,check_shell,operator,check_value,good_match FROM check_cmd"
            Logger.info(sql)
            self.cur.execute(sql)
            results = self.cur.fetchall()
            for row in results:
                a_id, service_id, local_check, check_shell, operator, check_value, good_match = row
                check = CheckCmd(a_id, service_id, local_check, check_shell, operator, check_value, good_match)
                a_job = a_dict.get(service_id, None)
                if a_job is None:
                    continue
                a_job.add_check(check)
            return True
        except:
            Logger.error(traceback.format_exc())
            return None

    def __load_relies(self, a_dict):
        """
        :type a_dict: dict[int, Job]
        :return: dict[int, Job] | None
        """
        try:
            sql = 'SELECT service_id,rely_id FROM service_rely'
            Logger.info(sql)
            self.cur.execute(sql)
            results = self.cur.fetchall()
            for row in results:
                service_id, rely_id = row
                a_job = a_dict.get(service_id, None)
                if a_job is None:
                    continue
                a_job.add_rely(rely_id)
            return True
        except:
            Logger.error(traceback.format_exc())
            return None


if __name__ == '__main__':
    pass
