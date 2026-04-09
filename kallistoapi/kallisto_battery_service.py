import struct
import json

import struct
import json
from datetime import datetime, timezone

class BatteryConfig:
    def __init__(self, command, mode=None, value=None):
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

        return bytes(result)

    @staticmethod
    def from_bytes(data):
        if len(data) < 1:
            raise ValueError("Data too short")

        command = data[0]

        if len(data) == 1:
            return BatteryConfig(command)

        mode = data[1]

        if mode == 0x01 and len(data) >= 6:
            value = struct.unpack('<I', data[2:6])[0]
        elif mode == 0x02 and len(data) >= 12:
            value = data[2:12]  # leave as raw bytes
        else:
            raise ValueError("Invalid or incomplete data for the specified mode")

        return BatteryConfig(command, mode, value)

    def to_dict(self):
        data = {
            'command': self.command,
            'mode': self.mode
        }

        if self.mode == 0x01:
            data['value'] = self.value
        elif self.mode == 0x02:
            data['value'] = list(self.value) if self.value else None

        return data

    @staticmethod
    def from_dict(data):
        value = data.get('value')
        if isinstance(value, list):  # CTS bytes in list form
            value = bytes(value)
        return BatteryConfig(data['command'], data.get('mode'), value)

    def save_to_json(self, filepath):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @staticmethod
    def load_from_json(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return BatteryConfig.from_dict(data)



class BatteryHandler:
    def serialize(self, config):
        """Serializes a MicrostrainConfig object to bytes."""
        return config.to_bytes()

    def deserialize(self, data):
        """Deserializes bytes to a MicrostrainConfig object."""
        return BatteryConfig.from_bytes(data)

    def set_battery_config(self, json_filepath):
        """
        Loads configuration from a JSON file, serializes it to bytes,
        and returns the serialized configuration.
        """
        config = BatteryConfig.load_from_json(json_filepath)
        serialized_config = config.to_bytes()

        print(f"Microstrain config with serialized value {serialized_config.hex()}")
        return serialized_config

    def get_battery_config(self, data):
        """
        Deserializes binary data to a MicrostrainConfig object
        and converts it to a dictionary.
        """
        config = BatteryConfig.from_bytes(data)
        return config.to_dict()

    def unpack_battery_samples(self, buffers: list[bytes]):
        return buffers

if __name__ == "__main__":
    from datetime import datetime, timedelta
    # Schedule shutdown untill tomorrow 08:30
    future_time = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0) + timedelta(days=1)

    config = BatteryConfig(command=0x01, mode=0x02, value=future_time)
    payload = config.to_bytes()

    print(payload.hex())  # Output binary payload in hex format

    handler = BatteryHandler()
    # Serialize and Deserialize to Bytes
    serialized = handler.serialize(config)
    print("Serialized:", serialized)

    deserialized = handler.deserialize(serialized)
    print("Deserialized:", deserialized.__dict__)

    # Save to JSON and Load from JSON
    config.save_to_json("battery_config.json")
    loaded_config = BatteryConfig.load_from_json("battery_config.json")
    print("Loaded from JSON:", loaded_config.__dict__)
