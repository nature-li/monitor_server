#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-

import gevent
import commands
from check_cmd import CheckCmd
from mt_log.logger import Logger
from ssh_executor import SSHExecutor
from config import config
from job_status import StatusCode


class JobDetail(object):
    def __init__(self, job_id, service_name, ssh_user, ssh_ip, ssh_port,
                 start_cmd, stop_cmd, is_active, auto_recover, mail_receiver):
        # job id
        self.__id = job_id
        """:type: int"""
        # service name
        self.__service_name = service_name
        """:type: int"""
        # ssh user
        self.__ssh_user = ssh_user
        """:type: str"""
        # ssh host
        self.__ssh_ip = ssh_ip
        """:type: str"""
        # ssh port
        self.__ssh_port = ssh_port
        """:type: int"""
        # service start command
        self.__start_cmd = start_cmd
        """:type: str"""
        # service stop command
        self.__stop_cmd = stop_cmd
        """:type: str"""
        # is active
        self.__is_active = is_active
        """:type: bool"""
        # is service need to auto recover when it is not healthy
        self.__auto_recover = auto_recover
        """:type: bool"""
        # when error occurs, who will receive alarm mails
        self.__mail_receiver = mail_receiver
        """:type: str"""

        # which job id this job relies
        self.__relies = set()
        """:type: set[int]"""
        # these check commands need to be executed on local server
        self.__local = dict()
        """:type: dict[int, CheckCmd]"""
        # these check commands need to be executed on remote server
        self.__remote = dict()
        """:type: dict[int, CheckCmd]"""
        # ssh executor
        self.client = None
        """:type: SSHExecutor"""

    def get_id(self):
        """
        Return job id
        :rtype: int
        """
        return self.__id

    def get_ssh_ip(self):
        return self.__ssh_ip

    def get_service_name(self):
        return self.__service_name

    def is_active(self):
        return self.__is_active

    def get_mail_receiver(self):
        return self.__mail_receiver

    def get_auto_recover(self):
        return self.__auto_recover

    def get_all_rely(self):
        return self.__relies

    def get_check_cmd_healthy_code(self):
        a_dict = dict()
        for k, item in self.__local.items():
            a_dict[k] = item.get_healthy_code()
        for k, item in self.__remote.items():
            a_dict[k] = item.get_healthy_code()
        return a_dict

    def login(self):
        try:
            self.client = SSHExecutor(self.__ssh_ip, self.__ssh_port, self.__ssh_user, config.key_file, config.key_pwd)
            self.client.open()
            return True
        except Exception, e:
            Logger.error(e.message)

    def logout(self):
        try:
            if self.client:
                self.client.close()
            return True
        except Exception, e:
            Logger.error(e.message)

    def do_all_check(self):
        """
        Execute all check command for the job, return (is_operate_success, is_healthy)
        :rtype: bool | None
        """
        status_code = StatusCode()
        try:
            # local checking
            for item in self.__local.values():
                status, output = commands.getstatusoutput(item.check_shell)
                Logger.info("id[%s]: localhost[127.0.0.1] execute cmd[%s], status[%s], output[%s]"
                            % (self.__id, item.check_shell, status, output))
                if status != 0:
                    status_code.set_status(None)

                # check healthy
                healthy_code = self.__get_health(item, output)
                Logger.info("id[%s]: localhost[127.0.0.1] healthy_code[%s]" % (self.__id, healthy_code))
                status_code.set_code(healthy_code)

            for item in self.__remote.values():
                std_out, std_err = self.client.execute(item.check_shell)
                Logger.info("id[%s]: remote[%s] execute cmd[%s], std_out[%s], std_err[%s]"
                            % (self.__id, self.__ssh_ip, item.check_shell, std_out, std_err))
                if not std_out and std_err:
                    status_code.set_status(None)
                # check healthy
                healthy_code = self.__get_health(item, std_out)
                Logger.info("id[%s]: remote[%s] healthy_code[%s]" % (self.__id, self.__ssh_ip, healthy_code))
                status_code.set_code(healthy_code)
        except Exception, e:
            Logger.error(e.message)
        finally:
            return status_code.get_code()

    @classmethod
    def __get_health(cls, item, raw_out):
        """
        Parse command out by operator, return (is_parse_error, is_healthy)
        :type item: CheckCmd
        :type raw_out: string
        :return: bool | None
        """
        healthy_code = StatusCode.WHITE_CODE
        try:
            out = raw_out.strip()
            match = None
            if item.operator == "<":
                if int(out) < int(item.check_value):
                    match = True
                else:
                    match = False
            elif item.operator == "<=":
                if int(out) <= int(item.check_value):
                    match = True
                else:
                    match = False
            elif item.operator == "==":
                if int(out) == int(item.check_value):
                    match = True
                else:
                    match = False
            elif item.operator == ">=":
                if int(out) >= int(item.check_value):
                    match = True
                else:
                    match = False
            elif item.operator == ">":
                if int(out) > int(item.check_value):
                    match = True
                else:
                    match = False
            elif item.operator.lower() == "include":
                if out.find(item.check_value) != -1:
                    match = True
                else:
                    match = False
            elif item.operator.lower() == "exclude":
                if out.find(item.check_value) == -1:
                    match = True
                else:
                    match = False

            if item.good_match:
                if match is True:
                    healthy_code = StatusCode.GREEN_CODE
                elif match is False:
                    healthy_code = StatusCode.RED_CODE
            else:
                if match is True:
                    healthy_code = StatusCode.RED_CODE
                elif match is False:
                    healthy_code = StatusCode.GREEN_CODE
        except Exception, e:
            Logger.error(e.message)
            healthy_code = StatusCode.YELLOW_CODE
        finally:
            Logger.info('check_cmd_id[%s], healthy_code[%s]' % (item.check_id, healthy_code))
            item.set_healthy_code(healthy_code)
            return healthy_code

    def stop(self):
        """ Stop service using stop_cmd
        :rtype: bool | None
        """
        try:
            std_out, std_err = self.client.execute(self.__stop_cmd)
            Logger.info("id[%s]: remote[%s] execute cmd[%s], std_out[%s], std_err[%s]"
                        % (self.__id, self.__ssh_ip, self.__stop_cmd, std_out, std_err))

            # check healthy
            # result = self.is_running()
            # return result
            return True
        except Exception, e:
            Logger.error(e.message)

    def start(self):
        """ Start service using start cmd
        :rtype: bool | None
        """
        try:
            std_out, std_err = self.client.execute(self.__start_cmd)
            Logger.info("id[%s]: remote[%s] execute cmd[%s], std_out[%s], std_err[%s]"
                        % (self.__id, self.__ssh_ip, self.__start_cmd, std_out, std_err))

            return True
        except Exception, e:
            Logger.error(e.message)

    def add_check(self, check):
        """
        :type check: CheckCmd
        :return:
        """
        if check.local_check:
            self.__local[check.check_id] = check
        else:
            self.__remote[check.check_id] = check

    def add_rely(self, rely):
        """
        :type rely: int
        :return:
        """
        self.__relies.add(rely)
