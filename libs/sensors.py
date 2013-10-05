from jnius import autoclass

Sensor = autoclass('android.hardware.Sensor')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')

class SensorsAccess(object):

    @staticmethod
    def get_sensors():
        '''Return dictionary with (name, power) values for each Android
        sensor'''
        sm = PythonActivity.mActivity.getSystemService(Context.SENSOR_SERVICE)
        sensors = sm.getSensorList(Sensor.TYPE_ALL).toArray()
        ret = {s.getName(): s.getPower() for s in sensors}
        return ret
