import math

from kallistoapi.modules.sensor import Sensor


class SensorGyrometer(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "gyrometer")

        # configure decoding
        self.scaling = SensorGyrometer._update_scaling(2000)
        self.value_byte_len = 2
        self.value_count_per_sample = 3
        self.timestamp_length = 8
        self.decode = self.decode_2_timestamp_value_pairs
        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)
        self.register("sensitivity", self._get_sensitivity, self._set_sensitivity)

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
        return "00002151-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00001024-702b-69b5-b243-d6094a2b0e24"

    @classmethod
    def _update_scaling(cls, sensitivity):
        return (math.pi / 180 * sensitivity)/ 32768

    def _get_sample_rate(self, frame_rate):
        return

    def _set_sample_rate(self, frame_rate):
        fr_default = 0

        fr_name = {
            "25Hz": 0,
            "50Hz": 1,
            "100Hz": 2,
            "200Hz": 3,
            "400Hz": 4,
            "800Hz": 5,
        }
        fr = fr_default
        if frame_rate in fr_name:
            fr = fr_name[frame_rate]

        cfg = (fr << 5)

        self.config_bytes[0] &= 0b00011111
        self.config_bytes[0] |= cfg
        return

    def _get_sensitivity(self):
        return

    def _set_sensitivity(self, sensitivity):
        sens_default = 0

        sens_name = {
            "2000°/s": 0,
            "125°/s": 1,
            "250°/s": 2,
            "500°/s": 3,
            "1000°/s": 4,
        }
        sens = sens_default
        if sensitivity in sens_name:
            sens = sens_name[sensitivity]

        factors = [2000, 125, 250, 500, 1000]
        self.scaling = self._update_scaling(factors[sens])

        cfg = (sens << 1)
        self.config_bytes[0] &= 0b11110001
        self.config_bytes[0] |= cfg
        return
