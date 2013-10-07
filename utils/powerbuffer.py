#!/usr/bin/env python

from utils.counter import Counter

class PowerBuffer(object):

    def __init__(self, max_queue_size):
        self._max_queue_size = max_queue_size
        self.uid_powers = {}

    def add_power(self, uid, iter_num, power):
        ''' Contract: iteration should only increase accross adds'''

        uid_power = self.uid_powers.get(uid, self._UidPower())
        uid_power.count.add(1)

        if power == 0:
            return

        uid_power.total.add(power)

        if self._max_queue_size == 0:
            return

        # Keep size of queue stable by treating it as circular queue (FILO)
        if len(uid_power.queue) > self._max_queue_size:
            uid_power.queue.pop()

        uid_power.queue.insert(0, self._PowerData(iter_num, power))

    def get_powers_up_to_timestamp(self, uid, timestamp, number):
        idx = 0

        if number < 0:
            number = 0

        if number > self._max_queue_size:
            number = self._max_queue_size

        powers = [0] * number
        uid_power = self.uid_powers.get(uid, None)

        if uid_power is None or len(uid_power.queue) == 0:
            return powers

        if timestamp == -1:
            timestamp = uid_power.queue[0].iter_num

        for data in uid_power.queue:
            while (data.iter_num < timestamp and idx < number):
                idx += 1
                timestamp -= 1

            if idx == number:
                break

            if data.iter_num == timestamp:
                powers[idx] = data.power
                idx += 1
                timestamp -= 1

        return powers

    def get_uid_total(self, uid, windowtype):
        uid_power = self.uid_powers.get(uid, None)
        if uid_power is not None:
            return uid_power.total.get(windowtype)

        return 0

    def get_uid_buffer_count(self, uid, windowtype):
        uid_power = self.uid_powers.get(uid, None)
        if uid_power is not None:
            return uid_power.count.get(windowtype)

        return 0

    class _UidPower(object):

        def __init__(self):
            self.queue = []
            self.total = Counter()
            self.count = Counter()

    class _PowerData(object):

        def __init__(self, iter_num, power):
            self.iter_num = iter_num
            self.power = power
