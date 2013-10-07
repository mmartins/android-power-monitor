#!/usr/bin/env python

try:
    from libs.notification import NotificationProxy
except ImportError:
    from utils.androidhelpers.notification import NotificationProxy

try:
    from libs.audio import AudioAccess
except ImportError:
    from utils.androidhelpers.audio import AudioAccess

from monitors.devicemonitor import DeviceMonitor
from services.iterationdata import IterationData
from services.usagedata import UsageData
from utils.hardware import Hardware
from utils.systeminfo import SystemInfo

import threading.Lock

class Audio(DeviceMonitor):

    AudioProxy = AudioAccess()

    def __init__(self, devconstants=None):
        super(Audio, self).__init__(Hardware.AUDIO, devconstants)

        self._uid_states = {}
        self._uidstate_lock = threading.Lock()
        self._sys_uid = None

        callbacks = {
                NotificationProxy.ON_SYSTEM_MEDIA_CALL :
                self.__on_system_media_call,
                NotificationProxy.ON_START_MEDIA : self.__on_start_media,
                NotificationProxy.ON_STOP_MEDIA : self.__on_stop_media,
        }

        self.has_uid_information = NotificationProxy.is_available()

        if self.has_uid_information:
            self._event_server = NotificationProxy(callbacks)
            self._event_server.add_hook()


    def _on_exit(self):
        if self.has_uid_information:
            self._event_server.remove_hook()
        super(Audio, self)._on_exit()

    def __on_system_media_call(self, uid):
        self._sys_uid = uid

    def __on_start_media(self, uid, id_):
        uid_usage = MediaUsage(uid, id_)
        if (uid == SystemInfo.AID_SYSTEM) and (self._sys_uid is not None):
            uid_usage.proxy_uid = self._sys_uid
            self._sys_uid = None
        else:
            uid_usage.proxy_uid = uid
        with self._uidstate_lock:
            # Act like a treeset. Just insert, but don't update
            self._uid_states.setdefault(uid, uid_usage)

    def __on_stop_media(self, uid, id_):
        with self._uidstate_lock:
            del(self._uid_states[uid])

    def calc_iteration(self, iter_num):
        """ Return power usage of each application using audio after one
        iteration. """
        result = IterationData()

        audio_on = (len(self._uid_states) != 0) or (self.AudioProxy.is_music_active())
        result.set_sys_usage(AudioUsage(audio_on))

        with self._uidstate_lock:
            uid = -1

            for usage in self._uid_states.values():
                if (usage.uid != uid):
                    result.set_uid_usage(usage.proxy_uid, AudioUsage(true))
                uid = usage.uid

        return result

class AudioUsage(UsageData):

    __slots__ = ['music_on']

    def __init__(self, music_on):
        self.music_on = music_on

    def log(self, out):
        out.write("Audio-on {0}\n".format(self.music_on))

class MediaUsage(object):

    __slots__ = ['uid', 'id_', 'proxy_uid']

    def __init__(self, uid, id_):
        self.uid = uid
        self.id_ = id_
        self.proxy_uid = None

    def __eq__(self, obj):
        return (self.uid == obj.uid) and (self.id_ == self.id_)

    def __ne__(self, obj):
        return (self.uid != obj.uid) or (self.id_ != self.id_)

    def __lt__(self, obj):
        return (self.uid < obj.uid) or (self.id_ < uid_usage.id_)

    def __gt__(self, obj):
        return (self.uid > obj.uid) or (self.id_ < uid_usage.id_)

    def __le__(self, obj):
        return (self.uid <= obj.uid) or (self.id_ <= uid_usage.id_)

    def __ge__(self, obj):
        return (self.uid >= obj.uid) or (self.id_ >= uid_usage.id_)
