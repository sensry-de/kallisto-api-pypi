from datetime import datetime, timezone
from kallistoapi.modules.sensor import Sensor


class SensorTime(Sensor):

    def __init__(self, device):
        Sensor.__init__(self, device, "time")
        # configure decoding
        self.value_byte_len = 10
        self.value_count_per_sample = 1
        self.decode = self.timestamp_from_bytearray
        #
        self.config_bytes = self._set_datetime()
        # register functions for configuration parameters
        self.register("datetime", self._get_datetime, self._set_datetime)

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "00001805-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        # read time
        return "00002a2b-0000-1000-8000-00805f9b34fb"

    @classmethod
    def config_uuid(cls):
        # write time
        return "00002a2b-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## special functions of this service
    def value(self):
        data_bytes = self.read(self.data_uuid())
        return self.timestamp_from_bytearray(data_bytes)

    def _get_datetime(self):
        return self.timestamp_from_bytearray(self.config_bytes)

    def _set_datetime(self, value = None):
        if value is None:
            value = datetime.now(tz=timezone.utc)

        config = value.year.to_bytes(2, "little")
        config += value.month.to_bytes(1, "little")
        config += value.day.to_bytes(1, "little")
        config += value.hour.to_bytes(1, "little")
        config += value.minute.to_bytes(1, "little")
        config += value.second.to_bytes(1, "little")
        config += b'\x00'  # day of the week (undefined)
        config += b'\x00'  # fractions of 256th of a second (undefined)
        config += b'\x01'  # Adjust reason: manual time update

        self.config_bytes = config

        return self.config_bytes

    def timestamp_from_bytearray(self, byte_array):
        # Assuming byte_array is a bytearray object containing the timestamp bytes
        year = int.from_bytes(byte_array[0:2], byteorder="little")
        month = int.from_bytes(byte_array[2:3], byteorder="little")
        day = int.from_bytes(byte_array[3:4], byteorder="little")
        hour = int.from_bytes(byte_array[4:5], byteorder="little")
        minute = int.from_bytes(byte_array[5:6], byteorder="little")
        second = int.from_bytes(byte_array[6:7], byteorder="little")

        timestamp = datetime(year, month, day, hour, minute, second)
        return timestamp