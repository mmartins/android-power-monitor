#!/usr/bin/env python

from __future__ import division

try:
    from libs.build import Build
except ImportError:
    from utils.androidhelpers.build import Build
try:
    from utils.androidhelpers.gps import GpsListener
except ImportError:
    from libs.gps import GpsListener
try:
    from libs.notification import NotificationProxy
except ImportError:
    from utils.androidhelpers.notification import NotificationProxy

from android.broadcast import BroadcastReceiver
from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from services.notification import NotificationService
from services.usagedata import UsageData
from utils.hardware import Hardware

import logging
import threading

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

    HOOK_GPS_STATUS_LISTENER = 1
    HOOK_NOTIFICATIONS = 2

    POWER_STATE_OFF = 0
    POWER_STATE_SLEEP = 1
    POWER_STATE_ON = 2
    NPOWER_STATES = 3

    def __init__(self, devconstants):
        super.__init__(GPS, self).__init__(Hardware.GPS, devconstants)
        self.uid_states = {}
        self._sleep_time = round(1000.0 * devconstants.GPS_SLEEP_TIME)
        self._hook_method = 0
        self._statekeeper = None

        self._setup_gps_hook()

        self._uidstates_lock = threading.Lock()
        self._statekeeper_lock = threading.Lock()

        # Track physical state
        self._statekeeper = GPSState(self._hook_method, self._sleep_time)

        # We need a GPS listener so that we can get the satellite count. Also
        # if anything goes wrong with the libgps hook, we revert to using this
        self._listener = GPSListener(self.__on_gps_status_changed)
        self._listener.start()

        # Use notification service to gather UID information if it's available

        callbacks = {
                NotificationProxy.ON_START_WAKELOCK : self.__on_start_wakelock,
                NotificationProxy.ON_STOP_WAKELOCK : self.__on_stop_wakelock,
                NotificationProxy.ON_START_GPS : self.__on_start_gps,
                NotificationProxy.ON_STOP_GPS : self.__on_start_gps,
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
                Build.VERSION.SDK_INT >= 5)):
                self._hook_method |= self.HOOK_NOTIFICATIONS
        except ValueError:
            pass

        # If we don't have a way of getting the off<->sleep transitions via
        # notifications, let's just use a timer and simulate the state of
        # the GPS instead

        if ((self._hook_method & self.HOOK_NOTIFICATIONS == 0):
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

    def update_uid_event(self, uid, event, hook_source):
        """ Update GPS state machine for given UID """
        with self._uidstates_lock:

            state = self._uid_states.get(uid, None)

            if state is None:
                state = GPSState(self.HOOK_NOTIFICATIONS | self.HOOK_TIMER,
                        self._sleep_time, self._update_time)
                state.update_event(event, hook_source)
                self._uid_states[uid] = state
            else:
                state.update_event(event, hook_source)

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using GPS after one
        iteration. """
        result = IterationData()

        # Get the power data for the physical GPS device

        with self._statekeeper_lock:
            state_times = self._statekeeper.get_start_times()
            pwr_state = self._statekeeper.get_power_state()
            self._statekeeper.reset_times()

        # Get the number of satellitle that were available in the last update

        num_satellites = 0
        if pwr_state == self.POWER_STATE_ON and self.status is not None:
            num_satellites = len(self.status.getSatellites())

        result.set_sys_usage(GPSUsage(state_times, num_satellites))

        # Get usage data for each UID we have information on
        if self.has_uid_information:
            with self._uidstates_lock:
                self.update_time = (self._start_time + self._iter_interval *
                        iter_num)
                for uid, state in self._uid_states.iteritems():
                    state_times = state.get_state_times()
                    pwr_state = state.get_power_state()
                    if pwr_state == self.POWER_STATE_ON:
                        usage = GPSUsage(state_times, num_satellites)
                    else:
                        usage = GPSUsage(state_times, 0)
                    state.reset_times()

                    result.set_uid_usage(uid, usage)

                    # Remove state information for UIDs no longer using the GPS
                    if pwr_state == self.POWER_STATE_OFF:
                        del(uid_states[uid])

        return result

class GPSUsage(UsageData):

    __slots__ = ['num_satellites']

    def __init__(self, state_times=None, num_satellites=None):
        """ A usage time is the time in seconds since the last data update.
        Number of satellites is only available whil the GPS is on.
        """
        self.state_times = state_times
        self.num_satellites = num_satellites

    def log(self, out):
        res = "GPS-state-times {0}\nGPS-num_satellites {1}\n".format(
                self.state_times, self.num_satellites)
        out.write(res)

class GPSState(object):
    """ Container for storing actual GPS state in addition to simulating
    individual UID states. """

    logger = logging.getLogger("GPSState")

    def __init__(self, hook_mask, sleep_time=0.0, update_time=None):
        # The union of whatever valid hook sources. See HOOK_ constants
        self._hook_mask = hook_mask
        # The time GPS hardware should turn off. Only used if HOOK_TIMER is in
        # hook_mask. Not useful if HOOK_TIMER is not set
        self._off_time = 0.0
        # Time GPS remains in sleep state after session has ended
        # (seconds)
        self._sleep_time = sleep_time

        if update_time is None:
            self._update_time = round(time.time())
        else:
            self._update_time = update_time

        self._state_times = []
        self.pwr_state = self.POWER_STATE_OFF

    @property
    def state_times(self):
        self._update_times()

        # Let's normalize the times so that power measurements are consistent
        norm = sum(self._state_times)
        if norm == 0.0:
            norm = 1.0

        self._state_times[:] = [e/norm for e in self._state_times]

        return self._state_times

    def reset_times(self):
        self._state_times = [0 for i in xrange(self.NPOWER_STATES)]

    def update_event(self, event, hook_source):
        """ When a hook source gets an event, it should report it to this
        function. The only exception is HOOK_TIME which is handled within this
        class itself.
        """
        # TODO: Access should be locked
        if (self._hook_mask & hook_source) == 0:
            # We are not using this hook source, ignore.
            return

        self._update_times()
        prev_state = self.pwr_state

        if event == self.GPS_STATUS_SESSION_BEGIN:
            self.pwr_state = self.POWER_STATE_ON
        elif event == self.GPS_STATUS_SESSION_END:
            if self.pwr_state == self.POWER_STATE_ON:
                self.pwr_state = self.POWER_STATE_SLEEP
        elif event == self.GPS_STATUS_ENGINE_ON:
            if self.pwr_state == self.POWER_STATE_OFF:
                self.pwr_state = self.POWER_STATE_SLEEP
        elif event == self.GPS_STATUS_ENGINE_OFF:
            self.pwr_state = self.POWER_STATE_OFF
        else:
            logger.warn("Unknown GPS event capture: {0}".format(event))

        if self.pwr_state != prev_state:
            if (prev_state == self.POWER_STATE_ON) and (self.pwr_state ==
                    self.POWER_STATE_SLEEP):
                self.off_time = time.time() + self._sleep_time
            else:
                # Any other state transition should reset the off timer
                self._off_time = 0

    def _update_times(self):
        now = round(time.time())

        # Check if GPS has gone to sleep state due to timer
        if ((self.hook_mask & self.HOOK_TIMER != 0) and (self._off_time != 0)
                and (self._off_time < now)):
            self._state_times[self.pwr_state] += (self._off_time -
                    self._update_time) / 1000
            self.pwr_state = self.POWER_STATE_OFF
            self._off_time = 0

        # Update the amount of time that we've been in the current state
        self._state_times[self.pwr_state] += ((now - self._update_time) /
                1000)

        self._update_time = now
