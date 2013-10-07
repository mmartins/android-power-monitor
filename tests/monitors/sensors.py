#!/usr/bin/env python

from monitors.sensors import Sensors
from monitors.sensors import SensorState
from monitors.sensors import SensorUsage
from phones.device import DeviceConstants
from services.notification import NotificationService

import mox          # for mock testing
import time
import unittest

class TestSensors(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_calc_iteration(self):
        # Setup sensors instance
        constants = self.m.CreateMock(DeviceConstants)
        state = self.m.CreateMock(SensorState)
        self.m.StubOutWithMock(NotificationService, "add_hook")
        self.m.StubOutWithMock(NotificationService, "remove_hook")
        NotificationService.add_hook(None).AndReturn()
        NotificationService.remove_hook(None).AndReturn()

        self.sensors = Sensors(constants)
        usage = self.m.CreateMock(SensorUsage)
        usage.get_times().AndReturn({1: 30})

        self.m.replayAll()

        res = self.sensors.calc_iteration(None)

        self.assertEqual(res.keys(), 1)
        self.assertEqual(res.values(), 60)

        self.m.VerifyAll()

class TestSensorState(unittest.TestCase):

    def setUp(self):
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_start_sensor_success(self):
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()
        # Make sure the next call to time.time() in start_sensor returns an
        # update clock
        time.time().AndReturn(5)
        self.m.ReplayAll()

        state.start_sensor('accelerometer')

        self.assertEqual(state._on_times['accelerometer'], 1)
        self.assertEqual(state.started_sensors, 1)
        self.m.VerifyAll()

    def test_start_same_sensor_twice(self):
        """ Test if calling start_sensor twice keep its state consistents --
        only first call modifies state
        """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()
        # Make sure the next call to time.time() in start_sensor returns an
        # update clock
        time.time().AndReturn(5)
        self.m.ReplayAll()

        self.state.start_sensor('accelerometer')

        # SECOND CALL BELOW: Should not affect state
        #
        self.state.start_sensor('accelerometer')

        self.assertEqual(self.state._on_times['accelerometer'], 1)
        self.assertEqual(self.state.started_sensors, 1)
        self.verifyAll()

    def test_start_unknown_sensor(self):
        """ Test if start_sensor deals with unknown sensor correctly --
        shouldn't change anything
        """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()

        self.state.start_sensor('compass')

        self.assertEqual(self.state.started_sensors, 0)
        self.m.VerifyAll()

    def test_stop_sensor_success(self):
        """ Test if start_sensor and stop_sensor for the same sensor name
        updates its state coherently.
        """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()
        # Make sure the next call to time.time() in start_sensor returns an
        # update clock
        time.time().AndReturn(5)
        self.m.ReplayAll()

        state.start_sensor('accelerometer')

        time.time().AndReturn(7)
        self.m.ReplayAll()

        state.stop_sensor('accelerometer')

        self.assertEqual(state._on_times['accelerometer'], 4)
        self.assertEqual(state.started_sensors, 0)
        self.m.VerifyAll()

    def test_stop_same_sensor_twice(self):
        """ Test if a sensor stopped multiple times has its state updated only
        once.
        """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()
        # Make sure the next call to time.time() in start_sensor returns an
        # update clock
        time.time().AndReturn(5)
        self.m.ReplayAll()

        state.start_sensor('accelerometer')

        time.time().AndReturn(7)
        self.m.ReplayAll()

        state.stop_sensor('accelerometer')
        # SECOND CALL BELOW: shouldn't change anything
        state.stop_sensor('accelerometer')

        self.assertEqual(state._on_times['accelerometer'], 4)
        self.assertEqual(state.started_sensors, 0)
        self.m.VerifyAll()

    def test_stop_sensor_not_started(self):
        """ Test if non-started sensor keeps its state the same even if told to
        stop. """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()

        state.stop_sensor('accelerometer')

        self.assertEqual(state.stopped_sensors, 0)
        self.m.VerifyAll()

    def test_stop_unknown_sensor(self):
        """ Test if start_sensor deals with unknown sensor correctly --
        shouldn't change anything
        """
        self.m.StubOutClassWithMocks(Sensors)
        Sensors.SENSORS = ['accelerometer', 'magnetometer']

        # SensorState.__init__ calls time.time(), which is not deterministic
        self.m.StubOutWithMock(time, "time")
        time.time().AndReturn(3)
        state = SensorState()

        self.m.ReplayAll()

        state.stop_sensor('compass')

        self.assertEqual(state.started_sensors, 0)
        self.m.VerifyAll()
