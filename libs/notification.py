#!/usr/bin/env python

from jnius import PythonJavaClass, java_method, autoclass

NotificationService = autoclass('edu.umich.PowerTutor.util.NotificationService')


class NotificationProxy(object):

    ON_START_WAKELOCK = 1
    ON_STOP_WAKELOCK = 2
    ON_START_SENSOR = 3
    ON_STOP_SENSOR = 4
    ON_START_GPS = 5
    ON_STOP_GPS = 6
    ON_SCREEN_BRIGHTNESS_CHANGED = 7
    ON_START_MEDIA = 8
    ON_STOP_MEDIA = 9
    ON_VIDEO_SIZE_CHANGED = 10
    ON_SYSTEM_MEDIA_CALL = 11
    ON_SCREEN_ON = 12
    ON_SCREEN_OFF = 13
    ON_INPUT_EVENT = 14
    ON_USER_ACTIVITY = 15
    ON_PHONE_ON = 16
    ON_PHONE_OFF = 17
    ON_PHONE_DATA_CONNECTION_STATE_CHANGED = 18
    ON_WIFI_ON = 19
    ON_WIFI_OFF = 20
    ON_WIFI_RUNNING = 21
    ON_WIFI_STOPPED = 22
    ON_BLUETOOTH_ON = 23
    ON_BLUETOOTH_OFF = 24
    ON_FULL_WIFI_LOCK_ACQUIRED = 25
    ON_FULL_WIFI_LOCK_RELEASED = 26
    ON_SCAN_WIFI_LOCK_ACQUIRED = 27
    ON_SCAN_WIFI_LOCK_RELEASED = 28
    ON_WIFI_MULTICAST_ENABLED = 29
    ON_WIFI_MULTICAST_DISABLED = 30
    ON_BATTERY_LEVEL_CHANGED = 31
    ON_RECORD_CURRENT_LEVEL = 32
    ON_VIDEO_ON = 33
    ON_VIDEO_OFF = 34
    ON_AUDIO_ON = 35
    ON_AUDIO_OFF = 36

    def __init__(self, callbacks):
        self._hook = NotificationReceiver(callbacks)

    def add_hook(self):
        NotificationService.addHook(self._hook)

    def remove_hook(self):
        NotificationService.removeHook(self._hook)

    @staticmethod
    def is_available():
        return NotificationService.available()


class NotificationReceiver(PythonJavaClass):
    __javainterfaces__ = ['edu.umich.PowerTutor.util.NotificationService$DefaultReceiver']

    def __init__(self, callbacks):
        super(NotificationReceiver, self).__init__()
        self.callbacks = callbacks

    @java_method('(ILjava/lang/String;I)V')
    def noteStartWakelock(self, uid, name, type_):
        self.callbacks[NotificationProxy.ON_START_WAKELOCK](uid, name, type_)

    @java_method('(ILjava/lang/String;I)V')
    def noteStopWakelock(self, uid, name, type_):
        self.callbacks[NotificationProxy.ON_STOP_WAKELOCK](uid, name, type_)

    @java_method('(II)V')
    def noteStartSensor(self, uid, sensor):
        self.callbacks[NotificationProxy.ON_START_SENSOR](uid, sensor)

    @java_method('(II)V')
    def noteStopSensor(self, uid, sensor):
        self.callbacks[NotificationProxy.ON_STOP_SENSOR](uid, sensor)

    @java_method('(I)V')
    def noteStartGps(self, uid, sensor):
        self.callbacks[NotificationProxy.ON_START_GPS](uid)

    @java_method('(I)V')
    def noteStopGps(self, uid):
        self.callbacks[NotificationProxy.ON_STOP_GPS](uid)

    @java_method('(I)V')
    def noteScreenBrightness(self, brightness):
        self.callbacks[NotificationProxy.ON_SCREEN_BRIGHTNESS_CHANGED](brightness)

    @java_method('(II)V')
    def noteStartMedia(self, uid, id_):
        self.callbacks[NotificationProxy.ON_START_MEDIA](uid, id_)

    @java_method('(II)V')
    def noteStopMedia(self, uid, id_):
        self.callbacks[NotificationProxy.ON_STOP_MEDIA](uid, id_)

    @java_method('(IIII)V')
    def noteVideoSize(self, uid, id_, width, height):
        self.callbacks[NotificationProxy.ON_VIDEO_SIZE_CHANGED](uid, id_,
                width, height)

    @java_method('(I)V')
    def noteSystemMediaCall(self, uid):
        self.callbacks[NotificationProxy.ON_SYSTEM_MEDIA_CALL](uid)

    # TODO: Add support for the following events
    # - noteScreenOn
    # - noteScreenOff
    # - noteInputEvent
    # - noteUserActivity
    # - notePhoneeOn
    # - notePhoneeOff
    # - notePhoneDataConnectionChanged
    # - noteWifiOn
    # - noteWifiOff
    # - noteWifiRunning
    # - noteWifiStopped
    # - noteBluetoothOn
    # - noteBluetoothOff
    # - noteFullWifiLockAcquired
    # - noteFullWifiLockReleased
    # - noteScanWifiLockAcquired
    # - noteScanWifiLockreleased
    # - noteWifiMulticastEnabled
    # - noteWifiMulticastDisabled
    # - setBattery
    # - recordCurrentLevel

    @java_method('(I)V')
    def noteVideoOn(self, uid):
        self.callbacks[NotificationProxy.ON_VIDEO_ON](uid)

    @java_method('(I)V')
    def noteVideoOff(self, uid):
        self.callbacks[NotificationProxy.ON_VIDEO_OFF](uid)

    @java_method('(I)V')
    def noteAudioOn(self, uid):
        self.callbacks[NotificationProxy.ON_AUDIO_ON](uid)

    @java_method('(I)V')
    def noteAudioOff(self, uid):
        self.callbacks[NotificationProxy.ON_AUDIO_OFF](uid)

    @java_method('()I')
    def hashCode(self):
        return id(self)

    @java_method('(Ljava/lang/Object;)Z')
    def equals(self, obj):
        return obj.hashCode() == self.hashCode()
