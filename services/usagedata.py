#!/usr/bin/env python

class UsageData(object):
    def __init__(self, usage=0):
        self.usage = usage

    def __repr__(self):
        return "usage = {0}".format(self.usage)

    def add(self, usage):
        self.usage += usage

    def log(self, out):
        raise NotImplementedError
