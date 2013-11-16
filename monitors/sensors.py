#!/usr/env/bin python

from __future__ import division

from libs.clock import SystemClock
from libs.notification import NotificationProxy
from libs.sensors import SensorsAccess
from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.hardware import Hardware

import threading


class Sensors(DeviceMonitor):
    SENSORS = SensorsAccess.get_sensors().keys()

    def __init__(self, devconstants=None):
        super(Sensors, self).__init__(Hardware.SENSORS, devconstants)
        self._state = SensorState()
        self._uid_states = {}
        self._sensorslock = threading.Lock()

        callbacks = {
            NotificationProxy.ON_START_SENSOR: self.__on_start_sensor,
            NotificationProxy.ON_STOP_SENSOR: self.__on_stop_sensor
        }

        self.has_uid_information = True

        if NotificationProxy.is_available():
            self._event_server = NotificationProxy(callbacks)
            self._event_server.add_hook()

    def _on_exit(self):
        if NotificationProxy.is_available():
            self._event_server.remove_hook()
        super(Sensors, self)._on_exit()

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using sensors after one
        iteration. """
        result = IterationData()
        sensor_usage = SensorUsage()

        with self._sensorslock:
            sensor_usage.on_times = self._state.get_times()
            result.set_sys_usage(sensor_usage)

            for uid, state in self._uid_states.iteritems():
                usage = SensorUsage()
                usage.on_times = state.get_times()
                result.set_uid_usage(uid, usage)

                if state.started_sensors == 0:
                    del (self._uid_states[uid])

        return result

    def __on_start_sensor(self, uid, sensor):
        with self._sensorslock:
            self._state.start_sensor(sensor)
            uid_state = self._uid_states.setdefault(uid, SensorState())
            uid_state.start_sensor(sensor)

    def __on_stop_sensor(self, uid, sensor):
        with self._sensorslock:
            self._state.stop_sensor(sensor)
            uid_state = self._uid_states.setdefault(uid, SensorState())
            uid_state.stop_sensor(sensor)


class SensorUsage(UsageData):
    def __init__(self):
        super(SensorUsage, self).__init__()
        self.on_times = {}

    def log(self, out):
        res = "Sensors-time: {}\n".format(self.on_times)
        out.write(res)


class SensorState(object):
    __slots__ = ['_on', '_on_times', 'started_sensors']

    def __init__(self):
        self._on = dict.fromkeys(Sensors.SENSORS, 0)
        self._on_times = dict.fromkeys(Sensors.SENSORS, 0)
        self._timestamp = SystemClock.elapsedRealtime()
        self.started_sensors = 0

    def start_sensor(self, name):
        if (name in self._on) and (self._on[name] == 0):
            self._on_times[name] -= SystemClock.elapsedRealtime() -\
                self._timestamp
            self.started_sensors += 1

        # WARNING: May break when name is invalid
        self._on[name] += 1

    def stop_sensor(self, name):
        if name in self._on:
            if self._on[name] == 0:
                return
            if self._on[name] - 1 == 0:
                self._on_times[name] += (SystemClock.elapsedRealtime() -
                                         self._timestamp)
                self.started_sensors -= 1
            self._on[name] -= 1

    def get_times(self):
        now = SystemClock.elapsedRealtime()
        div = now - self._timestamp

        if div <= 0:
            div = 1

        times = {}

        for k, v in self._on_times.iteritems():
            factor = now - self._timestamp if self._on.get(k, 0) > 0 else 0
            times[k] = (v + factor) / div
            self._on_times[k] = 0

        self._timestamp = now
        return times
