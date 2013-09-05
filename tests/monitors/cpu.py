#!/usr/bin/env python

from monitors.cpu import CPU
from monitors.cpu import CPUState
from monitors.cpu import CPUUsage
from phones.device import DeviceConstants
from StringIO import StringIO

import __builtin__  # for open
import mox          # for mock testing
import unittest

class TestCPU(unittest.TestCase):

    PROCINFO_OUT = "Processor : ARMv7\nprocessor : 0\nBogoMIPS : 1194.24\nprocessor : 1 \n BogoMIPS:1194.24"

    def setUp(self):
        # Create instance of Mox
        self.m = mox.Mox()
        self.constants = self.m.CreateMock(DeviceConstants)
        self.constants.CPU_FREQS = [600, 800, 1200]
        self.cpu = CPU(self.constants, num=0)
        self.sysfs_filename = CPU.SYSFS_FREQ_FILE_MASK.format(self.cpu.num)

    def tearDown(self):
        self.m.UnsetStubs()

#    def test_calc_iteration(self):
#        """ Test instance state after call calc_iteration() """
#        pass

    def test_get_cpu_usage_fastreturn(self):
        """ Test get_cpu_usage when user and system usage percentage is
        minimal (returns at first if) """
        self.m.ReplayAll()

        usage = self.cpu._get_cpu_usage(0, 0, 600)
        self.assertEqual(usage._sys_perc, 0)
        self.assertEqual(usage._usr_perc, 0)
        self.assertEqual(usage._freq, 600)

        self.m.VerifyAll()

    def test_get_cpu_usage_low_utilization(self):
        """ Test CPU prediction with usage less than 70% """
        self.m.ReplayAll()

        usage = self.cpu._get_cpu_usage(20, 70, 600)
        self.assertAlmostEqual(usage._usr_perc, 15)
        self.assertAlmostEqual(usage._sys_perc, 52.5)
        self.assertEqual(usage._freq, 800)

        self.m.VerifyAll()

    def test_get_cpu_usage_high_utilization(self):
        """ Test CPU prediction with usage higher than 70% """
        self.m.ReplayAll()

        usage = self.cpu._get_cpu_usage(30, 70, 600)
        self.assertAlmostEqual(usage._usr_perc, 15)
        self.assertAlmostEqual(usage._sys_perc, 35)
        self.assertEqual(usage._freq, 1200)

        self.m.VerifyAll()

    def test_read_cpu_freq_sysfs(self):
        """ Test reading CPU frequency from mock sysfs
        """
        self.m.StubOutWithMock(__builtin__, 'open')
        open(self.sysfs_filename).AndReturn(StringIO("1200"))
        self.m.ReplayAll()

        cpu = CPU(self.constants, 0)
        usage = cpu._read_cpu_freq()

        self.assertEqual(usage, 1200)
        self.m.VerifyAll()

    def test_read_cpu_freq_cpuinfo(self):
        """ Test reading CPU frequency from mock /proc/cpuinfo
        """
        self.m.StubOutWithMock(__builtin__, 'open')

       # Force sysfs exception so that frequency is read from /proc/cpuinfo
        open(self.sysfs_filename, 'r').AndRaises(IOError)
        open(CPU.CPU_FREQ_FILE, 'r').AndReturn(StringIO(self.PROCINFO_OUT))
        self.m.ReplayAll()

        self.assertEqual(self.cpu._read_cpu_freq(), 1200)

        self.m.VerifyAll()

    def test_read_cpu_freq_fail(self):
        """ Test reading CPU frequency failure """
        self.m.StubOutWithMock(__builtin__, 'open')

       # Force sysfs exception so that frequency is read from /proc/cpuinfo
        open(self.sysfs_filename, 'r').AndRaises(IOError)
        open('/proc/cpuinfo', 'r').AndRaises(IOError)
        self.m.ReplayAll()

        self.assertEqual(self.cpu._read_cpu_freq(), -1)

        self.m.VerifyAll()

class TestCPUUsage(unittest.TestCase):

    TEST_SYS_PERC = 30
    TEST_USR_PERC = 70
    TEST_FREQ = 500

    def setUp(self):
        self.usage = CPUUsage(self.TEST_SYS_PERC, self.TEST_USR_PERC,
                self.TEST_FREQ)

    def test_init(self):
        self.assertEqual(self.usage._sys_perc, self.TEST_SYS_PERC)
        self.assertEqual(self.usage._usr_perc, self.TEST_USR_PERC)
        self.assertEqual(self.usage._freq, self.TEST_FREQ)


class TestCPUCase(unittest.TestCase):

    TEST_UID = 1000
    TEST_SUM_USR = 7
    TEST_SUM_SYS = 3
    TEST_USR_TIME = 30
    TEST_SYS_TIME = 40
    TEST_ITERATION1 = 0
    TEST_ITERATION2 = 2
    TEST_TOTAL_TIME = 10000

    def setUp(self):
        self._state = CPUState(self.TEST_UID)

    def test_init(self):
        self.assertEqual(self._state.uid, self.TEST_UID)

    def test_is_initialized(self):
        self.assertEqual(self._state.is_initialized(), False)

    def test_skip_update(self):
        """ Test instance state after call to skip_update() """
        self._state.skip_update(self.TEST_ITERATION1, self.TEST_TOTAL_TIME)
        self.assertEqual(self._state._delta_total, self.TEST_TOTAL_TIME)
        self.assertEqual(self._state._last_total, self.TEST_TOTAL_TIME)
        self.assertEqual(self._state._iteration, self.TEST_ITERATION1)

    def test_update(self):
        """ Test instance state after call to update() """
        self._state.update(self.TEST_USR_TIME, self.TEST_SYS_TIME,
                self.TEST_TOTAL_TIME, self.TEST_ITERATION2)
        self.assertEqual(self._state._delta_usr, self.TEST_USR_TIME)
        self.assertEqual(self._state._delta_sys, self.TEST_SYS_TIME)
        self.assertEqual(self._state._delta_total, self.TEST_TOTAL_TIME)
        self.assertEqual(self._state._last_update, self.TEST_ITERATION2)
        self.assertEqual(self._state._inactive_iters, 0)

    def test_absorb(self):
        """ Test instance state after call to absorb() """
        state2 = CPUState(self.TEST_UID)
        state2.update(self.TEST_USR_TIME, self.TEST_SYS_TIME,
                self.TEST_TOTAL_TIME, self.TEST_ITERATION2)

        self._state.absorb(state2)
        self.assertEqual(self._state._delta_usr, self.TEST_USR_TIME)
        self.assertEqual(self._state._delta_sys, self.TEST_SYS_TIME)

    def test_get_usr_perc(self):
        self._state._delta_usr = self.TEST_SUM_USR
        self._state._delta_sys = self.TEST_SUM_SYS
        self.assertAlmostEqual(self._state.get_usr_perc(), 70.0)

    def test_get_sys_perc(self):
        self._state._delta_usr = self.TEST_SUM_USR
        self._state._delta_sys = self.TEST_SUM_SYS
        self.assertAlmostEqual(self._state.get_sys_perc(), 30.0)

    def test_is_alive(self):
        self.assertTrue(self._state.is_alive(self.TEST_ITERATION1))

    def test_is_alive_fail(self):
        self.assertFalse(self._state.is_alive(self.TEST_ITERATION2))

    def test_is_stale(self):
        self.assertTrue(self._state.is_stale(self.TEST_ITERATION2))

    def test_is_stale_fail(self):
        self.assertFalse(self._state.is_stale(self.TEST_ITERATION1))


if __name__ == "__main__":
    unittest.main()
