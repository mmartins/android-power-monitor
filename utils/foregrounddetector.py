#!/usr/bin/env python

from libs.resources import ResourceAccess
from utils.systeminfo import SystemInfo
from jnius import autoclass


class ForegroundDetector(object):
    RunningAppProcessInfo = autoclass(
        'android.app.ActivityManager$RunningAppProcessInfo')
    IMPORTANCE_FOREGROUND = RunningAppProcessInfo.IMPORTANCE_FOREGROUND

    _resources = ResourceAccess()
    _displayed_uids = []

    @classmethod
    def get_foreground_uid(cls):

        last_displayed_uids = cls._displayed_uids

        apps = cls._resources.get_running_apps()

        # Find a valid app now. Hopefully there is only one. If there are non,
        # return system.
        #
        for app in apps:
            if app.importance == cls.IMPORTANCE_FOREGROUND:
                uid = SystemInfo.get_uid_for_pid(app.pid)
                # Make sure we have a user app and UID does not go over
                # kernel limit number
                if (uid >= SystemInfo.AID_APP) and uid < (1 << 16):
                    cls._displayed_uids.append(uid)

        cls._displayed_uids.sort()

        uid_enter = -1
        uid_exit = -1

        # Find an enter/exit front transition between iterations
        for (uid1, uid2) in zip(last_displayed_uids, cls._displayed_uids):
            if uid1 == uid2:
                continue
            elif uid1 < uid2:
                uid_enter = uid1
            else:
                uid_exit = uid2

        # Find a valid application. Hopefully there is only one. If there is
        # none, return system. If there are several, return the one with
        # highest UID.
        if uid_enter == uid_exit and uid_enter in cls._displayed_uids:
            return uid_enter

        return SystemInfo.AID_SYSTEM
