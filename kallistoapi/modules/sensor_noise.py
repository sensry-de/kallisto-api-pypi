from kallistoapi.modules.sensor import Sensor


class SensorNoise(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "noise")

        # configure decoding
        self.scaling = 1.0

        # register functions for configuration parameters
        self.register("sample_rate", self._get_sample_rate, self._set_sample_rate)
        self.register("channel", self._get_channel, self._set_channel)
        self.register("word_width", self._get_word_width, self._set_word_width)
        self.register("frequency", self._get_frequency, self._set_frequency)
        self.register("raw_flag", self._get_raw_flag, self._set_raw_flag)

        self.timestamp_length = 8
        self.value_byte_len = 2
        self.value_count_per_sample = 1
        self.value_type = int
        self.decode = self.decode_2_timestamp_value_pairs
        self.timestamp_length = 8

        #
        # 2-byte BLE configuration packet
        self.config_bytes = bytearray([0x00, 0x00])


    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00001120-702b-69b5-b243-d6094a2b0e24"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        return "000021d1-702b-69b5-b243-d6094a2b0e24"



    ## ----------------------------------------------------
    ## special functions of this service

    @classmethod
    def config_uuid(cls):
        return "00001150-702b-69b5-b243-d6094a2b0e24"

    # =========================================================================
    # SAMPLE RATE / PERIOD
    # bits: [3:1]
    # =========================================================================

    def _get_raw_flag(self):
        flag = (self.config_bytes[1] & 0b10000000) >> 7
        return flag

    def _set_raw_flag(self, value):
        self.decode = self.decode_2_timestamp_value_pairs if value else self.decode_timestamp_value_pairs
        self.config_bytes[1] |= (value << 7)

    def _get_sample_rate(self):
        period_code = (self.config_bytes[0] & 0b00001110) >> 1

        period_map = {
            0b000: "1s",
            0b001: "0.5s",
            0b010: "0.1s",
            0b011: "0.0s",
        }

        return period_map.get(period_code, "0.1s")

    def _set_sample_rate(self, sample_rate):
        period_map = {
            "1s": 0b000,
            "0.5s": 0b001,
            "0.1s": 0b010,
            "0.0s": 0b011,
        }

        if sample_rate not in period_map:
            raise ValueError(
                "sample_rate must be one of: "
                "'1s', '0.5s', '0.1s', '0.0s'",
            )

        period_code = period_map[sample_rate]

        # clear bits [3:1]
        self.config_bytes[0] &= 0b11110001

        # set bits [3:1]
        self.config_bytes[0] |= (period_code << 1)

# =========================================================================
# CHANNEL
# bits: [1:0]
# =========================================================================
    def _get_channel(self):
        channel_code = self.config_bytes[1] & 0b00000011

        channel_map = {
            0: "stereo",
            1: "left",
            2: "right",
        }

        return channel_map.get(channel_code, "stereo")


    def _set_channel(self, channel):
        channel_map = {
            "stereo": 0,
            "left": 1,
            "right": 2,
        }

        if channel not in channel_map:
            raise ValueError(
                "channel must be one of: "
                "'stereo', 'left', 'right'"
            )

        channel_code = channel_map[channel]

        # clear bits [1:0]
        self.config_bytes[1] &= 0b11111100

        # set bits [1:0]
        self.config_bytes[1] |= channel_code

    # =========================================================================
    # WORD WIDTH
    # bits: [3:2]
    # =========================================================================

    def _get_word_width(self):
        width_code = (self.config_bytes[1] & 0b00001100) >> 2

        width_map = {
            0b00: 8,
            0b01: 16,
            0b10: 24,
        }

        return width_map.get(width_code, 24)

    def _set_word_width(self, width):
        width_map = {
            8: 0b00,
            16: 0b01,
            24: 0b10,
        }

        if width not in width_map:
            raise ValueError("word_width must be 8, 16, or 24")

        width_code = width_map[width]

        # clear bits [3:2]
        self.config_bytes[1] &= 0b11110011

        # set bits [3:2]
        self.config_bytes[1] |= (width_code << 2)

    # =========================================================================
    # FREQUENCY
    # bits: [6:4]
    # =========================================================================

    def _get_frequency(self):
        freq_code = (self.config_bytes[1] & 0b01110000) >> 4

        freq_map = {
            0b000: 1000,
            0b001: 4000,
            0b010: 8000,
            0b011: 16000,
        }

        return freq_map.get(freq_code, 24000)

    def _set_frequency(self, frequency):
        freq_map = {
            1000: 0b000,
            2000: 0b001,
            4000: 0b010,
            8000: 0b011,
            16000: 0b100,
        }

        if frequency not in freq_map:
            raise ValueError(
                "frequency must be one of: "
                "1000, 2000, 4000, 8000, 16000"
            )

        freq_code = freq_map[frequency]

        # clear bits [6:4]
        self.config_bytes[1] &= 0b10001111

        # set bits [6:4]
        self.config_bytes[1] |= (freq_code << 4)
