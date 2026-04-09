from kallistoapi.modules.sensor import Sensor


class SensorEnvVector(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "env_vector")

        # configure decoding
        self.scaling = 1.0 / 100

        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)

        self.timestamp_length = 8
        self.value_byte_len = 0
        self.value_count_per_sample = 1
        self.value_type = dict
        self.decode = self.decode_multiple_enviroment_meas_with_timestamp

        #
        self.config_bytes = bytearray([0])


    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00002000-702b-69b5-b243-d6094a2b0e24"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        return "00002411-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00002412-702b-69b5-b243-d6094a2b0e24"

    def _get_sample_rate(self):
        return

    def _set_sample_rate(self, sample_rate):
        sr_default = 0

        sr_name = {
            "0s" : 0,
            "1s": 1,
            "3s": 2,
            "10s": 3,
            "60s": 4,
        }
        sr = sr_default
        if sample_rate in sr_name:
            sr = sr_name[sample_rate]

        cfg = (sr << 5)

        self.config_bytes[0] &= 0b00011111
        self.config_bytes[0] |= cfg
