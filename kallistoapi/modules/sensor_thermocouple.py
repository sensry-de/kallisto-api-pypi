from kallistoapi.modules.sensor import Sensor
from kallistoapi.config_pb2 import ADCExtentionConfig

class SensorThermocouple(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "thermocouple")

        # configure decoding
        self.scaling = 1.0 / 100

        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)
        self.register("adc_config", self._get_adc_config, self._set_adc_config)
        self.decode = self.decode_timestamp_value_pairs

        self.timestamp_length = 8
        self.value_byte_len = 4
        self.value_count_per_sample = 4
        self.value_type = float

        #
        self.config_bytes = bytearray([2 << 5])  # Disabled, 1 Hz default.

    RATE_CODES = {"10s": 0, "5s": 1, "1s": 2, "0.5s": 3,
                  "0.25s": 4, "0.1s": 5, "0.05s": 6, "0.02s": 7}
    SAMPLE_INTERVALS = tuple(RATE_CODES)
    RATE_HZ = dict(zip(SAMPLE_INTERVALS, (0.1, 0.2, 1, 2, 4, 10, 20, 50)))


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
        header = self.config_bytes[0]
        code = header >> 5
        if header & 0x1e or code not in self.RATE_CODES.values():
            raise ValueError("Invalid thermocouple sample-rate code")
        return next(rate for rate, value in self.RATE_CODES.items() if value == code)

    @classmethod
    def normalize_sample_rate(cls, sample_rate):
        aliases = {f"{hz:g}Hz": interval for interval, hz in cls.RATE_HZ.items()}
        return aliases.get(sample_rate, sample_rate)

    def _set_sample_rate(self, sample_rate):
        sample_rate = self.normalize_sample_rate(sample_rate)
        if sample_rate not in self.RATE_CODES:
            raise ValueError(f"Unsupported thermocouple sample rate: {sample_rate}")
        code = self.RATE_CODES[sample_rate]
        self.config_bytes[0] = (self.config_bytes[0] & 1) | (code << 5)
