#!/usr/bin/env python

from __future__ import division

from monitors.devicemonitor import DeviceMonitor
from utils.batterystats import BatteryStats
from utils.counter import Counter
from utils.hardware import Hardware
from utils.systeminfo import SystemInfo
from utils.powerbuffer import PowerBuffer

import math
import threading
import time

class PowerEstimator(threading.Thread):

    POLYNOMIAL_WEIGHT = 0.2
    ITERATION_INTERVAL = 1000  # 1 second

    def __init__(self, phone):
        super(PowerEstimator, self).__init__(target=self._run)
        self.daemon = True

        self._avg_power = 0.0

        # Used to interrupt thread
        self._running = threading.Event()
        # Running apps: { uid : app_name }
        self._running_apps = {}

        self._phone = phone

        self._history = dict(self._phone.hardware.keys(), None)
        self._oled_pwr_history = {}

        self._log = open("powerlog.log", "w")

        self._appslock = threading.Lock()
        self._iterlock = threading.Lock()
        self._loglock = threading.Lock()

        # self.start()

    def __del__(self):
        super(PowerEstimator, self).__del__()
        self._log.close()

    def _run(self):
        '''Loop that keeps updating the power profile'''

        start_time = round(time.time())

        for hw in self._phone.hardware.values():
            hw.init(start_time, self.ITERATION_INTERVAL)
            hw.start()

        self._running.set()
        iter_num = 0

        while self.is_running():
            now = round(time.time())

            # Compute the next iteration that we can make the ending of. We
            # wait for the end of the iteration so that the monitors have a
            # chance to collect data


            iter_num = max(iter_num, (now - start_time) //
                    self.ITERATION_INTERVAL)

            # sleep until the next iteration completes
            time.sleep(start_time + iter_num *
                    self.ITERATION_INTERVAL - now)

            total_power = 0

            hw_data = {}
            for name, hw in self._phone.hardware.iteritems():
                data = hw.get_data(iter_num-1)

                if data is None:
                    continue

                hw_data[name] = data

                for uid, usage in data.uid_usage.iteritems():

                    power = self._phone.power_function[name](usage)
                    usage = power
                    self._history[name].add(uid, iter_num, power)
                    if uid == SystemInfo.AID_ALL:
                        total_power += power

                    # Update list of running apps
                    with self._appslock:
                        self._running_apps.setdefault(uid,
                                SystemInfo.get_app_name(uid))

                    if name == "OLED" and data.pix_pwr >= 0:
                        self._oled_history.add(uid, iter_num, int(1000 *
                            data.pix_pwr))

                self._update_avg_power()
                self._log_battery()
                self._log_sys_settings()
                self._log_power()

        # Wait for all hardware monitors to finish
        for hw in self._phone.hardware.values():
            hw.stop()
            hw.join()

    def stop(self):
        self._running.clear()

    def is_running(self):
        return self._running.isSet()

    def _log_battery(self):
        out = "batt-charge: {0}\nbatt-temp: {1}\nbatt-voltage: {3}\nbatt-current: {4}\n".format(
                BatteryStats.get_charge(),
                BatteryStats.get_temperature(),
                BatteryStats.get_voltage(),
                BatteryStats.get_current())
        with self._loglock:
            self._log.write("== BATTERY INFO START ==\n")
            self._log.write(out)
            self._log.write("== BATTERY INFO END ==\n")

    def _log_sys_setting(self):
        out = ""

        with self._loglock:
            self._log.write("== SYSTEM SETTINGS START ==\n")
            self._log.write(out)
            self._log.write("== SYSTEM SETTINGS END ==\n")

    def _log_power(self):
        out = ""
        with self._loglock:
            self._log.write("== POWER START ==\n")
            self._log.write(out)
            self._log.write("== POWER END ==\n")

    def _update_avg_power(self):
        hw_history = self._get_hw_history(5 * 60, -1, SystemInfo.AID_ALL, -1)

        avg = 0
        weighted_pwr = 0
        cnt = 0

        INV_POLY_WEIGHT = 1.0 - self.POLYNOMIAL_WEIGHT
        for power in hw_history.values():
            # Skip zero-powers to save cycles
            if power != 0:
                cnt += 1
                weighted_pwr *= INV_POLY_WEIGHT
                weighted_pwr += (self.POLYNOMIAL_WEIGHT * power /
                        1000.0)

        if cnt > 0:
            avg = weighted_pwr / (1.0 - math.pow(INV_POLY_WEIGHT, cnt))
            # Return power in mW
            avg *= 1000

        self._avg_power = avg
        return avg

    def get_hardware_names(self):
        return self._phone.hardware.keys()


    def get_hardware_max_powers(self):
        max_powers = {k: constants.get_max_power(k) for k in
            self._pwr_history.keys()}
        return max_powers

    def get_hw_uid_mask(self):
        '''Return a mask indicating which hardware components do not provide
        UID information'''
        mask = 0
        for i, hw in self._phone.hardware.values().enumerate():
            if not hw.has_uid_information:
                mask |= 1 << i

        return mask

    def get_hardware_history(self, number, uid, iter_num):
        #if iter_num == -1:
            #TODO: Finish this

        if name == "ALL":
            result = dict(self._pwr_history.keys(), 0)
            for k, pwrbuf in self._pwr_history.iteritems():
                powers[k] = pwrbuf.get_powers_up_to_timestamp(uid,
                    iter_num, number)

                for i, value in powers.enumerate():
                    result[k] += value

            return result

        if name not in self._phone.hardware.keys():
            return None

        return self._pwr_history[name].get_power_up_to_timestamp(uid, iter_num,
            number)

    def get_uid_hw_powers(self, uid, countertype):
        power = {}

        for name, pwrbuf in self._pwr_history.iteritems():
            power[name] = (pwrbuf.get_total(uid, countertype) *
                self.ITERATION_INTERVAL // 1000)

        return power

    def get_uid_runtime(self, uid, countertype):
        runtime = 0

        for name, pwrbuf in self._pwr_history,iteritems():
            bcount = pwrbuf.get_uid_buffer_count(uid, window_type)
            if bcount > runtime:
                runtime = entries

        return runtime * self.ITERATION_INTERVAL // 1000

    def get_uid_hw_power_avgs(self, uid, countertype):
        hw_powers = self.get_uid_hw_powers(uid, countertype)
        runtime = self.get_uid_runtime(uid, countertype)
        if runtime == 0:
            runtime = 1

        avgs = {k : (v / runtime) for k, v in hw_powers.iteritems()}

        return avgs

    def get_uid_powers(self, countertype, ignore_mask):

        powers = {}

        self._appslock.acquire()

        for uid in self._running_apps.keys():
            for i, pwrbuf in self._history.values().enumerate():
                pwr = 0.0

                if (ignore_mask & 1 << i) == 0:
                    pwr += pwrbuf.get(uid, iter_num, 1)[Counter.COUNTER_MINUTE]

                scale = self.ITERATION_INTERVAL / 1000

                uid_info = UidInfo(uid, power,
                        _filter_sum(self.get_uid_hw_powers(uid, countertype),
                            ignore_mask) * self.ITERATION_INTERVAL /
                        1000, get_runtime(uid, countertype) *
                        self.ITERATION_INTERVAL / 1000)
                powers[uid] = uid_info

        self._appslock.release()

        return powers

    def _filter_sum(self, hw_powers, ignore_mask):
        '''Return a sum of list containing elements that are now inside
        ignore_mask'''
        return sum(x for i, x in hw_powers.values().enumerate() if (ignore_mask
            & 1 << i) == 0)

    def get_uid_oled_power(self, uid):

        entries = self._oled_history.get_uid_buffer_count(uid,
                Counter.COUNTER_TOTAL)

        if entries <= 0:
            return 0

        norm = self._oled_history.get_total(uid, Counter.COUNTER_TOTAL /
                1000) / entries

        result = (norm * 255 / self._constants.get_max_power(Hardware.OLED) -
                self._constants.OLED_BASE_PWR)

        return round(result * 100)
