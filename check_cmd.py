#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
from job_status import StatusCode


class CheckCmd(object):
    def __init__(self, check_id, service_id, local_check, check_shell, operator, check_value, good_match):
        self.check_id = check_id
        """:type: int"""
        self.service_id = service_id
        """:type: int"""
        self.local_check = local_check
        """:type: bool"""
        self.check_shell = check_shell
        """:type: string"""
        self.operator = operator
        """:type: string"""
        self.check_value = check_value
        """:type: string"""
        self.good_match = good_match
        """:type: bool"""
        # Check result healthy or not
        self.healthy_code = StatusCode.WHITE_CODE
        """:type: bool"""

    def set_healthy_code(self, healthy_code):
        self.healthy_code = healthy_code

    def get_healthy_code(self):
        return self.healthy_code

