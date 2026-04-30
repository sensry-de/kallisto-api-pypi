import time
import csv
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from dateutil import tz
from kallistoapi.bluetooth_gatt import BluetoothGatt
from kallistoapi.kallisto_sensry_serive_microstrain import MicrostrainHandler
from kallistoapi.modules.list import ModuleList

import struct
import time
import random
import crcmod

# Create CRC16 function (standard CRC-CCITT)
crc16 = crcmod.predefined.mkCrcFun('kermit')

microstrainHanlder = MicrostrainHandler()

CHARACTERISTICS = {
    "fuel_gauge": "00002a19-0000-1000-8000-00805f9b34fb",
    "temperature": "00001133-702b-69b5-b243-d6094a2b0e24",
    "vibration": "00001039-702b-69b5-b243-d6094a2b0e24",
    "log_vibration": "00002114-702b-69b5-b243-d6094a2b0e24",
    "dump_vibration": "00002111-702b-69b5-b243-d6094a2b0e24",
    "log_temperature": "00002104-702b-69b5-b243-d6094a2b0e24",
    "dump_temperature": "00002101-702b-69b5-b243-d6094a2b0e24",
    "vibration_statistic": "00002221-702b-69b5-b243-d6094a2b0e24",
    "microstrain": "00002211-702b-69b5-b243-d6094a2b0e24",
}

def get_characteristic_uuid(name):
    return CHARACTERISTICS.get(name)

def get_sensor_from_uuid(uuid):
    reverse_lookup = {v: k for k, v in CHARACTERISTICS.items()}
    return reverse_lookup.get(uuid)

CONFIG_UUIDS = {
    "temperature": "00001134-702b-69b5-b243-d6094a2b0e24",
    "vibration": "00001040-702b-69b5-b243-d6094a2b0e24",
    "accelerometer": "00001022-702b-69b5-b243-d6094a2b0e24",
    "log_vibration": "00002114-702b-69b5-b243-d6094a2b0e24",
    "log_temperature": "00002104-702b-69b5-b243-d6094a2b0e24",
    "log_memory": "00002024-702b-69b5-b243-d6094a2b0e24",
    "log_start_cond": "00002022-702b-69b5-b243-d6094a2b0e24",
    "log_global": "00002021-702b-69b5-b243-d6094a2b0e24",
    "vibration_statistic": "00002222-702b-69b5-b243-d6094a2b0e24",
    "transformation_manager": "00003032-702b-69b5-b243-d6094a2b0e24",
    "microstrain": "00002212-702b-69b5-b243-d6094a2b0e24",
    "microstrain_log": "00002214-702b-69b5-b243-d6094a2b0e24",
    "battery_shutdown": "2a1b",
    "boot_config" : "00003042-702b-69b5-b243-d6094a2b0e24",
    "boot_config_cmd" : "00003045-702b-69b5-b243-d6094a2b0e24",
}

def get_config_uuid(name):
    return CONFIG_UUIDS.get(name)

def get_config_from_uuid(uuid):
    reverse_lookup = {v: k for k, v in CONFIG_UUIDS.items()}
    return reverse_lookup.get(uuid)

def get_vibration_config(frame_rate, sensitivity, rms, enable):
    fr_default = 10
    sens_default = 2

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

    sens_name = {
        "8g": 0,
        "16g": 1,
        "64g": 2,
    }
    sens = sens_default
    if sensitivity in sens_name:
        sens = sens_name[sensitivity]

    cfg = (fr << 4)
    cfg |= (rms << 3)
    cfg |= (sens << 1)
    cfg |= enable

    return cfg


def get_temperature_config(sample_rate, enable):
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
    cfg |= enable

    return cfg


def decode_byte_array_to_value_list(data, scaling=1.0, value_byte_len=4, value_count_per_sample=1, debug=False):
    l = len(data)
    sample_len = 4 + (value_byte_len * value_count_per_sample)

    value_list = []
    for i in range(0, l, sample_len):

        # extract timestamp
        ts = int.from_bytes(data[i:i + 4], byteorder='little')
        val_bytes = data[i+4:i+4 + value_byte_len * value_count_per_sample]

        # extract a number of values
        for k in range(0, value_count_per_sample):
            int_value = int.from_bytes(val_bytes[k*value_byte_len:k*value_byte_len + value_byte_len], byteorder='little')
            float_value = int_value * scaling

            # create sample and add to list
            sample = {"ts": ts, "value": float_value}
            if debug:
                print(f"found sample {sample}")
            value_list.append(sample)

    return value_list

import struct


class KallistoManager(BluetoothGatt):

    def __init__(self):
        BluetoothGatt.__init__(self)
        self.notifications = {}
        self.modules = {}

    def discover_modules(self):
        services = self.detect_services()
        self.modules = {}

        for service_uuid, service in services.items():
            for characteristic_uuid, dummy in service.items():
                s = ModuleList.create_service(self, service_uuid, characteristic_uuid)
                if s is not None:
                    module_type = s.get_type()
                    if module_type not in self.modules:
                        self.modules[module_type] = {}

                    idx = len(self.modules[module_type])
                    s.set_idx(idx)

                    print(f"found module {characteristic_uuid} - {s.name()}")
                    self.modules[module_type][idx] = s

        # return a list of modules
        m = []
        for module_type in self.modules:
            for idx in self.modules[module_type]:
                m.append(self.modules[module_type][idx])
        return m

    def sync_time(self):
        time0 = self.get_module("time", 0)
        if time0 is not None:
            time0.configure("datetime", None)
            time0.apply_config()

    def get_module(self, module_type, idx = 0):
        if not module_type in self.modules:
            return None
        if not idx in self.modules[module_type]:
            return None

        self.modules[module_type][idx]._mac = self._mac
        return self.modules[module_type][idx]

    def set_sample_rate(self, sensor_name, sample_rate):
        if sensor_name == "temperature":
            self.set_temperature_config(sample_rate, 1)
        elif sensor_name == "vibration":
            self.set_vibration_config(sample_rate, 2, 0, 1)
        else:
            raise ValueError(f"Unknown sensor name {sensor_name}")

    def get_value(self, sensor_name):
        return self.read_gatt_characteristics(get_characteristic_uuid(sensor_name))

    def get_config(self, sensor_name):
        value = self.read_gatt_characteristics(get_config_uuid(sensor_name))
        return value

    def set_config(self, sensor_name, config):
        self.write_gatt_characteristics(get_config_uuid(sensor_name), config)

    def start_notify(self, sensor_name):
        print(f"KM Start notify on uuid: {get_characteristic_uuid(sensor_name)}")
        self.start_gatt_notify(get_characteristic_uuid(sensor_name), self._notify_callback)

    def uart_notification_handler(self, sender, data):
        print(f"Received from device: {data.decode('utf-8')}")
        return

    def start_ble_logs(self):
        NUS_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Notify
        self.start_gatt_notify(NUS_TX_UUID, self.uart_notification_handler)
        return
    def stop_notify(self, sensor_name):
        print(f"Stop notify on uuid: {get_characteristic_uuid(sensor_name)}")
        self.stop_gatt_notify(get_characteristic_uuid(sensor_name))

    def get_notify_data(self, sensor_name):
        if sensor_name in self.notifications:
            temp = self.notifications[sensor_name]
            self.notifications[sensor_name] = []
            return temp
        else:
            return None

    def wait_for_notify_values(self, sensor_name, count=1, timeout=10):
        start_time = time.time()
        while True:
            if sensor_name in self.notifications:
                if len(self.notifications[sensor_name]) >= count:
                    return
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Timeout after {timeout} seconds while waiting for {count} values.")
            time.sleep(0.1)

    def wait_for_specific_value(self, sensor_name, exp_value, timeout=30):
        start_time = time.time()
        while True:
            if sensor_name in self.notifications:
                for x in self.notifications[sensor_name]:
                    if x == exp_value:
                        return
            if timeout is not None:
                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Timeout after {timeout} seconds while waiting for {sensor_name} to reach expected value {exp_value}.")
            time.sleep(0.1)

    def _notify_callback(self, sender, data):
        uuid = sender.uuid
        sensor_name = get_sensor_from_uuid(uuid)

        if not sensor_name in self.notifications:
            self.notifications[sensor_name] = []

        notify_decoder = self.get_notify_decoder(sensor_name)
        if notify_decoder is not None:
            data_to_add = notify_decoder(data)
            if data_to_add is not None:
                self.notifications[sensor_name].append(data_to_add)
        else:
            print(f"missing notification decoder for {sensor_name}")

        return

    ## CONFIG
    def set_temperature_config(self, frame_rate, enable):
    #    cfg = ((1<<1) << 5) | 1
        cfg = get_temperature_config(frame_rate, enable)
        uuid = get_config_uuid("temperature")
        print(f"write temperature uuid: {uuid} to value {hex(cfg)}")
        self.write_gatt_characteristics(uuid, cfg.to_bytes(1))

    def set_vibration_config(self, frame_rate, sensitivity, rms, enable):
        cfg = get_vibration_config(frame_rate, sensitivity, rms, enable)
        uuid = get_config_uuid("vibration")
        print(f"write vibration uuid: {uuid} to value {hex(cfg)} --> {bin(cfg)}")
        self.write_gatt_characteristics(uuid, cfg.to_bytes(1))

    def set_microstrain_config(self, json_filepath):
        cfg = microstrainHanlder.set_microstrain_config(json_filepath)
        # Add the enable byte (0 or 1) to the configuration
        #cfg = struct.pack('<B', enable) + cfg  # Insert enable byte

        uuid = get_config_uuid("microstrain")

        self.write_gatt_characteristics(uuid, cfg)

    def set_microstrain_logging_config(self, enable):
        # Add the enable byte (0 or 1) to the configuration
        cfg = struct.pack('<B', enable)  # Insert enable byte

        uuid = get_config_uuid("microstrain_log")

        if not isinstance(cfg, bytes):
            print(f"write vibration uuid: {uuid} to value {hex(cfg)} --> {bin(cfg)}")
            cfg = cfg.to_bytes(1)

        self.write_gatt_characteristics(uuid, cfg)

    def get_microstrain_config(self):
        uuid = get_config_uuid("microstrain")

        data = self.read_gatt_characteristics(uuid)

        print(f"config {data}")

    def generate_ble_payload(enable: bool, source_id: int, window_type: int, window: int) -> bytes:
        """
        Generates a byte string for BLE transmission based on the given fields.

        :param enable: bool - Enable or Disable the transformation
        :param source_id: int - Unique identifier of the data source (4 bytes)
        :param window_type: int - Type of windowing function (1 byte)
        :param window: int - Size of the window in milliseconds or sample count (4 bytes)
        :return: bytes - The formatted byte string for BLE transmission
        """
        return struct.pack("<?I B I", enable, source_id, window_type, window)

    def send_chunk(self, uuid, order, offset, payload):
        """
        Helper function to wrap payload with protocol header + CRC, then send.
        """
        # Build header: 2 bytes order, 4 bytes offset, 4 bytes length
        header = struct.pack('<HII', order, offset, len(payload))

        # Combine header + payload for CRC calculation
        crc_data = header + payload
        chunk_crc = crc16(crc_data)

        # Final chunk: header + payload + CRC16
        packet = crc_data + struct.pack('<H', chunk_crc)

        # Send over BLE
        assert len(packet) <= self.mtu_size, f"Chunk too large: {len(packet)} bytes"
        self.write_gatt_characteristics(uuid, packet)

    def write_big_payload(self, uuid, payload):
        """
        Main function to send a large payload over BLE, split into protocol chunks.
        """
        self.mtu_size = 247 - 3  # Assume negotiated MTU - ATT overhead
        header_size = 10  # 2 + 4 + 4
        crc_size = 2  # CRC16
        chunk_size = self.mtu_size - header_size - crc_size

        print(f"Detected MTU: {self.mtu_size}, using chunk size: {chunk_size}")

        payload_offset = 0
        chunk_order = 0

        self.send_chunk(uuid, 0, 0, bytearray(0))

        while payload_offset < len(payload):
            chunk_payload = payload[payload_offset:payload_offset + chunk_size]
            print(f"Sending chunk {chunk_order}: offset={payload_offset}, length={len(chunk_payload)}")

            self.send_chunk(uuid, chunk_order, payload_offset, chunk_payload)

            payload_offset += len(chunk_payload)
            chunk_order += 1
            time.sleep(0.005)  # small delay

        # After sending all chunks, send final packet with full CRC
        print("Sending final packet...")
        full_crc = crc16(payload)
        final_payload = struct.pack('<H', full_crc)

        self.send_chunk(uuid, 0xFFFF, 0, final_payload)

        print(f"Final packet sent, full data CRC: {full_crc:04X}")

    def send_json_file(self, json_file_path):
        # Read JSON from file
        with open(json_file_path, "r") as f:
            json_data = f.read()

        uuid = get_config_uuid("transformation_manager")

        # Convert to bytes
        payload = json_data.encode('utf-8')

        print(f"Sending JSON file of {len(payload)} bytes...")

        # Call big payload sender
        self.write_big_payload(uuid, payload)

    def send_protobuf_config(self, config_file_path):
        # Read JSON from file
        with open(config_file_path, "r") as f:
            config_data = f.read()

        uuid = get_config_uuid("config_manager")

        # Convert to bytes
        payload = config_data.encode('utf-8')

        print(f"Sending JSON file of {len(payload)} bytes...")

        # Call big payload sender
        self.write_big_payload(uuid, payload)

    def set_statistic_config(self, source_id, window_type, window, enable):
        cfg = KallistoManager.generate_ble_payload(enable, source_id, window_type, window)
        uuid = get_config_uuid("vibration_statistic")
        print(f"write vibration uuid: {uuid} to value cfg")
        self.write_gatt_characteristics(uuid, cfg)

    def set_transformation_config(self, source_id, window_type, window, enable):
        cfg = KallistoManager.generate_ble_payload(enable, source_id, window_type, window)
        uuid = get_config_uuid("vibration_statistic")
        print(f"write vibration uuid: {uuid} to value cfg")

        # Generate sample payload (24000 bytes as an example)
        payload = bytearray(random.randint(0, 255) for _ in range(1200))  # Adjust size as needed
        self.write_big_payload(uuid, payload)
        # self.write_gatt_characteristics(uuid, cfg)

    def set_boot_config(self, payload):
        uuid = get_config_uuid("boot_config")
        self.write_big_payload(uuid, payload)

    import time

    def handler(self, sender, data):
        order = int.from_bytes(data[0:2], "little")
        offset = int.from_bytes(data[2:6], "little")
        length = int.from_bytes(data[6:10], "little")

        payload = data[10:10 + length]

        if order == 0xFFFF:
            self.stats["end_time"] = time.time()
            print("Transfer complete")
            self.transfer_complete = True
            return

        # stats
        self.stats["messages"] += 1
        self.stats["bytes_received"] += length

        if self.stats["min_chunk"] is None or length < self.stats["min_chunk"]:
            self.stats["min_chunk"] = length

        if length > self.stats["max_chunk"]:
            self.stats["max_chunk"] = length

        # detect duplicate
        if offset in self.buffer:
            self.stats["duplicates"] += 1

        # store chunk
        self.buffer[offset] = payload
        self.max_offset = max(self.max_offset, offset + length)

        print(f"chunk {order}, offset {offset}, len {length}")

    def rebuild(self):
        data = bytearray()
        expected_offset = 0

        for offset in sorted(self.buffer.keys()):
            chunk = self.buffer[offset]
            length = len(chunk)

            if offset != expected_offset:
                print(f"Gap detected: expected {expected_offset}, got {offset}")
                self.stats["gaps"] += 1
                return None

            data.extend(chunk)
            expected_offset += length

        if expected_offset != self.max_offset:
            print(f"Size mismatch: built {expected_offset}, expected {self.max_offset}")
            return None

        return data

    def print_stats(self):
        duration = None
        if self.stats["end_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]

        avg_chunk = 0
        if self.stats["messages"] > 0:
            avg_chunk = self.stats["bytes_received"] / self.stats["messages"]

        throughput = 0
        if duration and duration > 0:
            throughput = self.stats["bytes_received"] / duration

        print("\n=== TRANSFER STATS ===")
        print(f"Messages:        {self.stats['messages']}")
        print(f"Duplicates:      {self.stats['duplicates']}")
        print(f"Gaps detected:   {self.stats['gaps']}")
        print(f"Total bytes:     {self.stats['bytes_received']}")
        print(f"Min chunk:       {self.stats['min_chunk']}")
        print(f"Max chunk:       {self.stats['max_chunk']}")
        print(f"Avg chunk:       {avg_chunk:.2f}")

        if duration:
            print(f"Transfer time:   {duration:.3f} sec")
            print(f"Throughput:      {throughput:.2f} bytes/sec")

    def set_write_enable(self, enable):
        cmd_uuid = get_config_uuid("boot_config_cmd")
        cmd = 1 if enable else 3
        packet = struct.pack('<B', cmd)
        value = self.write_gatt_characteristics(cmd_uuid, packet)
        time.sleep(1)

    def get_boot_config(self):

        uuid = get_config_uuid("boot_config")
        cmd_uuid = get_config_uuid("boot_config_cmd")
        self.buffer = {}  # offset → bytes
        self.transfer_complete = False
        self.max_offset = 0

        cmd = 3
        packet = struct.pack('<B', cmd)
        value = self.write_gatt_characteristics(cmd_uuid, packet)
        time.sleep(1)

        self.start_gatt_notify(uuid, self.handler)

        self.stats = {
            "start_time": time.time(),
            "end_time": None,

            "messages": 0,
            "duplicates": 0,

            "bytes_received": 0,
            "min_chunk": None,
            "max_chunk": 0,

            "gaps": 0,
        }

        cmd = 2
        offset = 0
        payload_len = 0
        packet = struct.pack('<BII', cmd, offset, payload_len)
        value = self.write_gatt_characteristics(cmd_uuid, packet)
        while not self.transfer_complete:
            time.sleep(1)
        value = self.rebuild()
        print("get_boot_config value {}".format(value))

        self.print_stats()
        return value

    def start_temperature_notify(self, context):
        self.start_gatt_notify("temperature", context)

    def get_vibration_config(self):
        value = self.read_gatt_characteristics(get_config_uuid("vibration"))
        return value

    def get_accelerometer_config(self):
        value = self.read_gatt_characteristics(get_config_uuid("accelerometer"))
        return value

    def start_dump(self, sensor):
        uuid = get_config_uuid(sensor)
        cmd = 0x02
        print(f"start dump: write {hex(cmd)} to uuid: {uuid}")
        self.write_gatt_characteristics(uuid, cmd.to_bytes(1))

    def stop_logging(self):
        SENSRY_SERVICE_GLOBAL_LOGGING_CONFIG_UUID = "00002021-702b-69b5-b243-d6094a2b0e24"
        uuid = SENSRY_SERVICE_GLOBAL_LOGGING_CONFIG_UUID
        cmd = 0x00
        self.write_gatt_characteristics(uuid, cmd.to_bytes(1))

    def start_logging(self):
        SENSRY_SERVICE_GLOBAL_LOGGING_CONFIG_UUID = "00002021-702b-69b5-b243-d6094a2b0e24"
        uuid = SENSRY_SERVICE_GLOBAL_LOGGING_CONFIG_UUID
        cmd = 0x01
        self.write_gatt_characteristics(uuid, cmd.to_bytes(1))

    def get_notify_decoder(self, name):
        c = {
            "temperature": self.decode_temperature,
            "vibration": self.decode_vibration,
            "dump_vibration": self.decode_dump_vibration,
            "log_vibration": self.decode_log_vibration,
            "vibration_statistic" : self.decode_vibration_statistic,
            "microstrain": microstrainHanlder.unpack_microstrain_samples
        }
        if name in c:
            return c[name]
        else:
            return None

    def decode_temperature(self, data):
        if len(data) != 16:
            raise ValueError("Byte sequence must be exactly 16 bytes long.")
        l = decode_byte_array_to_value_list(data, 1.0 / 100, debug=True)
        self.notifications["temperature"] += l
        return None

    def decode_vibration(self, data):
        print(f"decoding vibration data {data}")
        return None

    def decode_dump_vibration(self, data):
        #print(f"decoding dump vibration data {data}")
        print(".", end="")
        self.notifications["dump_vibration"].append(data)
        return None

    def decode_log_vibration(self, data):
        #print(f"decoding log vibration data {data}")
        self.notifications["log_vibration"].append(data)
        return None

    def decode_vibration_statistic(self, data):
        self.notifications["vibration_statistic"].append(data)
        return None

    def unpack_ble_transformation_meas(self, buffer: bytes):
        """
        Unpacks a byte string formatted according to the C function build_ble_transformation_meas.

        :param buffer: bytes - The packed data buffer
        :return: tuple - (timestamp, range, x, y, z)
        """
        timestamp, data_type, x, y, z = struct.unpack("<I H f f f", buffer)
        return timestamp, data_type, x, y, z

    def unpack_multiple_samples(self, buffers: list[bytes]):
        """
        Processes a list of byte arrays, each potentially containing multiple samples.

        :param buffers: list of bytes - Each byte array may contain multiple samples
        :return: list of tuples - Unpacked samples
        """
        sample_size = struct.calcsize("<Q H f f f")
        all_samples = []

        for buffer in buffers:
            if len(buffer) % sample_size != 0:
                raise ValueError(f"Buffer length {len(buffer)} is not a multiple of sample size {sample_size}")

            num_samples = len(buffer) // sample_size
            for i in range(num_samples):
                sample = self.unpack_ble_transformation_meas(buffer[i * sample_size: (i + 1) * sample_size])
                all_samples.append(sample)

        return all_samples

    def on_vibration_statistic_live_and_dump(self, data_set, values_in_g=True):
        values = []
        try:
            values = self.unpack_multiple_samples(data_set)
        except:
            pass

        return values

    def on_vibration_live_and_dump(self, data_set, used_range = 8, values_in_g = True):
        values = []

        RANGE = used_range
        coofitient = 1.0 if values_in_g else 9.8

        end_of_previouse_chunk = bytearray()

        try:
            for data_chunk in data_set:
                data = end_of_previouse_chunk + data_chunk

                if ((len(data) % 14) != 0):
                    print(f'Unable to parse byte array of size {len(data)} as vibration data.')

                now = datetime.now(tz=timezone.utc)

                data_len = len(data)

                for i in range(0, data_len, 14):
                    measurement = data[i:i + 14]
                    timestamp = measurement[0:8]
                    timestamp_int = int.from_bytes(timestamp, "little", signed="False")
                    timestamp = float(timestamp_int / 1000000000.0)

                    unix_epoch = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                    if now - unix_epoch < timedelta(seconds=5):
                        print("live data, ignoring")
                        break

                    # Convert to local time
                    # Internally, we always use UTC
                    # if utc == False:
                    #     to_zone = tz.tzlocal()
                    #     unix_epoch = unix_epoch.astimezone(to_zone)
                    #
                    # unix_epoch_str = unix_epoch.strftime("%d/%m/%Y %H:%M:%S.%f")


                    x = measurement[8:10]
                    x = int.from_bytes(x, "little", signed="True")
                    x = x * (coofitient * RANGE / 32768)
                    y = measurement[10:12]
                    y = int.from_bytes(y, "little", signed="True")
                    y = y * (coofitient * RANGE / 32768)
                    z = measurement[12:14]
                    z = int.from_bytes(z, "little", signed="True")
                    z = z * (coofitient * RANGE / 32768)

                    values.append([timestamp, [x, y, z]])

                end_of_previouse_chunk = data_chunk[i + 14:]
        except:
            pass

        return values

    def create_report(self, data, file_path = "", utc = False):

        print("Report creating begins.. Please, wait until it finished.")
        if file_path is None or not len(file_path):
            # Get the current date and time
            current_time = datetime.now()

            # Format the date and time as 'day-month-year_hh-mm-ss'
            timestamp = current_time.strftime("%d%m%Y_%H%M%S")

            # Create the filename
            file_path = f"dump_report_{timestamp}.csv"

        # Combine data by timestamp
        combined_data = defaultdict(lambda: {"t": None, "v": None})
        #print("combined_data")

        list_t = data[0]
        list_v = data[1]

        if list_t is not None:
            for entry in list_t:
                timestamp = entry[0]
                content = entry[1]
                combined_data[timestamp]["t"] = content

        if list_v is not None:
            for entry in list_v:
                timestamp = entry[0]
                content = entry[1]
                combined_data[timestamp]["v"] = content

        # Sort timestamps
        sorted_timestamps = sorted(combined_data.keys())

        # Specify the CSV file name
        csv_file = file_path
        #print("open file")

        # Write the combined data to the CSV file
        with open(csv_file, mode='w', newline='') as file:

            if not len(csv_file):
                return
            #print("csv.writer")
            writer = csv.writer(file)

            # Write the header

            header = ['Timestamp\Sensor type', 'temperature', ' vibration X', ' vibration Y', ' vibration Z', '']
            writer.writerow(header)

            # Write each row
            for timestamp in sorted_timestamps:
                list_t_content = combined_data[timestamp]["t"][0] if combined_data[timestamp]["t"] is not None else ""
                list_vx_content = combined_data[timestamp]["v"][0] if combined_data[timestamp]["v"] is not None else ""
                list_vy_content = combined_data[timestamp]["v"][1] if combined_data[timestamp]["v"] is not None else ""
                list_vz_content = combined_data[timestamp]["v"][2] if combined_data[timestamp]["v"] is not None else ""
                #print("fromtimestamp")
                unix_epoch = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                if utc == False:
                    #print("tzlocal")
                    to_zone = tz.tzlocal()
                    #print("astimezone")
                    unix_epoch = unix_epoch.astimezone(to_zone)

                #print("strftime")
                unix_epoch_str = unix_epoch.isoformat(timespec='microseconds')

                if "+" in unix_epoch_str:
                    unix_epoch_str = unix_epoch_str.split("+")[0]
                else:
                    unix_epoch_str = unix_epoch_str.split("-")[0]
                row = [unix_epoch_str, list_t_content, list_vx_content, list_vy_content, list_vz_content, '']
                writer.writerow(row)

        print(f"Data successfully written to {csv_file}")

