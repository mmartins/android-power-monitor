#!/usr/bin/env python

from monitors.screen.screen import Screen
from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.foregrounddetector import ForegroundDetector
from utils.hardware import Hardware

class LCD(Screen):

    def __init__(self, devconstants):
        super(LCD, self).__init__(Hardware.LCD. devconstants)

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using display after one
        iteration. """
        result = IterationData()

        brightness = Screen.get_screen_brightness()

        if 0 <= brightness <= 255:
            self.logger.warn("Could not retrieve brightness information")
            return result

        with self._screenlock:
            screen = self.screen_on

        usage = LCDUsage(brightness, screen)
        result.set_sys_usage(usage)

        if screen:
            uid = ForegroundDetector.get_foreground_uid()
            result.set_uid_usage(uid, usage)

        return result

class LCDUsage(UsageData):

    __slots__ = ['brightness', 'screen_on']

    def __init__(self, brightness, screen_on):
        self.brightness = brightness
        self.screen_on = screen_on

    def log(self, out):
        res = "LCD-brightness {0}\nLCD-screen-on {1}\n".format(self.brightness,
                self.screen_on)
        out.write(res)
