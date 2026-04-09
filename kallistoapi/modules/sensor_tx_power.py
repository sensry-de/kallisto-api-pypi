from kallistoapi.modules.sensor import Sensor


class SensorTxPower(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "tx_power")

        # configure decoding
        self.scaling = 1.0
        self.value_byte_len = 1
        self.value_count_per_sample = 1
        self.decode = self.decode_rssi
        #
        self.config_bytes = bytearray([0])
        # register functions for configuration parameters
        self.register("power-level", self._get_power_level, self._set_power_level)


    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00001804-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        # read RSSI
        return "0000ff01-0000-1000-8000-00805f9b34fb"


    @classmethod
    def config_uuid(cls):
        return "00002a07-0000-1000-8000-00805f9b34fb"


    ## ----------------------------------------------------
    ## special functions of this service

    def value(self):
        data_bytes = self.read(self.data_uuid())
        return list(data_bytes)[0]


    def _get_power_level(self):
        return int.from_bytes(self.config_bytes, byteorder="little", signed=True)

    def _set_power_level(self, value):
        if (value < -40) or (value > 8):
            return
        self.config_bytes = bytearray(value.to_bytes(1, byteorder="little", signed=True))
        return

    ## we expect to decode byte values without timestamp:
    #
    #   [value] [value] [value] ...
    #
    # value is configurable number of bytes (value_byte_len)
    #
    def decode_rssi(self, data_array, debug=False):
        l = len(data_array)
        sample_len = self.value_byte_len * self.value_count_per_sample

        value_list = []
        for i in range(0, l, sample_len):

            # extract timestamp
            ts = 0
            val_bytes = data_array[i:i + self.value_byte_len * self.value_count_per_sample]

            # extract a number of values
            for k in range(0, self.value_count_per_sample):
                int_value = int.from_bytes(val_bytes[k*self.value_byte_len:k*self.value_byte_len + self.value_byte_len], byteorder='little', signed=True)
                float_value = int_value * self.scaling

                # create sample and add to list
                sample = {"ts": ts, "value": float_value}
                if debug:
                    print(f"found sample {sample}")
                value_list.append(sample)

        return value_list
