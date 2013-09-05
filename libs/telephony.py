#!/usr/bin/env python

from jnius import autoclass

TelephonyManager = autoclass('android.telephony.TelephonyManager')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')

class TelephonyAccess(object):
    # From android.telephony.TelephonyManager
    # Data states

    DATA_DISCONNECTED = 0
    DATA_CONNECTING = 1
    DATA_CONNECTED = 2
    DATA_SUSPENDED = 3

    # Mobile network types

    NETWORK_TYPE_UNKNOWN = 0
    NETWORK_TYPE_GPRS = 1
    NETWORK_TYPE_EDGE = 2
    NETWORK_TYPE_UMTS = 3
    NETWORK_TYPE_CDMA = 4
    NETWORK_TYPE_EVDO_0 = 5
    NETWORK_TYPE_EVDO_A = 6
    NETWORK_TYPE_1xRTT = 7
    NETWORK_TYPE_HSDPA = 8
    NETWORK_TYPE_HSUPA = 9
    NETWORK_TYPE_HSPA = 10
    NETWORK_TYPE_IDEN = 11
    NETWORK_TYPE_EVDO_B = 12
    NETWORK_TYPE_LTE = 13
    NETWORK_TYPE_EHRPD = 14
    NETWORK_TYPE_HSPAP = 15

    # Phone types

    PHONE_TYPE_NONE = 0
    PHONE_TYPE_GSM = 1
    PHONE_TYPE_CDMA = 2
    PHONE_TYPE_SIP = 3

    def __init__(self):
        self.telephony_manager = PythonActivity.mActivity.getSystemService(
                Context.TELEPHONY_SERVICE)

    def get_network_type(self):
        return self.telephony_manager.getNetworkType()

    def get_state(self):
        return self.telephony_manager.getDataState()

    def get_phone_type(self):
        return self.telephony_manager.getPhoneType()

    def get_operator_name(self):
        return self.network_operator.getNetworkOperatorName()
