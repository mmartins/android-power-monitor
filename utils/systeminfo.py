#!/usr/bin/env python

import logging
import os


class SystemInfo(object):
    # UIDs as listed in android_filesystem_config.h
    AID_ALL = -1            # request for global information
    AID_ROOT = 0            # traditional Unix root user
    AID_SYSTEM = 1000       # system server
    AID_RADIO = 1001        # telephony, RIL
    AID_BLUETOOTH = 1002    # bluetooth
    AID_GRAPHICS = 1003     # graphics
    AID_INPUT = 1004        # input
    AID_AUDIO = 1005        # audio
    AID_CAMERA = 1006       # camera
    AID_LOG = 1007          # log devices
    AID_COMPASS = 1008      # compass sensor
    AID_MOUNT = 1009        # mountd socket
    AID_WIFI = 1010         # WiFi
    AID_ADB = 1011          # android debug bridge (adbd)
    AID_INSTALL = 1012      # package installer
    AID_MEDIA = 1013        # media server
    AID_DHCP = 1014         # DHCP client
    AID_SHELL = 2000        # ADB shell
    AID_CACHE = 2001        # cache access
    AID_DIAG = 2002         # access to diagnostic resources

    # 3000 series are intended for use as supplemental group IDs only
    # They indicate special Android capabilities that the kernel is aware of
    AID_NET_BT_ADMIN = 3001 # bluetooth: create any socket
    AID_NET_BT = 3002       # BT: create sco, rfcomm or l2cap socks
    AID_INET = 3003         # create AF_INET and AF_INET6 sockets
    AID_NET_RAW = 3004      # create raw INET sockets

    AID_MISC = 9998         # access to misc storage
    AID_NOBODY = 9999
    AID_APP = 10000         # first app user

    PID_STAT_MASK = "/proc/{0}/stat"
    PROC_DIR = "/proc"
    PROC_MEM_FILE = "/proc/meminfo"
    PROC_STAT_FILE = "/proc/stat"
    UID_STATS_DIR = "/proc/uid_stat/"
    UID_STATUS_MASK = "/proc/{0}/status"

    INDEX_USR_TIME = 0
    INDEX_SYS_TIME = 1
    INDEX_TOTAL_TIME = 2

    logger = logging.getLogger("SystemInfo")

    @classmethod
    def get_uid_for_pid(cls, pid):
        try:
            with open(cls.UID_STATUS_MASK.format(pid)) as fp:
                data = fp.readlines(6)
                if data[6].startswith("Uid"):
                    uid_str = data[6].split(":")[1].split()[0]
                    return int(uid_str)
        except IOError:
            pass

        cls.logger.error("Failed to read UID for PID {0}".format(pid))

        return -1

    @classmethod
    def get_running_pids(cls):
        # Assume all files in PROC_DIR which are numbers represent pids
        # WARNING: isdigit() only works with non-negative integers
        pids = [int(file_)
                for file_ in os.listdir(cls.PROC_DIR) if file_.isdigit()]
        return pids

    @classmethod
    def get_uids(cls):
        return [int(uid) for uid in os.listdir(cls.UID_STATS_DIR)]

    @classmethod
    def get_pid_usr_sys_times(cls, pid):
        """ times should contain two elements: times[INDEX_USR_TIME] constains
        user time for pid and times[INDEX_SYS_TIME] contains sys time for pid
        """
        try:
            with open(cls.PID_STAT_MASK.format(pid)) as fp:
                data = fp.read().split()
                return [int(data[13]), int(data[14])]
        except (IOError, IndexError, ValueError):
            pass

        cls.logger.error("Failed to read CPU time for PID {0}".format(pid))

        return []

    @classmethod
    def get_usr_sys_total_times(cls, cpu):
        """ times should contain seven elements. times[INDEX_USR_TIME]
        containts total user time, times[INDEX_SYS_TIME] contains total sys
        time, and times[INDEX_TOTAL_TIME] contains total time (including idle
        cycles)
        """
        try:
            with open(cls.PROC_STAT_FILE) as fp:
                data = fp.readlines(cpu + 1)
                if data[cpu + 1].startswith("cpu"):
                    times = data[cpu + 1].split()
                    # [usr, sys, total]
                    usr = int(times[1]) + int(times[2])
                    sys = int(times[2]) + int(times[6]) + int(times[7])
                    total = usr + sys + int(times[4]) + int(times[5])
                    return [usr, sys, total]
        except (IOError, IndexError, ValueError):
            pass

        cls.logger.error("Failed to read CPU time")

        return []

    @classmethod
    def get_mem_info(cls):
        """ mem should contain 4 elements. mem[INDEX_MEM_TOTAL] contains total
        memory available (Kb), mem[INDEX_MEM_FREE] contains amount of free
        memory (Kb), mem[INDEX_MEM_BUFFERS] contains size of kernel buffers
        (Kb), and mem[INDEX_MEM_CACHED] contains size of kernel caches (Kb)
        """
        try:
            with open(cls.PROC_MEM_FILE) as fp:
                data = fp.readlines(4)
                if data[0].startswith("MemTotal"):
                    total = int(data[0].split()[1])
                if data[1].startswith("MemFree"):
                    free = int(data[1].split()[1])
                if data[2].startswith("Buffers"):
                    buffers = int(data[2].split()[1])
                if data[3].startswith("Cached"):
                    cached = int(data[3].split()[1])

                return [total, free, buffers, cached]
        except (IOError, IndexError, ValueError):
            pass

        cls.logger.error("Failed to read memory info")

        return []
