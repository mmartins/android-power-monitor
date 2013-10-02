#!/usr/bin/env python

from __future__ import division
try:
    from libs.wifi import WifiAccess
except ImportError:
    from utils.androidhelpers.wifi import Wifi

from monitors.devicemonitor import DeviceMonitor
from services.usagedata import UsageData
from utils.hardware import Hardware
from utils.sysfs import Node
from utils.systeminfo import SystemInfo

import os
import time

class Wifi(DeviceMonitor):

    POWER_STATE_LOW = 0
    POWER_STATE_HIGH = 1

    NET_STATISTICS_MASK = "/sys/devices/virtual/net/{0}/statistics"
    UID_STATS_FOLDER = "/proc/uid_state/"
    UID_TX_BYTE_MASK = UID_STATS_FOLDER.join("{0}/tcp_snd")
    UID_RX_BYTE_MASK = UID_STATS_FOLDER.join("{0}/tcp_rcv")

    def __init__(self, devconstants):
        super(Wifi, self).__init__(Hardware.WIFI, devconstants)
        self._wifi = WifiAccess()
        iface_name = self._wifi.get_name()
        self.iface = iface_name if iface_name is not None else "eth0"
        self._state = WifiState(devconstants.WIFI_HIGHLOW_PKTBOUND,
                devconstants.WIFI_LOWHIGH_PKTBOUND)
        self._sysfs = Node(self.NET_STATISTICS_MASK.format(self.iface))
        self._uid_states = {}

        # Test file existence
        self.has_uid_information = os.access(self.UID_STATS_FOLDER, os.F_OK)

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using WiFi after one
        iteration. """
        result = IterationData()

        state = self._wifi.get_state()

        if (state != WifiAccess.WIFI_STATE_ENABLED) or (state !=
                WifiAccess.WIFI_STATE_DISABLING):

            # Allow the real interface state keeper to reset its state so that
            # the next update it knows it's coming back from an off state. We
            # also need to clear all UID information

            self._state.interface_off()
            self._uid_states.clear()
            self._speed = 0

            result.set_sys_usage(WifiUsage())
            return result

        tx_pkts = int(self._sysfs.tx_packets)
        rx_pkts = int(self._sysfs.rx_packets)
        tx_bytes = int(self._sysfs.tx_bytes)
        rx_bytes = int(self._sysfs.rx_bytes)

        if (tx_pkts == -1) or (rx_pkts == -1) or (tx_bytes == -1) or (rx_bytes
                == -1):
            self.logger.warn("Failed to read packet and byte counts from WiFi")
            return result

        # Update the link speed every 15 seconds as pulling the WifiInfo
        # structure from WifiManager is a little expensive. This isn't really
        # something that is likely to change frequently anyway

        if (iter_num % 15 == 0) or (self._speed == 0):
            self._speed = self._wifi.get_speed()

        if self._state.is_initialized():
            self._state.update(tx_pkts, rx_pkts, tx_bytes, rx_bytes)

        uids = SystemInfo.get_uids()

        if uids is not None:
            for uid in uids:
                if uid < 0:
                    break

                uid_state = self._uid_states.get(uid, None)

                if uid_state is None:
                    uid_state = WifiState(self._constants.WIFI_HIGHLOW_PKTBOUND,
                            self._constants.WIFI_LOWHIGH_PKTBOUND)
                    self._uid_states[uid] = uid_state

                if not uid_state.is_stale():
                    # Use heuristic to not poll for UIDs that haven't had much
                    # activity recently
                    continue

                # These read operations are the expensive part of polling
                with open(self.UID_TX_BYTE_MASK.format(uid)) as fp:
                    tx_bytes = int(fp.read().strip())
                with open(self.UID_RX_BYTE_MASK.format(uid)) as fp:
                    rx_bytes = int(fp.read().strip())

                if (rx_bytes == -1) or (tx_bytes == -1):
                    self.logger.warn("Failed to read UID Tx/Rx byte counts")
                elif uid_state.is_initialized():
                    # We only have info on bytes received but what we really
                    # want is the number of packets receivced so we will
                    # estimate it
                    delta_tx_bytes = tx_bytes - self._state.tx_bytes
                    delta_rx_bytes = rx_bytes - self._state.rx_bytes
                    tx_pkts = int(round(delta_tx_bytes /
                        self._state.avg_tx_pkt_size))
                    rx_pkts = int(round(delta_rx_bytes /
                        self._state.avg_rx_pkt_size))

                    if (delta_tx_bytes > 0) and (tx_pkts == 0):
                        tx_pkts = 1

                    if (delta_rx_bytes > 0) and (rx_pkts == 0):
                        rx_pkts = 1

                    active = (tx_bytes != uid_state.tx_bytes) or (rx_bytes !=
                            uid_state.rx_bytes)

                    uid_state.update((self._state.tx_pkts + tx_pkts),
                            (self._state.rx_pkts + rx_pkts), tx_pkts, rx_pkts)

                    if active:
                        usage = WifiUsage(uid_state.pkts,
                                uid_state.delta_tx_bytes,
                                uid_state.delta_rx_bytes, uid_state.tx_rate,
                                uid_state.speed, uid_state.pwr_state)
                        result.set_uid_usage(uid, usage)
                else:
                    uid_state.update(0, 0, tx_bytes, rx_bytes)

        return result

class WifiUsage(UsageData):

    __slots__ = ['speed', 'pwr_state']

    def __init__(self, pkts, tx_bytes, rx_bytes, tx_rate, speed, pwr_state):
        self.delta_pkts = pkts
        self.tx_bytes = tx_bytes
        self.rx_bytes = rx_bytes
        self.tx_rate = tx_rate
        self.speed = speed
        self.pwr_state = pwr_state

    def log(out):
        res = "Wifi-pkts {0}\nWifi-tx_bytes {1}\nWifi-rx_bytes {2}\nWifi-tx_rate{3}\nWifi-speed {4}\nWifi-pwr_state {5}\n".format(self.delta_pkts,
                self.tx_bytes, self.rx_bytes, self.tx_rate, self.speed,
                self.pwr_state)
        out.write(res)

class WifiState(object):

    __slots__ = ['_highlow_pktbound', '_lowhigh_pktbound', 'pwr_state']

    def __init__(self, highlow_pktbound, lowhigh_pktbound):
        self._highlow_pktbound = highlow_pktbound
        self._lowhigh_pktbound = lowhigh_pktbound

        self.tx_pkts = 0
        self.rx_pkts = 0
        self.tx_bytes = 0
        self.rx_bytes = 0
        self.tx_rate = 0.0
        self.delta_pkts = 0

        self.delta_tx_bytes = 0
        self.delta_rx_bytes = 0

        self.pwr_state = Wifi.POWER_STATE_LOW
        self.avg_tx_pkt_size = 1500
        self.avg_rx_pkt_size = 1500
        self._update_time = None
        self.inactive_time = 0

    def interface_off(self):
        self._update_time = round(time.time())
        self.pwr_state = Wifi.POWER_STATE_LOW

    def is_initialized(self):
        return self._update_time is not None

    def update(self, tx_pkts, rx_pkts, tx_bytes, rx_bytes):
        now = round(time.time())

        if (self._update_time is not None) and (now > self._update_time):
            delta_time = now - self._update_time
            # 1024 * 7.8125 = 131.072
            self.tx_rate = (tx_bytes - self.tx_bytes) / 131.072 / delta_time
            self.delta_pkts = rx_pkts + tx_pkts - self.rx_pkts - self.tx_pkts
            self.delta_tx_bytes = tx_bytes - self.tx_bytes
            self.delta_rx_bytes = rx_bytes - self.rx_bytes

            if tx_pkts != self.tx_pkts:
                self.avg_tx_pkt_size = (0.9 * self.avg_tx_pkt_size) + (0.1 *
                        (tx_bytes-self.tx_bytes) / (tx_pkts-self.tx_pkts))

            if rx_pkts != self.rx_pkts:
                self.avg_rx_pkt_size = (0.9 * self.avg_rx_pkt_size) + (0.1 *
                        (rx_bytes-self.rx_bytes) / (rx_pkts-self.rx_pkts))

            if (rx_bytes != self.rx_bytes) or (tx_bytes != self.tx_bytes):
                self.inactive_time = 0
            else:
                self.inactive_time += now - self._update_time

            if self.delta_pkts < self._highlow_pktbound:
                self.pwr_state = Wifi.POWER_STATE_LOW
            elif self.delta_pkts > self._lowhigh_pktbound:
                self.pwr_state = Wifi.POWER_STATE_HIGH

        self._update_time = now
        self.tx_pkts = tx_pkts
        self.rx_pkts = rx_pkts
        self.tx_bytes = tx_bytes
        self.rx_bytes = rx_bytes

    def is_stale(self):
        """ Heuristic to avoid excessive polling on UIDs. We shouldn't
        update state on every iteration as it takes too much time
        """
        if not self.is_initialized():
            return True

        # TODO: check if 10000 is the correct number (should be 10s?)
        return (round(time.time()) - self._update_time) > min(10000,
                self.inactive_time)
