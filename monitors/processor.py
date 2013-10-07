#!/usr/bin/env python

from monitors.cpu import CPU
from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from utils.hardware import Hardware

class Processor(DeviceMonitor):

    SYSFS_CPU_FILE = "/sys/devices/system/cpu/present"

    def __init__(self, devconstants):
        super(Processor, self).__init__(Hardware.CPU, devconstants)

        self.num_cpus = self._get_num_cpus()
        self.cpus = [CPU(i, devconstants) for i in xrange(self.num_cpus)]
        self.has_uid_information = True

    @classmethod
    def _get_num_cpus(cls):
        """ Return number of CPU cores from sysfs. Format should be "0-N" or
        "0" if read successfully. Return zero cores on failures """

        with open(cls.SYSFS_CPU_FILE) as fp:
            data = fp.read().strip()

        minmax = data.split("-")

        if len(minmax) > 0 and minmax[-1].isdigit():
            return int(minmax[-1] + 1)

        return 0

    def calc_iteration(self, iter_num):
        total = IterationData()
        # TODO: Rewrite below using FP
        for cpu in self.cpus:
            total.add(cpu.calc_iteration(iter_num))
        return total
