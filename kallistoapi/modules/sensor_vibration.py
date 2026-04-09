from kallistoapi.modules.sensor import Sensor


class SensorVibration(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "vibration")

        # configure decoding
        self.scaling = 9.80665 * 8.0/ 32768.0
        self.value_byte_len = 2
        self.value_count_per_sample = 3
        self.ts_auto_increment = 0
        #self.decode = self.decode_single_timestamp_with_multiple_values
        self.decode = self.decode_2_timestamp_value_pairs
        self.timestamp_length = 8
        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)
        self.register("rms", self._get_rms, self._set_rms)
        self.register("sensitivity", self._get_sensitivity, self._set_sensitivity)

        #
        self.config_bytes = bytearray([0x00])

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00002000-702b-69b5-b243-d6094a2b0e24"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        return "00002111-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00001040-702b-69b5-b243-d6094a2b0e24"

    def _update_ts_auto_increment(self, fr):
        freq = 0.78125 * pow(2, fr)
        self.ts_auto_increment = 1000000/freq
        return

    def _get_sample_rate(self, frame_rate):
        return

    def _set_sample_rate(self, frame_rate):
        fr_default = 10

        fr_name = {
            "0.78125Hz": 0,
            "1.5625Hz": 1,
            "3.125Hz": 2,
            "6.25Hz": 3,
            "12.5Hz": 4,
            "25Hz": 5,
            "50Hz": 6,
            "100Hz": 7,
            "200Hz": 8,
            "400Hz": 9,
            "800Hz": 10,
            "1600Hz": 11,
            "3200Hz": 12,
            "6400Hz": 13,
            "12800Hz": 14,
            "25600Hz": 15,
        }
        fr = fr_default
        if frame_rate in fr_name:
            fr = fr_name[frame_rate]

        self._update_ts_auto_increment(fr)

        cfg = (fr << 4)

        self.config_bytes[0] &= 0b00001111
        self.config_bytes[0] |= cfg
        return

    def _get_rms(self, enabled=True):
        return

    def _set_rms(self, enabled=True):
        rms = int(enabled)
        cfg = (rms << 3)
        self.config_bytes[0] &= 0b11110111
        self.config_bytes[0] |= cfg
        return

    def _get_sensitivity(self):
        return

    def _set_sensitivity(self, sensitivity):
        sens_default = 2

        sens_name = {
            "8g": 0,
            "16g": 1,
            "64g": 2,
        }
        sens = sens_default
        if sensitivity in sens_name:
            sens = sens_name[sensitivity]
        cfg = (sens << 1)
        self.config_bytes[0] &= 0b11111001
        self.config_bytes[0] |= cfg
        return

