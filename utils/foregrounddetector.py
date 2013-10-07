#!/usr/bin/env python

try:
    from libs.resources import ResourceAccess
except ImportError:
    from utils.androidhelpers.resources import ResourceAccess

from utils.systeminfo import SystemInfo
from jnius import autoclass

class ForegroundDetector(object):

    RunningAppProcessInfo = autoclass('android.app.ActivityManager$RunningAppProcessInfo')
    IMPORTANCE_FOREGROUND = RunningAppProcessInfo.IMPORTANCE_FOREGROUND

    _resources = ResourceAccess()
    _displayed_uids = []

    @classmethod
    def get_foreground_uid(cls):

        last_displayed_uids = cls._displayed_uids

        # Figure out
        apps = cls._resources.get_running_apps()

        # Find a valid app now. Hopefully there is only one. If there are non,
        # return system.
        #
        front_uids = [SystemInfo.get_uid_for_pid(app.pid) for app in
                apps if app.importance == cls.IMPORTANCE_FOREGROUND]

        cls._displayed_uids.sort()

        uid1 = uid2 = None

        # Find an enter/exit front transition between iterations
        for (uid1, uid2) in zip(last_displayed_uids, cls._displayed_uids):
            if uid1 == uid2:
                continue
            elif uid1 < uid2:
                uid_enter = uid1
            else:
                uid_exit = uid2

        # Find a valid application. Hopefully there is only one. If there is
        # none, return system. If there are several, return the onde with
        # highest UID.
        if uid_enter == uid_exit and uid_enter in cls._displayed_uids:
            return uid_enter

        return SystemInfo.AID_SYSTEM
