#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
import time
import copy


class StatusCode(object):
    WHITE_CODE = 0
    GREEN_CODE = 1
    YELLOW_CODE = 2
    RED_CODE = 3

    def __init__(self):
        self.code = self.WHITE_CODE

    def set_status(self, healthy):
        """
        :type healthy: bool | None
        """
        if healthy is True:
            self.set_code(self.GREEN_CODE)
        elif healthy is False:
            self.set_code(self.RED_CODE)
        elif healthy is None:
            self.set_code(self.YELLOW_CODE)

    def set_code(self, code):
        if code > self.code:
            self.code = code

    def get_code(self):
        return self.code


class JobStatus(object):
    def __init__(self, healthy_code, check_cmd_dict):
        """
        :type healthy_code: int
        :type check_cmd_dict: dict[int, boo]
        """
        # job status: healthy or not
        self.__healthy_code = healthy_code
        """:type: int"""
        # check command status
        self.__check_cmd_healthy_code = check_cmd_dict
        """:type: dict[int, bool]"""
        # last check time
        self.__last = time.time()
        """:type: float"""

    def set_status(self, healthy_code, check_cmd_dict):
        """ Set job status
        :type healthy_code: int
        :type check_cmd_dict: dict[int, bool]
        :rtype: None
        """
        self.__healthy_code = healthy_code
        self.__check_cmd_healthy_code = check_cmd_dict
        self.__last = time.time()

    def get_status(self):
        """ Get job status
        :rtype: (int, float)
        """
        return self.__healthy_code, self.__last

    def get_full_status(self):
        """ Get job status
        :rtype: (int, dict[int, bool], float)
        """
        return self.__healthy_code, copy.deepcopy(self.__check_cmd_healthy_code), self.__last
