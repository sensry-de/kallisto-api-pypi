from kallistoapi.modules.device_info import DeviceInfo
from kallistoapi.modules.sensor_accelerometer import SensorAccelerometer
from kallistoapi.modules.sensor_barometer import SensorBarometer
from kallistoapi.modules.sensor_env_vector import SensorEnvVector
from kallistoapi.modules.sensor_fuel_gauge import SensorFuelGauge
from kallistoapi.modules.sensor_gyrometer import SensorGyrometer
from kallistoapi.modules.sensor_light import SensorLight
from kallistoapi.modules.sensor_magnetometer import SensorMagnetometer
from kallistoapi.modules.sensor_temperature import SensorTemperature
from kallistoapi.modules.sensor_pt100 import SensorPT100
from kallistoapi.modules.sensor_tx_power import SensorTxPower
from kallistoapi.modules.sensor_vibration import SensorVibration
from kallistoapi.modules.sensor_pressure import SensorPressure
from kallistoapi.modules.sensor_humidity import SensorHumidity
from kallistoapi.modules.sensor_eco2 import SensorECO2
from kallistoapi.modules.sensor_tvoc import SensorTvoc
from kallistoapi.modules.sensor_bvoc import SensorBVOC
from kallistoapi.modules.sensor_iaq import SensorIAQ
from kallistoapi.modules.sensor_time import SensorTime
from kallistoapi.modules.sensor_battery import SensorBattery
from kallistoapi.modules.sensor_thermocouple import SensorThermocouple
from kallistoapi.modules.sensor_noise import SensorNoise

class ModuleList:
    __list = {
        DeviceInfo.identity_uuid(): DeviceInfo,
        SensorTemperature.identity_uuid(): SensorTemperature,
        SensorFuelGauge.identity_uuid(): SensorFuelGauge,
        SensorVibration.identity_uuid(): SensorVibration,
        SensorAccelerometer.identity_uuid(): SensorAccelerometer,
        SensorGyrometer.identity_uuid(): SensorGyrometer,
        SensorMagnetometer.identity_uuid(): SensorMagnetometer,
        SensorLight.identity_uuid(): SensorLight,
        SensorPressure.identity_uuid(): SensorPressure,
        SensorHumidity.identity_uuid(): SensorHumidity,
        SensorECO2.identity_uuid(): SensorECO2,
        SensorTvoc.identity_uuid(): SensorTvoc,
        SensorBVOC.identity_uuid(): SensorBVOC,
        SensorIAQ.identity_uuid(): SensorIAQ,
        SensorBarometer.identity_uuid(): SensorBarometer,
        SensorTxPower.identity_uuid(): SensorTxPower,
        SensorPT100.identity_uuid(): SensorPT100,
        SensorEnvVector.identity_uuid(): SensorEnvVector,
        SensorTime.identity_uuid(): SensorTime,
        SensorBattery.identity_uuid(): SensorBattery,
        SensorThermocouple.identity_uuid(): SensorThermocouple,
        SensorNoise.identity_uuid(): SensorNoise,
    }


    def __init__(self):
        return

    @classmethod
    def create_service(cls, kallisto, service_uuid, characteristic_uuid):
        if characteristic_uuid not in cls.__list:
            return None

        ModuleClass = cls.__list[characteristic_uuid]

        # if service_uuid != ModuleClass.service_uuid():
        #     return None

        return ModuleClass(kallisto)
