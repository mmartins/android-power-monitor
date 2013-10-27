#!/usr/bin/env python

from jnius import autoclass

PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')


class ResourceAccess(object):

    __slot__ = ["activity_manager"]

    def __init__(self):
        self.activity_manager = \
            PythonActivity.mActivity.getSystemService(Context.ACTIVITY_SERVICE)

    def get_running_apps(self):
        return self.activity_manager.getRunningAppProcesses().toArray()
