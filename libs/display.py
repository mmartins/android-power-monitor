#!/usr/bin/env python

from jnius import autoclass

DisplayMetrics = autoclass('android.utils.DisplayMetrics')
System = autoclass('android.provider.Settings$System')
PythonActivity = autoclass('org.renpy.android.PythonActivity')


class DisplayAccess(object):
    def __init__(self):
        self.metrics = DisplayMetrics()

    def get_dpi(self):
        return self.metrics.densityDpi

    def get_height(self):
        return self.metrics.heightPixels

    def get_width(self):
        return self.metrics.widthPixels

    @staticmethod
    def get_brightness():
        return System.getInt(PythonActivity.mActivity.getContentResolver(),
                             System.SCREEN_BRIGHTNESS)
