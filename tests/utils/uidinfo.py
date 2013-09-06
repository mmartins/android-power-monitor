#!/usr/bin/env python

from services.uidinfo import UidInfo

import unittest

class TestUidInfo (unittest.TestCase):

    def setUp(self):
        self.info1 = UidInfo(1, 0, 0, 0)
        self.info2 = UidInfo(2, 0, 0, 0)
        self.info1.key = 1
        self.info2.key = 2

    def test_operator_success(self):
        self.assertTrue(self.info1 == self.info1)
        self.assertTrue(self.info1 >= self.info1)
        self.assertTrue(self.info1 <= self.info1)
        self.assertTrue(self.info1 != self.info2)
        self.assertTrue(self.info1  < self.info2)
        self.assertTrue(self.info1 <= self.info2)
        self.assertTrue(self.info2  > self.info1)
        self.assertTrue(self.info2 >= self.info1)

    def test_operator_failure(self):
        self.assertFalse(self.info1 != self.info1)
        self.assertFalse(self.info1 == self.info2)
        self.assertFalse(self.info1  > self.info2)
        self.assertFalse(self.info1 >= self.info2)
        self.assertFalse(self.info2  < self.info1)
        self.assertFalse(self.info2 <= self.info1)

if __name__ == "__main__":
    unittest.main()
