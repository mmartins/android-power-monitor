#!/usr/bin/env python

from services.usagedata import UsageData

import unittest


class TestUsageData(unittest):
    def setUp(self):
        self.data = UsageData(10)

    def test_add(self):
        self.data.add(10)
        self.assertEqual(self.data.usage, 20)

    def test_log_raise(self):
        self.assertRaises(self.data.log(None), NotImplementedError)

if __name__ == "__main__":
    unittest.main()
