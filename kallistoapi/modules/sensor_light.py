from kallistoapi.modules.sensor import Sensor


class SensorLight(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "light")

        # configure decoding
        self.scaling = 1.0

        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)

        self.timestamp_length = 8
        self.value_byte_len = 4
        self.value_count_per_sample = 1
        self.value_type = float
        self.decode = self.decode_timestamp_value_pairs

        #
        self.config_bytes = bytearray([0])


    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00001120-702b-69b5-b243-d6094a2b0e24"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        return "000021a1-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00001144-702b-69b5-b243-d6094a2b0e24"

    def _get_sample_rate(self):
        return

    def _set_sample_rate(self, sample_rate):
        sr_default = 2

        sr_name = {
            "1s": 0,
            "10s": 1,
            "60s": 2,
            "0.125s": 3,
            "0.250s": 4,
            "0.500s": 5,
            "n.a.": 6,
            "0.800s": 7,
        }
        sr = sr_default
        if sample_rate in sr_name:
            sr = sr_name[sample_rate]

        cfg = (sr << 5)

        self.config_bytes[0] &= 0b00011111
        self.config_bytes[0] |= cfg
