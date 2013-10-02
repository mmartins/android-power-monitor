#!/usr/bin/env python

from __future__ import division
from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.hardware import Hardware
from utils.systeminfo import SystemInfo

class CPU(DeviceMonitor):

    TAG_MASK = Hardware.CPU + "{0}"
    CPUINFO_FILE = "/proc/cpuinfo"
    STAT_FILE = "/proc/stat"
    SYSFS_FREQ_FILE_MASK = "/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_cur_freq"

    def __init__(self, devconstants, num=0):
        super(CPU, self).__init__(self.TAG_MASK.format(num), devconstants)

        self._state = CPUState(SystemInfo.AID_ALL)
        self._pid_states = {}
        self._uid_states = {}
        self.num = num
        self.cpufreq_file = self.SYSFS_FREQ_FILE_MASK.format(num)

        self.has_uid_information = True

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using CPU core after one
        iteration. """
        result = IterationData()

        freq = self._read_cpu_freq()

        if freq == 0:
            self.logger.warn("Failed to read CPU frequency")
            return result

        times = SystemInfo.get_usr_total_times(self.num)

        if times == []:
            self.logger.warn("Failed to read CPU times")
            return result

        usr_time = times[SystemInfo.INDEX_USR_TIME]
        sys_time = times[SystemInfo.INDEX_SYS_TIME]
        total_time = times[SystemInfo.INDEX_TOTAL_TIME]

        self._state.update(usr_time, sys_time, total_time, iter_num)

        # Power draw is based on usage time along with CPU frequency
        if self._state.is_initialized():
            result.set_sys_usage(CPUUsage(self._state.get_usr_perc(),
                    self._state.get_sys_perc(), freq))

        # Distribute CPU power draw during iteration among running processes.
        # CPU usage is returned by Linux using process ID.
        # A UID can have many processes and our final result should be based on
        # UID (app), therefore we need to account for all processes referring
        # to the same UID
        self._uid_states.clear()
        pids = SystemInfo.get_running_pids(pids)

        if pids is not None:
            for i, pid in enumerate(pids):
                if pid < 0:
                    break

                pid_state = self._pid_states.get(pid, None)

                # New process that hasn't been registered yet by our monitor
                if pid_state is None:
                    uid = SystemInfo.get_uid_for_pid(pid)

                    if uid >= 0:
                        self._pid_states[pid] = CpuState(uid)
                    else:
                        # Assume process no longer exists
                        continue

                if pid_state.is_stale(iter_num):
                    # Nothing much is going on with this PID recently. We'll
                    # just assume that it's not using any of the CPU for this
                    # iteration
                    pid_state.skip_update(iter_num, total_time)
                else:
                    times = SystemInfo.get_pid_usr_sys_times(pid)

                    if times != []:
                        usr_time = times[SystemInfo.INDEX_USR_TIME]
                        sys_time = times[SystemInfo.INDEX_SYS_TIME]

                        # Update slice of time used by this process based on
                        # global iteration time
                        pid_state.update(usr_time, sys_time, total_time,
                                iter_num)

                        if not pid_state.is_initialized():
                            continue

                uid_state = self._uid_states.get(pid_state.uid, None)

                # Register new UID if it doesn't exist. Else absorb power data
                # from its respective process
                if uid_state is not None:
                    self._uid_states[pid_state.uid] = pid_state
                else:
                    uid_state.absorb(pid_state)

        # Remove processes that are no longer active
        self._pid_states = {k: v for k, v in self._pid_states.iteritems() if
                self._pid_states[k].is_alive(iter_num)}

        # Collect the summed UID information
        for k, v in self._uid_states.iteritems():
            uid_usage = self._get_cpu_usage(uid_state.get_usr_perc(),
                    uid_state.get_sys_perc(), freq)
            result.set_uid_usage(uid, uid_usage)

        return result

    def _get_cpu_usage(self, usr_perc, sys_perc, freq):
        """ Predicts the CPU P-state as if it was running a single process. Finds
        the lowest frequency that keeps the CPU usage under 70% assuming there
        is a linear relationship to CPU utilization at different frequencies
        """
        freqs = self._constants.CPU_FREQS

        if usr_perc + sys_perc < 1e-6:
            # Don't waste time with binary search if there is no utilization
            # which will be the case most of the time
            return CPUUsage(sys_perc, usr_perc, freqs[0])

        lo = 0
        hi = len(freqs) - 1
        perc = sys_perc + usr_perc

        while lo < hi:
            mid = (lo + hi) // 2
            nperc = perc * freq / freqs[mid]
            if nperc < 70.0:
                hi = mid
            else:
                lo = mid + 1

        return CPUUsage(sys_perc * freq/freqs[lo], usr_perc * freq/freqs[lo],
                freqs[lo])

    def _read_cpu_freq(self):
        """ Update the frequency of the processor core in MHz. If frequency
        cannot be determined, return 0.
        """

        # Try to read from /sys/devices file first
        try:
            with open(self.cpufreq_file, 'r') as fp:
                freq_khz = fp.read().strip()
            if freq_khz.isdigit():
                return int(freq_khz) // 1000
        except (IOError, ValueError), (errno, strerror):
            pass

        try:
            with open(self.CPUINFO_FILE, 'r') as fp:
                data = fp.readlines()
                # Core frequency at every 3 lines
                freq_line = 3 * (self.num+1)
                if data[freq_line-1].startswith("BogoMIPS"):
                    return int(data.split(":")[1].strip())
        except (IOError, IndexError, ValueError), (errno, strerror):
            self.logger.error("Failed to read CPU{0} frequency: {1}".format(
                self.num, strerror))

        return 0

class CPUUsage(UsageData):

    __slots__ = ['_freq']

    def __init__(self, sys_perc, usr_perc, freq):
        super(CPUUsage, self).__init__(self)

        self._sys_perc = sys_perc
        self._usr_perc = usr_perc
        self._freq = freq

    def log(self, out):
        """ Raises IOError error if output stream can't be written
        """
        out.write("CPU-sys {0}\n CPU-usr {1}\n CPU-freq {2}\n".format(
                self._sys_perc, self._usr_perc, self._freq))

class CPUState(object):

    __slots__ = ['_iteration', '_inactive_iters']

    def __init__(self, uid):
        self.uid = uid
        self._last_usr = 0
        self._last_sys = 0
        self._last_total = 0
        self._delta_usr = 0
        self._delta_sys = 0
        self._delta_total = 1
        self._last_update = 0
        self._iteration = 0
        self._inactive_iters = 0

    def is_initialized(self):
        return self._last_usr != 0

    def skip_update(self, iteration, total_time):
        """ Process is still running but we skip reading the CPU utilization
        for this iteration to avoid wasting CPU cycles as this process has not
        been very active lately
        """
        self._delta_usr = 0
        self._delta_sys = 0
        self._delta_total = total_time - self._last_total
        if self._delta_total < 1:
            self._delta_total = 1
        self._last_total = total_time
        self._iteration = iteration

    def update(self, usr_time, sys_time, total_time, iteration):
        self._delta_usr = usr_time - self._last_usr
        self._delta_sys = sys_time - self._last_sys
        self._delta_total = total_time - self._last_total

        if self._delta_total < 1:
            self._delta_total = 1
        self._last_usr = usr_time
        self._last_sys = sys_time
        self._last_total = total_time
        self._last_update = self._iteration = iteration

        if self.get_usr_perc() + self.get_sys_perc() < 0.1:
            self._inactive_iters += 1
        else:
            self._inactive_iters = 0

    def absorb(self, state):
        """ Accumulate state data """
        self._delta_usr += state._delta_usr
        self._delta_sys += state._delta_sys

    def get_usr_perc(self):
        """ Get user time percentage for last iteration """
        return (100.0 * self._delta_usr / max(self._delta_usr + self._delta_sys,
            self._delta_total))

    def get_sys_perc(self):
        """ Get system time percentage for last iteration """
        return (100.0 * self._delta_sys / max(self._delta_usr + self._delta_sys,
            self._delta_total))

    def is_alive(self, iteration):
        return self._iteration == iteration

    def is_stale(self, iteration):
        return ((iteration - self._last_update) > (self._inactive_iters *
            self._inactive_iters))
