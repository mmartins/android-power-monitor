#!/usr/bin/env python

from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.systeminfo import SystemInfo

import unittest

class TestIterationData(object):

    def setUp(self):
        self.data = IterationData()
        self.data.uid_usage[2] = UsageData(10)

    def test_add(self):
        idata = IterationData()
        idata.uid_usage[2] = UsageData(10)
        idata.uid_usage[3] = UsageData(15)

        idata = self.data.add(idata)
        self.assertEqual(self.data.uid_usage.keys(), [2])
        self.assertEqual(self.data.uid_usage.values(), [UsageData(20)])
        self.assertEqual(idata.uid_usage.keys(), [2, 3])
        self.assertEqual(idata.uid_usage.values(), [UsageData(20),
            UsageData(15)])

    def test_add_uid_usage(self):
        self.data.add_uid_usage(10, UsageData(15))
        self.assertEqual(self.data.uid_usage[10].usage, 15)

    def test_set_usage(self):
        self.data.set_usage(10)
        self.assertEqual(self.uid_usage[SystemInfo.AID_ALL], 10)

if __name__ == "__main__":
    unittest.main()
