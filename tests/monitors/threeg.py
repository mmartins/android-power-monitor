#!/usr/bin/env python

from monitors.threeg import ThreeG
from monitors.threeg import ThreeGUsage
from monitors.threeg import ThreeGState
from phones.device import DeviceConstants

import mox
import time
import unittest

class TestThreeG(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()
        self.constants = self.m.CreateMock(DeviceConstants)
        telephony = self.m.CreateMock(TelephonyAccess)

    def tearDown(self):
        self.m.UnsetStubs()

    def test_calc_iteration(self):
        pass


class TestThreeState(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()
        self.state = ThreeGState(2, 1, 0, 0)

    def tearDown(self):
        self.m.UnsetStubs()

    def test_interface_off(self):
        self.state.interface_off()
        self.assertEqual(self.state.pwr_state, ThreeG.POWER_STATE_IDLE)

    def test_is_initialized_success(self):
        """ Test if interface has been initialized before usage. To do so,
        update its stats. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        self.state.update(0, 0, 0, 0)
        self.assertTrue(self.state.is_initialized())
        self.m.VerifyAll()

    def test_is_initialized_failure(self):
        self.assertFalse(self.state.is_initialized())

    def test_update_first_time(self):
        """ Test if most of update() logic is skipped when called for the first
        time. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        self.state.update(2, 2, 2800, 2800)
        self.assertEqual(self.state.pkts, 4)
        self.m.VerifyAll()

    def test_update_idlefach(self):
        """ Test update() for IDLE -> FACH state transition. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        # Initial state update
        self.state.update(2, 2, 2800, 2800)

        # Increase delta_time
        # IDLE -> FACH
        time.time().AndReturn(1)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)
        self.assertEqual(self.state.pkts, 4)
        self.assertFalse(self.state.inactive)
        self.assertTrue(self.state.pwr_state, ThreeG.POWER_STATE_FACH)
        self.m.VerifyAll()

    def test_update_fachdch(self):
        """ Test update() for FACH -> DCH state transition. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        # Initial state update
        self.state.update(2, 2, 2800, 2800)

        # Increase delta_time
        # IDLE -> FACH
        time.time().AndReturn(1)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)

        # FACH -> DCH
        time.time().AndReturn(2)
        self.m.ReplayAll()

        self.state.update(6, 6, 11200, 11200)
        self.assertEqual(self.state.pkts, 4)
        self.assertFalse(self.state.inactive)
        self.assertTrue(self.state.pwr_state, ThreeG.POWER_STATE_DCH)
        self.m.VerifyAll()

    def test_update_dchfach(self):
        """ Test update() for FACH -> DCH state transition. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        # Initial state update
        self.state.update(2, 2, 2800, 2800)

        # Increase delta_time
        # IDLE -> FACH
        time.time().AndReturn(1)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)

        # FACH -> DCH
        time.time().AndReturn(2)
        self.m.ReplayAll()

        self.state.update(6, 6, 11200, 11200)

        # DCH -> FACH
        time.time().AndReturn(4)
        self.m.ReplayAll()

        self.state.update(6, 6, 11200, 11200)

        self.assertEqual(self.state.pkts, 0)
        self.assertTrue(self.state,inactive)
        self.assertTrue(self.state.pwr_state, ThreeG.POWER_STATE_FACH)
        self.m.VerifyAll()

    def test_update_fachidle(self):
        """ Test update() for FACH -> IDLE state transition. """
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(0)
        self.m.ReplayAll()

        # Initial state update
        self.state.update(2, 2, 2800, 2800)

        # Increase delta_time

        # IDLE -> FACH
        time.time().AndReturn(1)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)

        # FACH -> IDLE
        time.time().AndReturn(3)
        self.m.ReplayAll()

        self.state.update(4, 4, 5600, 5600)
        self.assertEqual(self.state.pkts, 0)
        self.assertTrue(self.state.inactive)
        self.assertTrue(self.pwr_state, ThreeG.POWER_STATE_IDLE)
        self.m.VerifyAll()

    def test_is_stale_success(self):
        self.assetTrue(self.state.is_stale())

if __name__ == "__main__":
    unittest.main()
