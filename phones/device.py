#!/usr/bin/env python

class Device(object):

    hardware = {
            Hardware.CPU: None,
            Hardware.LCD: None,
            Hardware.OLED:None,
            Hardware.WIFI: None,
            Hardware.THREEG: None,
            Hardware.GPS: None,
            Hardware.AUDIO: None,
            Hardware.SENSORS: None,
    }

    power_function = {
            Hardware.CPU: None,
            Hardware.LCD: None,
            Hardware.OLED: None,
            Hardware.WIFI: None,
            Hardware.THREEG: None,
            Hardware.GPS: None,
            Hardware.AUDIO: None,
            Hardware.SENSORS: None,
    }

    # This is an abstract class that should be extended and incr
    def __init__(self):
        raise NotImplementedError
