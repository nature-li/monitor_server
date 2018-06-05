#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-


class Defer(object):
    def __init__(self, fn):
        self.fn = fn

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fn()
