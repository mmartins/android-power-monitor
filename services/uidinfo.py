#!/usr/bin/env python

class UidInfo(object):
    def __init__(self, uid, power, energy, runtime):
        self.uid = uid
        self.power = power
        self.energy = energy
        self.runtime = runtime

        self.key = 0
        self.percentage = 0
        self.unit = ""

    # Implement 6 comparison operators instead of __cmp__, as the latter has
    # been removed from Python 3
    def __eq__(self, other):
        return self.key == other.key

    def __ne__(self, other):
        return self.key != other.key

    def __gt__(self, other):
        return self.key > other.key

    def __lt__(self, other):
        return self.key < other.key

    def __ge__(self, other):
        return self.key >= other.key

    def __le__(self, other):
        return self.key <= other.key
