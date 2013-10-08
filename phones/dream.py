#!/usr/bin/env python

from monitors.audio import Audio
from monitors.cpu import CPU
from monitors.gps import GPS
from monitors.screen.lcd import LCD
from monitors.sensors import Sensors
from monitors.threeg import ThreeG
from monitors.wifi import Wifi
from phones.base import Constants as BaseConstants, BaseDevice
from phones.base import BasePowerCalculator
from utils.hardware import Hardware


class Constants(BaseConstants):
    BATTERY_VOLTAGE = 3.7
    MODEL_NAME = "dream"

    MAX_POWER = 2800
    LCD_BRIGHTNESS_PWR = 2.40276
    LCD_BACKLIGHT = 121.4606 + 166.5
    OLED_BASE_PWR = None     # HTC Dream has no OLED display
    OLED_RGB_PWRS = None
    OLED_MODULATION = None
    CPU_PWR_RATIOS = [3.4169, 4.3388]
    CPU_FREQS = [245, 384]
    AUDIO_PWR = 384.62
    GPS_STATE_PWRS = [0, 173.55, 429.55]
    GPS_SLEEP_TIME = 6
    WIFI_LOW_PWR = 38.554
    WIFI_HIGH_PWR = 720
    WIFI_LOWHIGH_PKTBOUND = 15
    WIFI_HIGHLOW_PKTBOUND = 8
    WIFI_LINK_RATIOS = [47.122645, 46.354821, 43.667437,
                        43.283525, 40.980053, 39.44422, 38.676581, 34.069637,
                        29.462693, 20.248805, 11.034917, 6.427122]
    WIFI_LINK_SPEEDS = [1, 2, 5.5, 6, 9, 11, 12, 18, 24, 36, 48,
                        54]
    THREEG_IFACE = "rmnet0"

    @classmethod
    def get_3g_idle_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 10
        # Return the worst case for unknown operators
        return 10

    @classmethod
    def get_3g_fach_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 401
        # Return the worst case for unknown operators
        return 401

    @classmethod
    def get_3g_dch_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 570
            # Return the worst case for unknown operators
        return 570

    @classmethod
    def get_3g_dchfach_time(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 6
        if provider == cls.PROVIDER_ATT:
            return 5

        # Not sure if this refers Sprinter and Verizon?
        return 4

    @classmethod
    def get_3g_fachidle_time(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 4
        if provider == cls.PROVIDER_ATT:
            return 12

        # Not sure if this refer to Sprinter and Verizon?
        return 6

    @classmethod
    def get_3g_tx_queue(cls, provider):
        return 151

    @classmethod
    def get_3g_rx_queue(cls, provider):
        return 119

    @classmethod
    def get_max_power(cls, monitor_name):
        if monitor_name == Hardware.LCD:
            return cls.LCD_BACKLIGHT + cls.LCD_BRIGHTNESS_PWR * 255
        if monitor_name == Hardware.CPU:
            return cls.CPU_PWR_RATIOS[-1] * 100
        if monitor_name == Hardware.AUDIO:
            return cls.AUDIO_PWR
        if monitor_name == Hardware.GPS:
            return cls.GPS_STATE_PWRS[-1]
        if monitor_name == Hardware.WIFI:
            # TODO: Get a better estimation here
            return 800
        if monitor_name == Hardware.THREEG:
            return cls.get_3g_dch_power("")
        if monitor_name == Hardware.SENSORS:
            return sum(cls.SENSOR_PWR_RATIOS.values)

        # Where does this value come from?
        return 900


class DreamPhone(BaseDevice):
    hardware = {
        Hardware.CPU: CPU(Constants),
        Hardware.LCD: LCD(Constants),
        Hardware.WIFI: Wifi(Constants),
        Hardware.THREEG: ThreeG(Constants),
        Hardware.GPS: GPS(Constants),
        Hardware.AUDIO: Audio(Constants),
        Hardware.SENSORS: Sensors(Constants),
    }

    power_function = {
        Hardware.CPU: PowerCalculator.get_cpu_power,
        Hardware.LCD: PowerCalculator.get_lcd_power,
        Hardware.WIFI: PowerCalculator.get_wifi_power,
        Hardware.THREEG: PowerCalculator.get_3g_power,
        Hardware.GPS: PowerCalculator.get_gps_power,
        Hardware.AUDIO: PowerCalculator.get_audio_power,
        Hardware.SENSORS: PowerCalculator.get_sensor_power,
    }


class PowerCalculator(BasePowerCalculator):
    @classmethod
    def get_lcd_power(cls, lcd_data):
        if lcd_data.screen_on:
            return (Constants.LCD_BRIGHTNESS_PWR * lcd_data.brightness +
                    Constants.LCD_BACKLIGHT)
        return 0

    # HTC Dream has no OLED screen
    @classmethod
    def get_oled_power(cls, oled_data):
        raise NotImplementedError
