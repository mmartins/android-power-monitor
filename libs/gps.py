from jnius import PythonJavaClass, java_method, autoclass

Looper = autoclass('android.os.Looper')
LocationManager = autoclass('android.location.LocationManager')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
GpsStatus = autoclass('android.location.GpsStatus')
Context = autoclass('android.content.Context')


class GPSListener(PythonJavaClass):
    __slots__ = ['location_manager']
    __javainterfaces__ = ['android/location/LocationListener']

    def __init__(self, callback):
        super(GPSListener, self).__init__()
        self.callback = callback
        self.location_manager = PythonActivity.mActivity.getSystemService(
            Context.LOCATION_SERVICE)

    def start(self):
        self.location_manager.requestLocationUpdates(
            LocationManager.GPS_PROVIDER,
            10000, 10, self, Looper.getMainLooper())

    def stop(self):
        self.location_manager.removeUpdates(self)

    @java_method('()I')
    def hashCode(self):
        return id(self)

    @java_method('(Landroid/location/Location;)V')
    def onLocationChanged(self, location):
        self.callback(self, 'location', location)

    @java_method('(Ljava/lang/String;)V')
    def onProviderDisabled(self, status):
        self.callback(self, 'provider-disabled', status)

    @java_method('(Ljava/lang/Object;)Z')
    def equals(self, obj):
        return obj.hashCode() == self.hashCode()


class GPSStatusListener(PythonJavaClass):
    __slots__ = ['location_manager']
    __javainterfaces__ = ['android/location/GpsStatus$Listener']

    def __init__(self, callback):
        super(GPSStatusListener, self).__init__()
        self.callback = callback
        self.gps_status = GpsStatus()
        self.location_manager = PythonActivity.mActivity.getSystemService(
            Context.LOCATION_SERVICE)

    def start(self):
        self.location_manager.addGpsStatusListener(self)

    def stop(self):
        self.location_manager.removeGpsStatusListener(self)

    @java_method('()I')
    def hashCode(self):
        return id(self)

    @java_method('(I)V')
    def onGpsStatusChanged(self, event):
        self.gps_status = self.location_manager.getGpsStatus(self.gps_status)
        self.callback(self, 'gps-status-changed', event)

    @java_method('(Ljava/lang/Object;)Z')
    def equals(self, obj):
        return obj.hashcode() == self.hashCode()
