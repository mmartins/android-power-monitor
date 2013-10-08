#!/usr/bin/env python

from usagedata import UsageData
from utils.systeminfo import SystemInfo


class IterationData(object):
    """ Encloses physical hardware usage data as well as estimated usage data
    for each UID that contributes a non-negligible amount of usage for this
    component.
    """

    def __init__(self):
        self.uid_usage = {}

    # Only used in processor?
    def add(self, data):
        for uid, value in self.uid_usage:
            if uid in data.uid_usage:
                value.uid_usage.add(data.uid_usage[uid])

    def set_uid_usage(self, uid, usage):
        self.uid_usage[uid] = usage

    def set_sys_usage(self, usage):
        self.uid_usage[SystemInfo.AID_ALL] = usage
