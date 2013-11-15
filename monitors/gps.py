#!/usr/bin/env python

from __future__ import division

from libs.sdk import Build
from libs.gps import GPSListener
from libs.notification import NotificationProxy

from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.hardware import Hardware
from utils.systeminfo import SystemInfo

import logging
import threading
import time


class GPS(DeviceMonitor):
    # Constants from android.location.GpsStatus
    GPS_EVENT_STARTED = 1
    GPS_EVENT_STOPPED = 2
    GPS_EVENT_FIRST_FIX = 3
    GPS_EVENT_SATELLITE_STATUS = 4

    # Local constants
    GPS_STATUS_SESSION_BEGIN = 1
    GPS_STATUS_SESSION_END = 2
    GPS_STATUS_ENGINE_ON = 3
    GPS_STATUS_ENGINE_OFF = 4

    NO_HOOKS = 0
    HOOK_GPS_STATUS_LISTENER = 1
    HOOK_NOTIFICATIONS = 2
    HOOK_TIMER = 4

    POWER_STATE_OFF = 0
    POWER_STATE_SLEEP = 1
    POWER_STATE_ON = 2
    NPOWER_STATES = 3

    def __init__(self, devconstants):
        super(GPS, self).__init__(Hardware.GPS, devconstants)
        self._uid_states = {}
        self._sleep_time = round(1000 * devconstants.GPS_SLEEP_TIME)
        self._update_time = 0
        self._hook_method = 0
        self._statekeeper = None
        self._status = None

        self._setup_gps_hook()

        self._uidstates_lock = threading.Lock()
        self._statekeeper_lock = threading.Lock()
        self._gpsstatus_lock = threading.Lock()

        # Track physical state
        self._statekeeper = GPSState(self._hook_method, self._sleep_time)

        # We need a GPS listener so that we can get the satellite count. Also
        # if anything goes wrong with the libgps hook, we revert to using this
        self._listener = GPSListener(self.__on_gps_status_changed)
        self._listener.start()

        # Use notification service to gather UID information if it's available

        callbacks = {
            NotificationProxy.ON_START_WAKELOCK: self.__on_start_wakelock,
            NotificationProxy.ON_STOP_WAKELOCK: self.__on_stop_wakelock,
            NotificationProxy.ON_START_GPS: self.__on_start_gps,
            NotificationProxy.ON_STOP_GPS: self.__on_start_gps,
        }

        if NotificationProxy.is_available():
            self._event_server = NotificationProxy(callbacks)
            self._event_server.add_hook()

    def _on_exit(self):
        self._listener.stop()

        if NotificationProxy.is_available():
            self._event_server.remove_hook()

        super(GPS, self)._on_exit()

    @property
    def has_uid_information(self):
        return NotificationProxy.is_available()

    def _setup_gps_hook(self):
        """ Setup method for collecting GPS state information. """
        # We can always use the status listener hook and perhaps the
        # notification hook if we are running eclaire or higher and the
        # notification hook is installed. We can only do this on eclaire or
        # higher because it wasn't until eclaire that they fixed a bug
        # where they didn't maintain a wakelock while the GPS engine was on
        self._hook_method = self.HOOK_GPS_STATUS_LISTENER

        try:
            # >= 5: eclair or higher
            if ((NotificationProxy.is_available() and
                    int(Build.VERSION.SDK_INT) >= 5)):
                self._hook_method |= self.HOOK_NOTIFICATIONS
        except ValueError:
            pass

        # If we don't have a way of getting the off<->sleep transitions via
        # notifications, let's just use a timer and simulate the state of
        # the GPS instead

        if self._hook_method & self.HOOK_NOTIFICATIONS == self.NO_HOOKS:
            self._hook_method |= self.HOOK_TIMER

    def __on_start_wakelock(self, uid, name, lock_type):
        """ Callback method for GPS status monitor. """
        if (uid == SystemInfo.AID_SYSTEM) and (name == "GpsLocationProvider"):
            self._statekeeper.update_event(self.GPS_STATUS_ENGINE_ON,
                                           self.HOOK_NOTIFICATIONS)

    def __on_stop_wakelock(self, uid, name, lock_type):
        """ Callback method for GPS status monitor. """
        if (uid == SystemInfo.AID_SYSTEM) and (name == "GpsLocationProvider"):
            self._statekeeper.update_event(self.GPS_STATUS_ENGINE_OFF,
                                           self.HOOK_NOTIFICATIONS)

    def __on_start_gps(self, uid):
        """ Callback method for GPS status monitor. """
        self.update_uid_event(uid, self.GPS_STATUS_SESSION_BEGIN,
                              self.HOOK_NOTIFICATIONS)

    def __on_stop_gps(self, uid):
        """ Callback method for GPS status monitor. """
        self.update_uid_event(uid, self.GPS_STATUS_SESSION_END,
                              self.HOOK_NOTIFICATIONS)

    def __on_gps_status_changed(self, event):
        """ Callback method for GPS status monitor. """
        if event == self.GPS_EVENT_STARTED:
            self._statekeeper.update_event(self.GPS_STATUS_SESSION_BEGIN,
                                           self.HOOK_GPS_STATUS_LISTENER)
        elif event == self.GPS_EVENT_STOPPED:
            self._statekeeper.update_event(self.GPS_STATUS_SESSION_END,
                                           self.HOOK_GPS_STATUS_LISTENER)
        with self._gpsstatus_lock:
            self._status = self._listener.gps_status

    def update_uid_event(self, uid, event, hook_source):
        """ Update GPS state machine for given UID """
        with self._uidstates_lock:

            state = self._uid_states.get(uid, None)

            if not state:
                state = GPSState(self.HOOK_NOTIFICATIONS | self.HOOK_TIMER,
                                 self._sleep_time, self._update_time)
                self._uid_states[uid] = state

            state.update_event(event, hook_source)

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using GPS after one
        iteration. """
        result = IterationData()

        # Get the power data for the physical GPS device

        with self._statekeeper_lock:
            state_times = self._statekeeper.state_times
            pwr_state = self._statekeeper.pwr_state
            self._statekeeper.reset_times()

        # Get the number of satellite that were available in the last update

        num_satellites = 0
        with self._gpsstatus_lock:
            if pwr_state == self.POWER_STATE_ON and self._status is not None:
                num_satellites = len(self._status.getSatellites())

        result.set_sys_usage(GPSUsage(state_times, num_satellites))

        # Get usage data for each UID we have information on
        if self.has_uid_information:
            with self._uidstates_lock:
                self._update_time = (self._start_time + self._iter_interval *
                                     iter_num)
                for uid, state in self._uid_states.iteritems():
                    state_times = state.get_state_times()
                    pwr_state = state.get_power_state()
                    state.reset_times()

                    # There is a guarantee that num_satellites will be zero
                    # if GPS is off (see above)
                    result.set_uid_usage(uid, GPSUsage(state_times,
                                                       num_satellites))

                    # Remove state information for UIDs no longer using the GPS
                    if pwr_state == self.POWER_STATE_OFF:
                        del (self._uid_states[uid])

        return result


class GPSUsage(UsageData):
    __slots__ = ['num_satellites']

    def __init__(self, state_times, num_satellites):
        """ A usage time is the time in seconds since the last data update.
        Number of satellites is only available whil the GPS is on.
        """
        super(GPSUsage, self).__init__()
        # TODO: Should be dictionary
        self.state_times = state_times
        self.num_satellites = num_satellites

    def log(self, out):
        res = "GPS-state-times: {} GPS-num_satellites: {}\n".format(
            self.state_times, self.num_satellites)
        out.write(res)


class GPSState(object):
    """ Container for storing actual GPS state in addition to simulating
    individual UID states. """

    logger = logging.getLogger("GPSState")

    def __init__(self, hook_mask, sleep_time=None, update_time=None):
        # The union of whatever valid hook sources. See HOOK_ constants
        self._hook_mask = hook_mask
        # The time GPS hardware should turn off. Only used if HOOK_TIMER is in
        # hook_mask. Not useful if HOOK_TIMER is not set
        self._off_time = None
        # Time GPS remains in sleep state after session has ended
        # (seconds)
        self._sleep_time = sleep_time

        if not update_time:
            self._update_time = round(time.time())
        else:
            self._update_time = update_time

        self._state_times = []
        self.pwr_state = GPS.POWER_STATE_OFF

    @property
    def state_times(self):
        self._update_times()

        # Let's normalize the times so that power measurements are consistent
        norm = sum(self._state_times)
        if norm == 0.0:
            norm = 1.0

        self._state_times[:] = [e / norm for e in self._state_times]

        return self._state_times

    def reset_times(self):
        self._state_times = [0] * GPS.NPOWER_STATES

    def update_event(self, event, hook_source):
        """ When a hook source gets an event, it should report it to this
        function. The only exception is HOOK_TIME which is handled within this
        class itself.
        """
        # TODO: Access should be locked
        if (self._hook_mask & hook_source) == GPS.NO_HOOKS:
            # We are not using this hook source, ignore.
            return

        self._update_times()
        prev_state = self.pwr_state

        if event == GPS.GPS_STATUS_SESSION_BEGIN:
            self.pwr_state = GPS.POWER_STATE_ON
        elif event == GPS.GPS_STATUS_SESSION_END:
            if self.pwr_state == GPS.POWER_STATE_ON:
                self.pwr_state = GPS.POWER_STATE_SLEEP
        elif event == GPS.GPS_STATUS_ENGINE_ON:
            if self.pwr_state == GPS.POWER_STATE_OFF:
                self.pwr_state = GPS.POWER_STATE_SLEEP
        elif event == GPS.GPS_STATUS_ENGINE_OFF:
            self.pwr_state = GPS.POWER_STATE_OFF
        else:
            self.logger.error("Unknown GPS event capture: {0}".format(event))

        if self.pwr_state != prev_state:
            if ((prev_state == GPS.POWER_STATE_ON) and
                    (self.pwr_state == GPS.POWER_STATE_SLEEP)):
                self._off_time = time.time() + self._sleep_time
            else:
                # Any other state transition should reset the off timer
                self._off_time = None

    def _update_times(self):
        now = round(time.time())

        # Check if GPS has gone to sleep state due to timer
        if ((self._hook_mask & GPS.HOOK_TIMER != GPS.NO_HOOKS) and
                (self._off_time is not None) and (self._off_time < now)):
            self._state_times[self.pwr_state] += (self._off_time -
                                                  self._update_time) / 1000
            self.pwr_state = GPS.POWER_STATE_OFF
            self._off_time = None

        # Update the amount of time that we've been in the current state
        self._state_times[self.pwr_state] += ((now - self._update_time) /
                                              1000)
        self._update_time = now
