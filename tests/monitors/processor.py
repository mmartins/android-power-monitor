#!/usr/bin/env python

from monitors.processor import Processor
from monitors.cpu import CPU
from utils.sysfs import Node

import __builtin__  # for open
import mox          # for mock testing
import unittest

class TestProcessor(unittest):

    def setUp(self):
        self.m = mox.Mox()

    def teartDown(self):
        self.m.UnsetStubs()

    def test_get_num_cpus_zero_core(self):
        self.m.StubOutWithMock(__builtin__, "open")
        open(Processor.SYSFS_CPU_FILE).AndReturn('0')
        self.m.ReplayAll()

        self.assertEqual(Processor._get_num_cpus, 0)

        self.m.VerifyAll()

    def test_get_num_cpus_one_core(self):
        self.m.StubOutWithMock(__builtin__, "open")
        open(Processor.SYSFS_CPU_FILE).AndReturn('0')
        self.m.ReplayAll()

        self.assertEqual(Processor._get_num_cpus, 1)

        self.m.VerifyAll()

    def test_get_num_cpus_more_cores(self):
        self.m.StubOutWithMock(__builtin__, "open")
        open(Processor.SYSFS_CPU_FILE).AndReturn('0-2')
        self.m.ReplayAll()

        self.assertEqual(Processor._get_nums_cpus, 3)

        self.m.VerifyAll()

if __name__ == "__main__":
    unittest.main()
