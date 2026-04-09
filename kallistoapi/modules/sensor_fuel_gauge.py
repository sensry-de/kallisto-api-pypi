from kallistoapi.modules.sensor import Sensor


class SensorFuelGauge(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "fuel_gauge")

        # configure decoding
        self.scaling = 1.0
        self.value_byte_len = 1
        self.value_count_per_sample = 1
        self.decode = self.decode_values
        #
        self.config_bytes = bytearray([0])

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "0000180f-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        return "00002a19-0000-1000-8000-00805f9b34fb"


    ## ----------------------------------------------------
    ## special functions of this service

    def value(self):
        data_bytes = self.read(self.data_uuid())
        return list(data_bytes)[0]

    def apply_config(self):
        return