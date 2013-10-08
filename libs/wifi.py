#!/usr/bin/env python

from jnius import autoclass

PythonActivity = autoclass('org.renpy.android.PythonActivity')
SystemProperties = autoclass('android.os.SystemProperties')
Context = autoclass('android.content.Context')


class WifiAccess(object):
    __slots__ = ['wifi_manager']

    # From android.net.wifi.WifiManager
    WIFI_STATE_DISABLING = 0
    WIFI_STATE_DISABLED = 1
    WIFI_STATE_ENABLING = 2
    WIFI_STATE_ENABLED = 3
    WIFI_STATE_UNKNONW = 4

    def __init__(self):
        self.wifi_manager = PythonActivity.mActivity.getSystemService(
                Context.WIFI_SERVICE)

    def get_name(self):
        return SystemProperties.get("wifi.interface")

    def get_speed(self):
        wifi_info = self.wifi_manager.getConnectionInfo()
        if wifi_info:
            return wifi_info.getLinkSpeed()

        return 0

    def get_state(self):
        return self.wifi_manager.getWifiState()
