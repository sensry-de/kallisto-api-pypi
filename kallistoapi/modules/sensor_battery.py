from datetime import datetime, timezone
import struct
from kallistoapi.modules.sensor import Sensor
from dataclasses import dataclass
from typing import Union


class SensorBattery(Sensor):
    @dataclass
    class ShutdownConfig:
        command: int = None
        mode: int = None
        timestamp: Union[datetime, int] = None

        def __post_init__(self):
            if self.mode == 0x01 and not isinstance(self.timestamp, int):
                raise TypeError("For mode 0x01, timestamp must be int")

            if self.mode == 0x02 and not isinstance(self.timestamp, datetime):
                raise TypeError("For mode 0x02, timestamp must be datetime")


    def __init__(self, device):
        Sensor.__init__(self, device, "battery")
        # configure decoding
        self.value_byte_len = 10
        self.value_count_per_sample = 1
        self.decode = self.decode_battery_level
        #
        self.config_bytes = bytearray()
        # register functions for configuration parameters

        shutdown_description = """
        Configure device shutdown or reboot behavior.

        Parameters:
            command:
                0x01 -> shutdown device
                0x02 -> reboot device

            mode:
                0x01 -> time offset in seconds
                         timestamp must be int

                0x02 -> absolute date/time
                         timestamp must be datetime

            timestamp:
                int       -> delay in seconds (mode 0x01)
                datetime  -> exact execution time (mode 0x02)
        """

        self.register("shutdown", self._get_shutdown, self._set_shutdown, shutdown_description)

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "0000180f-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        # read time
        return "00002a19-0000-1000-8000-00805f9b34fb"

    @classmethod
    def config_uuid(cls):
        # write time
        return "00002a1b-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## special functions of this service
    def value(self):
        data_bytes = self.read(self.data_uuid())
        return self.decode(data_bytes)

    def _get_shutdown(self):
        return

    def _set_shutdown(self, config: ShutdownConfig):
        if config is None:
            raise ValueError("config cannot be None")
        self.change_config(config.command, config.mode, config.timestamp)
        self.config_bytes = self.to_bytes()
        return

    def change_config(self, command, mode=None, value=None):
        """
        :param command: 0x01 = shutdown, 0x02 = reboot
        :param mode: 0x01 = offset (value is int), 0x02 = absolute time (value is datetime)
        :param value: int (for offset), or datetime (for absolute time)
        """
        self.command = command
        self.mode = mode

        if self.mode == 0x02 and isinstance(value, datetime):
            # Convert to UTC before encoding
            utc_dt = value.astimezone(timezone.utc)
            self.value = self._datetime_to_cts_bytes(utc_dt)
        else:
            self.value = value

    def _datetime_to_cts_bytes(self, dt: datetime) -> bytes:
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        day_of_week = dt.isoweekday()  # Monday = 1, Sunday = 7
        fractions256 = 0
        adjust_reason = 0

        return struct.pack('<HBBBBBB2B',
                           year,
                           month,
                           day,
                           hour,
                           minute,
                           second,
                           day_of_week,
                           fractions256,
                           adjust_reason)

    def to_bytes(self):
        result = bytearray()
        result.append(self.command)

        if self.mode is not None:
            result.append(self.mode)

            if self.mode == 0x01 and isinstance(self.value, int):
                result += struct.pack('<I', self.value)
            elif self.mode == 0x02 and isinstance(self.value, (bytes, bytearray)) and len(self.value) == 10:
                result += self.value
            else:
                raise ValueError("Invalid value format for the given mode")
        return result

    def decode_battery_level(self, byte_array):
        return list(byte_array)[0]


