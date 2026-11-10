"""Existing microstrain packet: two timestamps followed by float32 triples."""
import struct
from kallistoapi.modules.sensor_pt100 import SensorPT100


class SensorMicrostrain(SensorPT100):
    def __init__(self, device):
        super().__init__(device)
        self._name = "microstrain"
        self.config_bytes = bytearray([1 << 5])  # Disabled, 1 Hz.
        self.value_count_per_sample = 3
        self.decode = self._decode_microstrain

    RATE_CODES = {"10s": 0, "1s": 1, "0.1s": 2, "0.02s": 3, "150Hz": 4, "300Hz": 5}
    SAMPLE_INTERVALS = tuple(RATE_CODES)
    RATE_HZ = dict(zip(SAMPLE_INTERVALS, (0.1, 1, 10, 50, 150, 300)))

    def _get_sample_rate(self):
        header = self.config_bytes[0]
        code = header >> 5
        if header & 0x1e or code not in self.RATE_CODES.values():
            raise ValueError("Invalid microstrain sample-rate code")
        return next(rate for rate, value in self.RATE_CODES.items() if value == code)

    @classmethod
    def normalize_sample_rate(cls, sample_rate):
        aliases = {f"{hz:g}Hz": interval for interval, hz in cls.RATE_HZ.items()}
        return aliases.get(sample_rate, sample_rate)

    def _set_sample_rate(self, sample_rate):
        sample_rate = self.normalize_sample_rate(sample_rate)
        if sample_rate not in self.RATE_HZ:
            raise ValueError(f"Unsupported microstrain sample rate: {sample_rate}")
        code = self.RATE_CODES[sample_rate]
        self.config_bytes[0] = (self.config_bytes[0] & 1) | (code << 5)

    @classmethod
    def data_uuid(cls):
        return "00002211-702b-69b5-b243-d6094a2b0e24"

    @classmethod
    def config_uuid(cls):
        return "00002212-702b-69b5-b243-d6094a2b0e24"

    def _decode_microstrain(self, data, debug=False):
        if len(data) < 28 or (len(data) - 16) % 12:
            raise ValueError("Invalid microstrain packet length")
        first, last = struct.unpack_from("<QQ", data)
        count = (len(data) - 16) // 12
        if last < first or (count == 1 and last != first):
            raise ValueError("Invalid microstrain packet timestamps")
        return [{"ts": first + (last - first) * i // max(1, count - 1),
                 "value": list(struct.unpack_from("<3f", data, 16 + 12 * i))}
                for i in range(count)]
