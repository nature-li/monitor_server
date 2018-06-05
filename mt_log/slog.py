#!/usr/bin/env python2.7
# coding: utf-8


import syslog
import traceback
import time
import multiprocessing


class SysLog(object):
    __lock = None
    __max_log_count = 100
    __max_log_interval = 3600
    __last_log_time = 0
    __cur_log_count = 0

    @classmethod
    def open(cls):
        try:
            cls.__lock = multiprocessing.Lock()
            cls.__max_log_count = 100
            cls.__max_log_interval = 3600
            cls.__last_log_time = 0
            cls.__cur_log_count = 0
            syslog.openlog(logoption=syslog.LOG_CONS | syslog.LOG_PID | syslog.LOG_NDELAY | syslog.LOG_PERROR,
                           facility=syslog.LOG_USER)
            return True
        except:
            print traceback.format_exc()

    @classmethod
    def close(cls):
        try:
            syslog.closelog()
        except:
            print traceback.format_exc()

    @classmethod
    def error(cls, content):
        try:
            if not cls.__should_log():
                return False
            syslog.syslog(syslog.LOG_ERR, content)
            return True
        except:
            print traceback.format_exc()

    @classmethod
    def __should_log(cls):
        try:
            with cls.__lock:
                now = time.time()
                if now - cls.__last_log_time > cls.__max_log_interval:
                    cls.__cur_log_count = 0
                if cls.__cur_log_count >= cls.__max_log_count:
                    return False
                cls.__cur_log_count += 1
                cls.__last_log_time = now
                return True
        except:
            print traceback.format_exc()
