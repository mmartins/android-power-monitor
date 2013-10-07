#!/usr/bin/env python

from monitors.audio import Audio
from monitors.cpu import CPU
from monitors.gps import GPS
from monitors.screen.oled import OLED
from monitors.sensors import Sensors
from monitors.threeg import ThreeG
from monitors.wifi import Wifi
from phones.base import Constants as BaseConstants, BaseDevice
from phones.base import BasePowerCalculator

from utils.hardware import Hardware

class Constants(BaseConstants):

    BATTERY_VOLTAGE = 3.7
    MODEL_NAME = "maguro"

    MAX_POWER = None
    LCD_BRIGHTNESS_PWR = None # Galaxy Nexus has no LCD display
    LCD_BACKLIGHT = None
    OLED_BASE_PWR = None
    OLED_RGB_PWRS = None
    OLED_MODULATION = None
    CPU_PWR_RATIOS = []
    CPU_FREQS = [350, 700, 920, 1200]
    AUDIO_PWR = None
    GPS_STATE_PWRS = []
    GPS_SLEEP_TIME = None
    WIFI_LOW_PWR = None
    WIFI_HIGH_PWR = None
    WIFI_LOWHIGH_PKTBOUND = None
    WIFI_HIGHLOW_PKTBOUND = None
    WIFI_LINK_RATIOS = []
    WIFI_LINK_SPEEDS = [1, 2, 5.5, 6, 9, 11, 12, 18, 24, 36, 48,
            54]
    THREEG_IFACE = "rmnet0"

    @classmethod
    def get_3g_idle_power(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_fach_power(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_dch_power(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_dchfach_time(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_fachidle_time(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_tx_queue(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_3g_rx_queue(cls, provider):
        raise NotImplementedError("Needs implementation")

    @classmethod
    def get_max_power(cls, monitor_name):
        raise NotImplementedError("Needs implementation")


class MaguroPhone(BaseDevice):

    hardware = {
            Hardware.CPU: CPU(Constants),
            Hardware.OLED: OLED(Constants),
            Hardware.WIFI: Wifi(Constants),
            Hardware.THREEG: None,
            Hardware.GPS: None,
            Hardware.AUDIO: None,
            Hardware.SENSORS: None
    }

    power_function = {
            Hardware.CPU: PowerCalculator.get_cpu_power,
            Hardware.OLED: PowerCalculator.get_oled_power,
            Hardware.WIFI: PowerCalculator.get_wifi_power,
            Hardware.THREEG: None,
            Hardware.GPS: None,
            Hardware.AUDIO: None,
            Hardware.SENSORS: None
    }


class PowerCalculator(BasePowerCalculator):

    # Galaxy Nexus has no LCd screen
    @classmethod
    def get_lcd_power(cls, lcd_data):
        raise NotImplementedError

    @classmethod
    def get_oled_power(cls, oled_data):
        # TODO
        return NotImplementedError("Needs implementation")
