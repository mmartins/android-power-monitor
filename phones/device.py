#!/usr/bin/env python

class DeviceConstants(object):

    PROVIDER_ATT = "AT&T"
    PROVIDER_TMOBILE = "T - Mobile"

    @classmethod
    def get_max_power(cls, monitor_name):
        raise NotImplementedError("DeviceConstants class shouldn't be instantiated directly")

