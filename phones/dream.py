#!/usr/bin/env python

try:
    from libs.sensors import SensorsAccess
except ImportError:
    from utils.androidhelpers.sensors import SensorsAccess

from monitors.audio import AudioData
from monitors.gps import GPSData
from monitors.sensors import Sensors
from monitors.screen.lcd import LCDData
from monitors.screen.oled import OLEDData
from monitors.threeg import ThreeG, ThreeGData
from monitors.wifi import Wifi, WifiData
from phones.device import Device
from phones.device import DeviceConstants

from utils.hardware import Hardware

class DreamPhone(Device):

    hardware = {
            Hardware.CPU: CPU(Constants),
            Hardware.LCD: LCD(Constants),
            Hardware.WIFI: Wifi(Constants),
            Hardware.THREEG: ThreeG(Constants),
            Hardware.GPS: GPS(Constants),
            Hardawre.AUDIO: Audio(Constants),
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


class PowerCalculator(object):

    @classmethod
    def get_lcd_power(cls, lcd_data):
        if lcd_data.screen_on:
            return (Constants.LCD_BRIGHTNESS * lcd_data.brightness +
                    Constants.LCD_BACKLIGHT)
        return 0

    @classmethod
    def get_oled_power(cls, oled_data):
        raise NotImplementedError

    @classmethod
    def get_cpu_power(cls, cpu_data):
        """ Find the two closest CPU frequencies and linearly interpolate the
        power ratio for current freq
        """
        if len(Constants.CPU_PWR_RATIOS) == 1:
            ratio = Constants.CPU_PWR_RATIOS[0]
        else:
            freq = cpu_data.freq
            if cpu_data.freq < Constants.CPU_PWR_RATIOS[0]:
                freq = Constants.CPU_FREQS[0]
            if cpu_data.freq > Constants.CPU_PWR_RATIOS[-1]:
                freq = Constants.CPU_FREQS[-1]

            i = _upper_bound(freq, Constants.CPU_FREQS)

            ratio = (Constants.CPU_PWR_RATIOS[i-1] +
                (Constants.CPU_PWR_RATIOS[i] - Constants.CPU_PWR_RATIOS[i-1]) /
                (Constants.CPU_FREQS[i] - Constants.CPU_FREQS[i-1]) *
                (freq - Constants.CPU_FREQS[i-1]))

        return max(0, ratio * (cpu_data.usr_perc + cpu_data.sys_perc))

    @classmethod
    def get_audio_power(cls, audio_data):
        return (Constants.AUDIO_PWR if audio_data.music else 0)

    @classmethod
    def get_gps_power(cls, gps_data):
        res = sum(time * power for time, power in zip(gps_data.state_times,
                Constants.GPS_PWR_RATIOS))
        return res

    @classmethod
    def get_wifi_power(cls, wifi_data):
        ratio = 0

        if not wifi_data:
            return 0
        if wifi_data.pwr_state == Wifi.POWER_STATE_LOW:
            return Constants.WIFI_LOW_PWR
        if wifi_data.pwr_state == Wifi.POWER_STATE_HIGH:
            if len(Constants.WIFI_SPEEDS) == 1:
                # If there is only one set speed we have to use its ratio as we
                # have nothing else to use
                ratio = WIFI_PWR_RATIOS[0]
            else:
                # Find two nearest speed/ratio pairs and linearly interpolate
                # the ratio for this link speed

                i = _upper_bound(wifi_data.speed, Constants.WIFI_SPEEDS)
                if i == 0:
                    i += 1
                elif i == len(Constants.WIFI_SPEEDS):
                    i -= 1

                ratio = (Constants.WIFI_SPEEDS[i-1] +
                        (Constants.WIFI_SPEEDS[i] - Constants.WIFI_SPEEDS[i-1])
                        * (wifi_data.speed - Constants.WIFI_SPEEDS[i-1]))

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
        res = sum(time * power for time, power in
                zip(sensor_data.on_times.values,
                Constants.SENSOR_PWR_RATIOS.values))

def _get_sensor_power_ratios():
    powers = {}

    for name, power in SensorsAccess.get_sensor():
        powers[name] = power * Constants.BATTERY_VOLTAGE

    return powers

def _upper_bound(value, list_):
    lo = 0
    hi = len(list_)

    while (lo < hi):
        mid = lo + (hi - lo) // 2
        if list_[mid] <= value:
            lo = mid + 1
        else:
            hi = mid

    return lo

class Constants(DeviceConstants):

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
    SENSOR_PWR_RATIOS = _get_sensor_power_ratios()

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
            5

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
            return cls.LCD_BACKLIGHT + cls.LCD_BRIGHTNESS * 255
        if monitor_name == Hardware.CPU:
            return cls.CPU_PWR_RATIOS[-1] * 100
        if monitor_name == Hardware.AUDIO:
            return cls.AUDIO_POWER
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
