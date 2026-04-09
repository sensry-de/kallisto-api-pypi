from kallistoapi.modules.sensor import Sensor


class SensorMagnetometer(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "magnetometer")

        # configure decoding
        self.scaling = 1.0/16
        self.value_byte_len = 2
        self.value_count_per_sample = 3
        self.timestamp_length = 8
        self.decode = self.decode_2_timestamp_value_pairs
        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)

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
        return "00002141-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00001026-702b-69b5-b243-d6094a2b0e24"

    def _get_sample_rate(self, frame_rate):
        return

    def _set_sample_rate(self, frame_rate):
        fr_default = 0

        fr_name = {
            "2Hz": 0,
            "10Hz": 1,
            "20Hz": 2,
            "30Hz": 3,
            "50Hz": 4,
            "100Hz": 5,
            "150Hz": 6,
            "200Hz": 7,
        }
        fr = fr_default
        if frame_rate in fr_name:
            fr = fr_name[frame_rate]

        cfg = (fr << 5)

        self.config_bytes[0] &= 0b00011111
        self.config_bytes[0] |= cfg
        return

