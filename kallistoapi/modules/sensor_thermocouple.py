from kallistoapi.modules.sensor import Sensor
from kallistoapi.config_pb2 import ADCExtentionConfig

class SensorThermocouple(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "thermocouple")

        # configure decoding
        self.scaling = 1.0 / 100

        # register functions for configuration parameters
        self.register("adc_config", self._get_adc_config, self._set_adc_config)
        self.decode = self.decode_timestamp_value_pairs

        self.timestamp_length = 8
        self.value_byte_len = 4
        self.value_count_per_sample = 4
        self.value_type = float

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
        return "00002511-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00002512-702b-69b5-b243-d6094a2b0e24"

    def _get_adc_config(self):
        result_config = None
        header = self.config_bytes[0]
        config_string = self.config_bytes[1:]

        if len(config_string) > 0:
            result_config = ADCExtentionConfig()
            result_config.ParseFromString(config_string)

        return result_config

    def _set_adc_config(self, config):
        self.adc_config = config
        config_string = config.SerializeToString()
        if len(self.config_bytes) > 0:
            header = self.config_bytes[0]
        else:
            header = 0x00

        self.config_bytes = bytearray([header]) + config_string

    def _get_sample_rate(self):
        return

    def _set_sample_rate(self, sample_rate):
        sr_default = 2

        sr_name = {
            "10s": 0,
            "5s": 1,
            "1s": 2,
            "0.5s": 3,
            "0.25s": 4,
            "0.1s": 5,
            "0.05s": 6,
            "0.02s": 7,
        }
        sr = sr_default
        if sample_rate in sr_name:
            sr = sr_name[sample_rate]

        cfg = (sr << 5)

        self.config_bytes[0] &= 0b00011111
        self.config_bytes[0] |= cfg
