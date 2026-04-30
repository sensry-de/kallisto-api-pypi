import types
from kallistoapi.modules.base import ModuleBase
import struct

class Sensor(ModuleBase):


    def __init__(self, device, name):
        ModuleBase.__init__(self, device, name)
        #
        self.scaling = 1.0
        self.value_byte_len = 4
        self.value_type = int
        self.value_count_per_sample = 1
        self.ts_auto_increment = 0
        self.timestamp_length = 4
        self.decode = self.decode_timestamp_value_pairs

        self.recieved_data = dict()
        self.result_value_list = list()
        #
        self.register("enable", self._get_enable, self._set_enable, "Enable sensor")

        self.data = {}
        self._mac = None
        self.data_callback = None
        #
        self.config_bytes = bytearray()

    def apply_config(self):
        print(f"Applying config {self.name()} {self.config_uuid()} to {self.config_bytes}")
        self.write(self.config_uuid(), self.config_bytes)

    @classmethod
    def config_uuid(cls):
        raise NotImplementedError()

    def ble_notify_callback(self, sender, data_array):
        value_list = self.decode(data_array)

        if not (self.data_callback is None):
            self.data_callback(sender, value_list)

    def start_notify(self, param=None):
        if type(param) is list:
            self.recieved_data.clear()
            self.data_callback = self.default_data_handler
            self.result_value_list = param
        else:
            if param is None:
                self.data_callback = self.__notify_callback
            else:
                self.data_callback = param

        super().start_notify(self.ble_notify_callback)
        return

    def stop_notify(self):
        super().stop_notify()
        return self.get_data()

    def default_data_handler(self, sender, value_list):
        # Normalize MAC into DBus format
        mac_dbus = ""
        if not self._mac is None:
            mac_dbus = "dev_" + self._mac.replace(":", "_")

        if not mac_dbus in sender.path:
            print("not {} in {}", mac_dbus, sender.path)
            return

        uuid = sender.uuid
        if not uuid in self.recieved_data.keys():
            self.recieved_data[uuid] = []

        self.recieved_data[uuid].append(value_list)

    def __notify_callback(self, sender, value_list):
        print(value_list)

    def get_data(self):
        uuid = self.data_uuid()
        if uuid not in self.recieved_data.keys():
            return list()

        if self.result_value_list is None:
            self.result_value_list = list()

        self.result_value_list.append(self.recieved_data[uuid])
        return self.result_value_list

    # default for all sensors
    def _get_enable(self):
        return self.config_bytes[0] & 0b00000001 != 0

    def _set_enable(self, enable):
        self.config_bytes[0] &= 0b11111110
        self.config_bytes[0] |= int(enable)

    ## we expect to decode pairs of:
    #
    #   [ts, value0, value1, ...] [ts,value0, value1, ...] [ts, value0, value1, ...] ...
    #
    #   where (ts) is fixed 4 bytes and (value) can be configured with value_byte_len and value_count_per_sample
    #

    import struct

    def decode_multiple_enviroment_meas_with_timestamp(self, val_bytes, debug=False):
        """
        Decode multiple BLE environment messages concatenated in a single bytearray.
        Each message format:
          [timestamp (timestamp_len B)] [count 1B] [type 1B + value 4B] * count

        Returns a list of dictionaries:
          [{'timestamp': ..., 'values': {type: value, ...}}, ...]
        """
        pos = 0
        all_messages = []

        timestamp_len = self.timestamp_length

        while pos < len(val_bytes):
            # Read timestamp
            timestamp_bytes = val_bytes[pos:pos + timestamp_len]
            if len(timestamp_bytes) < timestamp_len:
                raise ValueError("Incomplete timestamp at the end of buffer")

            if timestamp_len == 4:
                timestamp = struct.unpack('<I', timestamp_bytes)[0]
            elif timestamp_len == 8:
                timestamp = struct.unpack('<Q', timestamp_bytes)[0]
            else:
                raise ValueError("Unsupported timestamp length")

            pos += timestamp_len

            # Read builder count
            if pos >= len(val_bytes):
                raise ValueError("Missing count after timestamp")
            count = val_bytes[pos]
            pos += 1

            # Read sensor values
            sensor_dict = {}
            for _ in range(count):
                if pos + 5 > len(val_bytes):
                    raise ValueError("Incomplete sensor data")

                sensor_type = val_bytes[pos]
                pos += 1

                value_bytes = val_bytes[pos:pos + 4]
                value = struct.unpack('<f', value_bytes)[0]
                pos += 4

                sensor_dict[sensor_type] = value

            all_messages.append({"ts": timestamp, "value": sensor_dict})

        return all_messages

    def decode_timestamp_dict_pairs(self, data_array, debug=False):
        l = len(data_array)
        timestamp_length = self.timestamp_length
        sample_len = timestamp_length + (self.value_byte_len * self.value_count_per_sample)

        value_list = []

        pos = 0

        for i in range(0, l, sample_len):

            # extract timestamp
            ts = int.from_bytes(data_array[i:i + timestamp_length], byteorder='little')
            pos += timestamp_length
            val_bytes = data_array[
                        i + timestamp_length:i + timestamp_length + self.value_byte_len * self.value_count_per_sample]

            # extract a number of values
            float_values = []

            for k in range(0, self.value_count_per_sample):

                float_value = 0.0
                if self.value_type is int:
                    int_value = int.from_bytes(
                        val_bytes[k * self.value_byte_len: k * self.value_byte_len + self.value_byte_len],
                        byteorder='little',
                        signed=True
                    )

                    float_value = int_value * self.scaling
                elif self.value_type is float:
                    val, = struct.unpack_from("<f", data_array, pos)
                    pos += self.value_byte_len
                    float_value = val
                elif self.value_type is dict:
                    print("self.value_type is dict")


            # create sample and add to list
            sample = {"ts": ts, "value": float_values}
            if debug:
                print(f"found {self} sample {sample}")
            value_list.append(sample)

        return value_list

    def decode_timestamp_value_pairs(self, data_array, debug=False):
        l = len(data_array)
        timestamp_length = self.timestamp_length
        sample_len = timestamp_length + (self.value_byte_len * self.value_count_per_sample)

        value_list = []

        pos = 0
        for i in range(0, l, sample_len):

            # extract timestamp
            ts = int.from_bytes(data_array[i:i + timestamp_length], byteorder='little')
            pos += timestamp_length
            val_bytes = data_array[i+timestamp_length:i+timestamp_length + self.value_byte_len * self.value_count_per_sample]

            # extract a number of values
            float_values = []

            for k in range(0, self.value_count_per_sample):

                float_value = 0.0
                if self.value_type is int:
                    int_value = int.from_bytes(
                        val_bytes[k * self.value_byte_len: k * self.value_byte_len + self.value_byte_len],
                        byteorder='little',
                        signed=True
                    )

                    float_value = int_value * self.scaling
                elif self.value_type is float:
                    val, = struct.unpack_from("<f", data_array, pos)
                    pos += self.value_byte_len
                    float_value = val
                elif self.value_type is dict:
                   print("self.value_type is dict")
                   float_values = self.decode_enviroment_meas(val_bytes)


                float_values.append(float_value)

            # create sample and add to list
            sample = {"ts": ts, "value": float_values}
            if debug:
                print(f"found {self} sample {sample}")
            value_list.append(sample)

        return value_list

    def decode_2_timestamp_value_pairs(self, data_array, debug=False):
        l = len(data_array)
        timestamp_length = self.timestamp_length
        sample_len = (self.value_byte_len * self.value_count_per_sample)

        samples_count = int((l - 2 * timestamp_length) / sample_len)

        if samples_count < 2:
            return None
        value_list = []
        #for i in range(0, l, sample_len):

        # extract timestamp
        ts_start = int.from_bytes(data_array[0:timestamp_length], byteorder='little')
        ts_end = int.from_bytes(data_array[timestamp_length : 2 * timestamp_length], byteorder='little')
        ts_delta = ts_end - ts_start
        ts_delta = ts_delta / (samples_count - 1)
        ts_delta = int(ts_delta)

        val_bytes = data_array[2 * timestamp_length:]

        # extract a number of values
        for index in range(0, samples_count):

            float_values = []

            for k in range(0, self.value_count_per_sample):
                offset = self.value_count_per_sample * index
                offset = offset + k
                offset = offset * self.value_byte_len
                int_value = int.from_bytes(val_bytes[offset:offset + self.value_byte_len], byteorder='little', signed=True)
                float_value = int_value * self.scaling
                float_values.append(float_value)

            # create sample and add to list
            sample = {"ts": int(ts_start + index * ts_delta), "value": float_values}

            if debug:
                print(f"found sample {sample}")
            value_list.append(sample)

        return value_list

    def decode_timestamp_dyn_vector(self, data_array, debug=False):
        """
            Parse binary packet from live_and_dump_build_packet()

            Format:
            - 8 bytes: timestamp (uint64, little endian, nanoseconds)
            - then repeating samples:
                - N * 4 bytes: float32 values
            """
        pos = 0
        data = data_array
        # timestamp is 8 bytes little endian
        ts, = struct.unpack_from("<Q", data, pos)
        pos += 8

        samples = []

        while pos < len(data):
            if pos >= len(data):
                break
            # read length
            # length, = struct.unpack_from("<B", data, pos)
            # pos += 1

            length = 4

            values = []
            for _ in range(length):
                val, = struct.unpack_from("<f", data, pos)
                pos += 4
                values.append(val)

            sample = {"ts": ts, "value": values}
            if debug:
                print(f"found sample {sample}")
            samples.append(sample)

        return samples

    ## we expect to decode a single timestamp followed by value pairs:
    #
    #   [ts] [value0, value1, ...] [value0, value1, ...] [value0, value1, ...] ...
    #
    #   where (ts) is fixed 4 bytes and (value) can be configured with value_byte_len
    #
    def decode_single_timestamp_with_multiple_values(self, data_array, debug=False):
        l = len(data_array)
        ts_size = 4
        sample_len = self.value_byte_len * self.value_count_per_sample

        ts_packet = int.from_bytes(data_array[0:ts_size], byteorder='little')

        value_list = []
        for i in range(0, l - ts_size, sample_len):

            # extract timestamp

            ts = ts_packet
            val_bytes = data_array[i+ts_size:i+ts_size + self.value_byte_len * self.value_count_per_sample]

            # extract a number of values
            float_values = []
            for k in range(0, self.value_count_per_sample):
                int_value = int.from_bytes(val_bytes[k*self.value_byte_len:k*self.value_byte_len + self.value_byte_len], byteorder='little', signed=True)
                float_value = int_value * self.scaling
                float_values.append(float_value)

            # create sample and add to list
            sample = {"ts": ts, "value": float_values}
            if debug:
                print(f"found sample {sample}")
            value_list.append(sample)

            ts_packet = ts_packet + self.ts_auto_increment

        return value_list


    ## we expect to decode byte values without timestamp:
    #
    #   [value] [value] [value] ...
    #
    # value is configurable number of bytes (value_byte_len)
    #
    def decode_values(self, data_array, debug=False):
        l = len(data_array)
        sample_len = self.value_byte_len * self.value_count_per_sample

        value_list = []
        for i in range(0, l, sample_len):

            # extract timestamp
            ts = 0
            val_bytes = data_array[i:i + self.value_byte_len * self.value_count_per_sample]

            # extract a number of values
            for k in range(0, self.value_count_per_sample):
                int_value = int.from_bytes(val_bytes[k*self.value_byte_len:k*self.value_byte_len + self.value_byte_len], byteorder='little')
                float_value = int_value * self.scaling

                # create sample and add to list
                sample = {"ts": ts, "value": float_value}
                if debug:
                    print(f"found sample {sample}")
                value_list.append(sample)

        return value_list
