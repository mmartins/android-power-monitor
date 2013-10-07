#!/usr/bin/env python

from __future__ import division

import os

class BatteryStats(object):

    _SYSFS_MASK = "/sys/class/power_supply/battery/{0}"

    @classmethod
    def get_voltage(cls):
        """Return battery voltage in volts"""
        filename = cls._SYSFS_MASK.format("voltage_now")
        # Transform source from mV to V
        factor = 1e-6

        if not os.path.exists(filename):
            filename = cls._SYSFS_MASK.format("batt_vol")
            # Transform source from uV to V
            factor = 1e-3

        try:
            with open(filename) as fp:
                voltage = int(fp.read().strip())
        except (IOError, ValueError):
            return 0

        return voltage * factor

    @classmethod
    def get_current(cls):
        """Return battery current in ampers"""
        filename = cls._SYSFS_MASK.format("current_now")
        # Transform source from uA to A
        factor = 1e-6

        try:
            with open(filename) as fp:
                current = int(fp.read().strip())
        except (IOError, ValueError):
            return 0

        return current * factor

    @classmethod
    def get_temperature(cls):
        """Return battery temperature in Celsius degrees"""
        filename = cls._SYSFS_MASK.format("temp")
        factor = 1e-1

        if not os.path.exists(filename):
            filename = cls._SYSFS_MASK.format("batt_temp")

        try:
            with open(filename) as fp:
                temperature = int(fp.read().strip())
        except (IOError, ValueError):
            return 0

        return temperature * factor

    @classmethod
    def get_capacity(cls):
        """Return remaining batt capacity in percentage"""
        filename = cls._SYSFS_MASK.format("capacity")
        # Transform source from percentage to 1
        factor = 0.01

        try:
            with open(filename) as fp:
                capacity = int(fp.read().strip())
        except (IOError, ValueError):
            return 0

        return capacity * factor

    @classmethod
    def get_full_capacity(cls):
        """Return battery at full capacity in V"""
        filename = cls._SYSFS_MASK.format("full_bat")

        # Transform source from mAh to 
        # 0.0036 = 60 * 60 * 1e-6
        factor = 0.0036

        try:
            with open(filename) as fp:
                full_capacity = int(fp.read()).strip()
        except (IOError, ValueError):
            return 0

        return full_capacity * factor

    @classmethod
    def get_charge(cls):
        filename = cls._SYSFS_MASK.format("charge_counter")
        # Transform from mAh to voltage
        # 0.0036 = 60 * 60 * 1e-6
        factor = 0.0036

        if not os.path.exists(filename):
            return cls.get_capacity() * cls.get_full_capacity()

        try:
            with open(filename) as fp:
                charge = int(fp.read().strip())
        except (IOError, ValueError):
            return 0

        return charge * factor
