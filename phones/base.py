#!/usr/bin/env python

from __future__ import division

try:
    from libs.sensors import SensorsAccess
except ImportError:
    from utils.androidhelpers.sensors import SensorsAccess

from monitors.audio import Audio
from monitors.cpu import CPU
from monitors.gps import GPS
from monitors.sensors import Sensors
from monitors.screen.lcd import LCD
from monitors.threeg import ThreeG
from monitors.wifi import Wifi
from phones.device import Device
from utils.hardware import Hardware


class Constants(object):
    PROVIDER_ATT = "AT&T"
    PROVIDER_TMOBILE = "T - Mobile"

    BATTERY_VOLTAGE = 0
    MODEL_NAME = "base"
    MAX_POWER = 0

    LCD_BRIGHTNESS_PWR = 0
    LCD_BACKLIGHT = 0
    OLED_BASE_PWR = 0
    OLED_RGB_PWRS = 0
    OLED_MODULATION = 0
    CPU_PWR_RATIOS = []
    CPU_FREQS = []
    AUDIO_PWR = 0
    GPS_STATE_PWRS = []
    GPS_SLEEP_TIME = 0
    WIFI_LOW_PWR = 0
    WIFI_HIGH_PWR = 0
    WIFI_LOWHIGH_PKTBOUND = 0
    WIFI_HIGHLOW_PKTBOUND = 0
    WIFI_LINK_RATIOS = []
    WIFI_LINK_SPEEDS = []

    @classmethod
    def _get_sensor_pwr_ratios(cls):
        powers = {}

        for name, power in SensorsAccess.get_sensors():
            powers[name] = power * Constants.BATTERY_VOLTAGE

        return powers

    SENSOR_PWR_RATIOS = _get_sensor_pwr_ratios()

    # The following methods are too specific and need to be implemented
    # according to the device in question

    @classmethod
    def get_3g_idle_power(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_3g_fach_power(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_3g_dch_power(cls, provider):
        raise NotImplementedError

    @classmethod
    def get_3g_dchfach_time(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_3g_fachidle_time(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_3g_tx_queue(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_3g_rx_queue(cls, provider):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")

    @classmethod
    def get_max_power(cls, monitor_name):
        raise NotImplementedError(
            "Constants shouldn't be instantiated directly")


class BaseDevice(Device):
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
        Hardware.CPU: BasePowerCalculator.get_cpu_power,
        Hardware.LCD: BasePowerCalculator.get_lcd_power,
        Hardware.WIFI: BasePowerCalculator.get_wifi_power,
        Hardware.THREEG: BasePowerCalculator.get_3g_power,
        Hardware.GPS: BasePowerCalculator.get_gps_power,
        Hardware.AUDIO: BasePowerCalculator.get_audio_power,
        Hardware.SENSORS: BasePowerCalculator.get_sensor_power,
    }


class BasePowerCalculator(object):
    @classmethod
    def get_lcd_power(cls, lcd_data):
        raise NotImplementedError

    @classmethod
    def get_oled_power(cls, oled_data):
        raise NotImplementedError

    @classmethod
    def get_cpu_power(cls, cpu_data):
        """ Find the two closest CPU frequencies and linearly interpolate the
        power ratio for current freq
        """
        if not cpu_data or len(Constants.CPU_PWR_RATIOS) == 0:
            return 0
        elif len(Constants.CPU_PWR_RATIOS) == 1:
            ratio = Constants.CPU_PWR_RATIOS[0]
        else:
            freq = cpu_data.freq
            if cpu_data.freq < Constants.CPU_PWR_RATIOS[0]:
                freq = Constants.CPU_FREQS[0]
            if cpu_data.freq > Constants.CPU_PWR_RATIOS[-1]:
                freq = Constants.CPU_FREQS[-1]

            i = cls._upper_bound(freq, Constants.CPU_FREQS)

            ratio = (Constants.CPU_PWR_RATIOS[i - 1] +
                     (Constants.CPU_PWR_RATIOS[i] - Constants.CPU_PWR_RATIOS[
                         i - 1]) /
                     (Constants.CPU_FREQS[i] - Constants.CPU_FREQS[i - 1]) *
                     (freq - Constants.CPU_FREQS[i - 1]))

        return max(0, ratio * (cpu_data.usr_perc + cpu_data.sys_perc))

    @classmethod
    def get_audio_power(cls, audio_data):
        return Constants.AUDIO_PWR if audio_data.music else 0

    @classmethod
    def get_gps_power(cls, gps_data):
        res = sum(time * power for time, power in zip(gps_data.state_times,
                                                      Constants.GPS_STATE_PWRS))
        return res

    @classmethod
    def get_wifi_power(cls, wifi_data):
        ratio = 0

        if not wifi_data:
            return 0
        if wifi_data.pwr_state == Wifi.POWER_STATE_LOW:
            return Constants.WIFI_LOW_PWR
        if wifi_data.pwr_state == Wifi.POWER_STATE_HIGH:
            if len(Constants.WIFI_LINK_SPEEDS) == 1:
                # If there is only one set speed we have to use its ratio as we
                # have nothing else to use
                ratio = Constants.WIFI_LINK_RATIOS[0]
            else:
                # Find two nearest speed/ratio pairs and linearly interpolate
                # the ratio for this link speed

                i = cls._upper_bound(wifi_data.speed, Constants
                .WIFI_LINK_SPEEDS)
                if i == 0:
                    i += 1
                elif i == len(Constants.WIFI_LINK_SPEEDS):
                    i -= 1

                ratio = (Constants.WIFI_LINK_SPEEDS[i - 1] +
                         (Constants.WIFI_LINK_SPEEDS[i] -
                          Constants.WIFI_LINK_SPEEDS[i - 1]) *
                         (wifi_data.speed - Constants.WIFI_LINK_SPEEDS[i - 1]))

        return max(0, Constants.WIFI_HIGH_PWR + ratio * wifi_data.tx_rate)

    @classmethod
    def get_3g_power(cls, threeg_data):
        if not threeg_data:
            return 0
        if threeg_data.pwr_state == ThreeG.POWER_STATE_IDLE:
            return Constants.get_3g_idle_power(threeg_data.provider)
        if threeg_data.pwr_state == ThreeG.POWER_STATE_FACH:
            return Constants.get_3g_fach_power(threeg_data.provider)
        if threeg_data.pwr_state == ThreeG.POWER_STATE_DCH:
            return Constants.get_3g_dch_power(threeg_data.provider)

        return 0

    @classmethod
    def get_sensor_power(cls, sensor_data):
        if not sensor_data:
            return 0

        res = sum(time * power for time, power in
                  zip(sensor_data.on_times.values,
                      Constants.SENSOR_PWR_RATIOS.values))

    @classmethod
    def _upper_bound(cls, value, list_):
        lo = 0
        hi = len(list_)

        while lo < hi:
            mid = lo + (hi - lo) // 2
            if list_[mid] <= value:
                lo = mid + 1
            else:
                hi = mid

        return lo

