#!/usr/bin/env python

from monitors.wifi import Wifi
from monitors.wifi import WifiUsage
from monitors.wifi import WifiState
from phones.device import DeviceConstants

import mox
import time
import unittest

class TestWifi(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()

        wifi_access = self.m.CreateMock(WifiAccess)
        wifi_access.get_name().AndReturn("eth0")
        constants = self.m.CreatMock(DeviceConstants)
        constants.WIFI_HIGHLOW_TRANS = 100
        constants.WIFI_LOWHIGH_TRANS = 300

        self.wifi = Wifi(constants)

    def tearDown(self):
        self.m.UnsetStubs()

#    def test_calc_iteration(self):
#

class TestWifiState(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()
        self.state = WifiState(2, 10)

    def tearDown(self):
        self.m.UnsetStubs()

    def test_interface_off(self):
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        self.state.interface_off()
        self.assertEqual(self.state.pwr_state, Wifi.POWER_STATE_LOW)
        self.m.VerifyAll()

    def test_is_initialized_success(self):
        """ Test if interface has been initialized before usage. To do so,
        update its stats. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        self.state.update(0, 0, 0,0)
        self.assertTrue(self.state.is_initialized())
        self.m.VerifyAll()

    def test_is_initialized_failure(self):
        self.m.ReplayAll()
        self.assertFalse(self.state.is_initialized())
        self.m.VerifyAll()

    def test_update_first_time(self):
        """ Test if most of update() logic is skipped when called for the first
        time. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(2)
        self.m.ReplayAll()

        self.state.update(2, 2, 2800, 2800)

        self.assertEqual(self.state.update_time, 2)
        self.assertEqual(self.state.tx_rate, 0)
        self.m.VerifyAll()

    def test_update_full(self):
        """ Test update() full logic by calling it twice. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(2)
        self.m.ReplayAll()

        self.state.update(2, 2, 2800, 2800)
        # Increase delta_time
        time.time().AndReturn(3)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)

        self.assertEqual(self.state.pkts, 4)
        self.assertAlmostEqual(self.state.avg_tx_pkt_size, 1490.0)
        self.assertAlmostEqual(self.state.avg_rx_pkt_size, 1490.0)
        self.assertEqual(self.state.inactive_time, 0)
        self.assertEqual(self.state.pwr_state, Wifi.POWER_STATE_LOW)
        self.m.VerifyAll()

    def test_is_stale_success(self):
        self.m.ReplayAll()
        self.assertTrue(self.state.is_stale())
        self.m.VerifyAll()

if __name__ == "__main__":
    unittest.main()
