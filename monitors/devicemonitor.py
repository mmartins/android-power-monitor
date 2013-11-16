#!/usr/bin/env python

from libs.clock import SystemClock
import logging
import threading
import time


class DeviceMonitor(threading.Thread):
    __slots__ = ["_constants", "has_uid_information"]

    def __init__(self, monitor_name, devconstants):
        self.daemon = True

        self.has_uid_information = False
        self.monitor_name = monitor_name
        self._constants = devconstants
        self.logger = logging.getLogger(monitor_name)
        self._stop = threading.Event()

        super(DeviceMonitor, self).__init__(target=self._run)
        self._data_lock = threading.Lock()
        #self.start()

    def _prepare(self, iter_interval=1):
        """ Called once at the beginning of the daemon loop. """
        self._start_time = SystemClock.elapsedRealtime()
        self._iter_interval = iter_interval # Every second

        # Iteration-data buffers for cycling during data collection
        self._data1 = None
        self._data2 = None
        self._iter1 = -1
        self._iter2 = -1

    def _run(self):
        """ Runs the daemon loop that collects data for this monitor."""

        # Hands off to client class to actually calculate the information we
        # want for this monitor

        iter_num = 0
        self._prepare()

        while not self.is_stopped():
            data = self.calc_iteration(iter_num)
            if data is not None:
                with self._data_lock:
                    if self._iter1 < self._iter2:
                        self._iter1 = iter_num
                        self._data1 = data
                    else:
                        self._iter2 = iter_num
                        self._data2 = data

            if not self.is_stopped():
                break

            now = SystemClock.elapsedRealtime()
            # Compute the next iteration that we can make the start of
            prev_iter = iter_num
            iter_num = max((iter_num + 1), 1 + (now - self._start_time) /
                           self._iter_interval)

            if prev_iter + 1 != iter_num:
                self.logger.warn("Had to skip iteration {0} to "
                                 "{1}".format(prev_iter, iter_num))

            # Sleep until next iteration completes
            time.sleep(self._start_time + iter_num * self._iter_interval - now)

        self._on_exit()

    def stop(self):
        self._stop.set()

    def is_stopped(self):
        return self._stop.isSet()

    def _on_exit(self):
        """ Called when thread running this interface is asked to exit """
        pass

    def calc_iteration(self, iter_num):
        """ Extending classes need to override this function. It should
        calculate the data point for the given monitor in a timely manner
        (under 1 second, loger times will cause data to be missed). The
        iteration parameter can be ignored in most cases.

        Integer -> IterationData
        """
        raise NotImplementedError

    def get_data(self, iter_num):
        """ Returns data point for given iteration. Method should be called
        with a strictly increasing iteration parameter

        Integer -> Data
        """
        with self._data_lock:
            ret = None
            if iter_num == self._iter1:
                ret = self._data1
            if iter_num == self._iter2:
                ret = self._data2

            if self._iter1 <= iter_num:
                self._data1 = None
                self._iter1 = -1
            if self._iter2 <= iter_num:
                self._data2 = None
                self._iter2 = -1

        if not ret:
            self.logger.warn("Could not find data for requested iteration")

        return ret
