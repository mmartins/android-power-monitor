#!/usr/bin/env python

try:
    from libs.display import DisplayAccess
except ImportError:
    from utils.androidhelpers.display import DisplayAccess

from libs.broadcast import BroadcastReceiver
from monitors.devicemonitor import DeviceMonitor

import threading


class Screen(DeviceMonitor):
    Display = DisplayAccess()

    BACKLIGHT_BRIGHTNESS_FILES = [
        "/sys/class/leds/lcd-backlight/brightness",
        "/sys/devices/virtual/leds/lcd-backlight/brightness",
        "/sys/devices/platform/trout-backlight.0/leds/lcd-backlight/brightness"
    ]

    def __init__(self, monitor_name, devconstants):
        super(Screen, self).__init__(monitor_name, devconstants)
        self.br = BroadcastReceiver(self.__on_receive, action=['screen_on',
                                                               'screen_off'])
        self.width = self.Display.get_width()
        self.height = self.Display.get_height()

        self.screen_on = True
        self.has_uid_information = True
        self._screenlock = threading.Lock()
        # Start display status monitor
        self.br.start()

    def _on_exit(self):
        super(Screen, self)._on_exit()
        self.br.stop()

    def __on_receive(self, context, intent):
        """ Callback method for display status monitor. """
        with self._screenlock:
            if intent.getAction() == 'screen_on':
                self.screen_on = True
            elif intent.getAction() == 'screen_off':
                self.screen_on = False

    @classmethod
    def get_display_brightness(cls):
        for filename in cls.BACKLIGHT_BRIGHTNESS_FILES:
            try:
                with open(filename, 'r') as fp:
                    brightness = int(fp.read().strip())
                    return brightness
            except (IOError, ValueError):
                pass

        return DisplayAccess.get_brightness()

    def calc_iteration(self, iter_num):
        pass
