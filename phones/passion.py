#!/usr/bin/env python

try:
    from libs.display import DisplayAccces
except ImportError:
    from utils.androidhelpers.display import DisplayAccess

from monitors.device import Device
from monitors.screen.oled import OLEDData
from phones.dream import PowerCalculator as DreamCalculator
from phones.dream import Constants as DreamConstants
from utils.hardware import Hardware

Display = DisplayAccess()

class PassionPhone(Device):
    hardware = {
            Hardware.CPU: CPU(DreamConstants),
            Hardware.LCD: LCD(DreamConstants),
            Hardware.WIFI: Wifi(DreamConstants),
            Hardware.THREEG: ThreeG(DreamConstants),
            Hardware.GPS: GPS(DreamConstants),
            Hardawre.AUDIO: Audio(DreamConstants),
            Hardware.SENSORS: Sensors(DreamConstants),
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


class PowerCalculator(DreamCalculator):
    """ HTC Passion inherits most of its coefficients from HTC Dream, as most
    of the hardware is the same
    """

    @classmethod
    def get_oled_power(cls, oled_data):
        if not oled_data.screen_on:
            return 0

        if oled_data.pix_power == -1:
            # No pixel power available
            return (Constants.OLED_BASE_PWR + Constants.LCD_BRIGHTNESS_PWR *
                    oled_data.brightness)
        else:
            return (Constants.OLED_BASE_PWR + oled_data.pixPower *
                    oled_data.brightness)

class Constants(DreamConstants):

    MODEL_NAME = "passion"

    MAX_POWER = 2800
    SCREEN_HEIGHT = Display.get_height()
    SCREEN_WIDTH = Display.get_width()
    LCD_BRIGHTNESS_PWR = 1.2217
    LCD_BACKLIGHT = None    # HTC Passion has no LCD display
    OLED_BASE_PWR = 365     # constant monitor of the model
    OLED_RGB_PWRS = [3.0647e-006, 4.4799e-006, 6.4045e-006]
    OLED_MODULATION = 1.758e-006
    CPU_PWR_RATIOS = [1.1273, 1.5907, 1.8736, 2.1745, 2.6031,
            2.9612, 3.1373, 3.4513, 3.9073, 4.1959, 4.6492, 5.4818]
    CPU_FREQS = [245, 384, 460, 499, 576, 614, 653, 691, 768, 806,
            845, 998]
    AUDIO_PWR = 106.81
    GPS_STATE_PWRS = [0, 17.5, 268.94]
    GPS_SLEEP_TIME = 6
    WIFI_LOW_PWR = 34.37
    WIFI_HIGH_PWR = 404.46
    WIFI_LOWHIGH_PKTBOUND = 15
    WIFI_HIGHLOW_PKTBOUND = 8
    WIFI_LINK_RATIOS = [47.122645, 46.354821, 43.667437,
            43.283525, 40.980053, 39.44422, 38.676581, 34.069637,
            29.462693, 20.248805, 11.034917, 6.427122]
    THREEG_IFACE = "rmnet0"
    WIFI_LINK_SPEEDS = [1, 2, 5.5, 6, 9, 11, 12, 18, 24, 36, 48,
            54]

    @classmethod
    def get_3g_idle_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 10
        # Return the worst case for unknown operators
        return 10

    @classmethod
    def get_3g_fach_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 405.81
        # Return the worst case for unknown operators
        return 405.81

    @classmethod
    def get_3g_dch_power(cls, provider):
        if provider == cls.PROVIDER_TMOBILE:
            return 902.03
        # Return the worst case for unknown operators
        return 902.03

    @classmethod
    def get_max_power(cls, monitor_name):
        if monitor_name == Hardware.OLED:
            return (cls.OLED_BASE_PWR + 255 * cls.SCREEN_WIDTH *
                    cls.SCREEN_HEIGHT * (cls.OLED_RGB_PWRS[0] +
                        cls.OLED_RGB_PWRS[1] + cls.OLED_RGB_PWRS[2] -
                        cls.OLED_MODULATION))

        return super(Constants, cls).get_max_power(monitor_name)
