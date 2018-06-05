#!/usr/bin/env python2.7
# coding: utf-8

import os
import re
import datetime
import traceback
from slog import SysLog


class Writer(object):
    def __init__(self, lock, target, file_name, max_size, max_count):
        self.target = target
        self.file_path = os.path.join(target, file_name)
        self.file_name = file_name
        self.max_size = max_size
        self.max_count = max_count
        self.current_size = 0
        self.handler = None
        self.lock = lock

    def open(self):
        try:
            self.handler = open(self.file_path, 'ab')
            self.current_size = self.handler.tell()
            return True
        except:
            SysLog.error(traceback.format_exc())

    def write(self, content):
        try:
            if self.lock is None:
                return self.__write(content)

            with self.lock:
                return self.__write(content)
        except:
            SysLog.error(traceback.format_exc())

    def __write(self, content):
        try:
            try:
                self.handler.write(content)
                self.current_size = self.handler.tell()
            except Exception, e:
                self.close()
                self.open()
                SysLog.error(e.message)

            if self.current_size >= self.max_size:
                self.close()
                self.__rename()
                self.__clean()
                self.open()
            return True
        except:
            SysLog.error(traceback.format_exc())

    def close(self):
        try:
            if self.handler is None:
                return
            if self.current_size <= 0:
                return
            self.handler.flush()
            self.handler.close()
            self.handler = None
        except:
            SysLog.error(traceback.format_exc())

    def __rename(self):
        try:
            ending = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            new_file_path = self.file_path + '.' + ending
            os.rename(self.file_path, new_file_path)
        except:
            SysLog.error(traceback.format_exc())

    def __clean(self):
        try:
            if self.max_count < 0:
                return
            sorted_names = dict()
            """:type: dict[int, string]"""
            names = os.listdir(self.target)
            for name in names:
                if not re.match(r'^' + self.file_name + r'\.\d{20}$', name):
                    continue
                when = name.split('.')[-1]
                sorted_names[int(when)] = name
            deleted_count = len(sorted_names) - self.max_count

            deleted_list = list()
            for when, name in sorted_names.items():
                if deleted_count <= 0:
                    break
                deleted_list.append(name)
                deleted_count -= 1

            for name in deleted_list:
                full_path = os.path.join(self.target, name)
                os.remove(full_path)
        except:
            SysLog.error(traceback.format_exc())