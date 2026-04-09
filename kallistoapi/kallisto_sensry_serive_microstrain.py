import struct
import json
from google.protobuf.json_format import ParseDict
import kallistoapi.config_pb2 as config_pb2

class ADCDriverConfig:
    def __init__(self, samples_per_second=0, v_ref=0, continiouse_mode=0, adc_gain=0, meas_cur=0, meas_cur_output=0, differential_mode=0):
        self.samples_per_second = samples_per_second
        self.v_ref = v_ref
        self.continiouse_mode = continiouse_mode
        self.adc_gain = adc_gain
        self.meas_cur = meas_cur
        self.meas_cur_output = meas_cur_output
        self.differential_mode = differential_mode

    def to_bytes(self):
        return struct.pack('<HBBBBBB',
                          self.samples_per_second,
                          self.v_ref,
                          self.continiouse_mode,
                          self.adc_gain,
                          self.meas_cur,
                          self.meas_cur_output,
                          self.differential_mode)

    @staticmethod
    def from_bytes(data):
        unpacked = struct.unpack('<HBBBBBB', data)
        return ADCDriverConfig(*unpacked)

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return ADCDriverConfig(**data)


class MicrostrainConfig:
    def __init__(self, period_us=0, over_sampling=0, oversampling_interval_us=0, resolution=0, r_ref=0.0, offset_mv=0.0, adc_quantization=1.0, lp_coof=0.0, adc_config=None):
        self.period_us = period_us
        self.over_sampling = over_sampling
        self.oversampling_interval_us = oversampling_interval_us
        self.resolution = resolution
        self.r_ref = r_ref
        self.offset_mv = offset_mv
        self.lp_coof = lp_coof
        self.adc_quantization = adc_quantization
        self.adc_config = adc_config if adc_config else ADCDriverConfig()


    def to_bytes(self):
        return struct.pack('<I I H B f f f f',
                          self.period_us,
                          self.over_sampling,
                          self.oversampling_interval_us,
                          self.resolution,
                          self.r_ref,
                          self.offset_mv,
                          self.adc_quantization,
                          self.lp_coof) + self.adc_config.to_bytes()

    @staticmethod
    def from_bytes(data):
        base_size = struct.calcsize('<I I H B f f f')
        unpacked = struct.unpack('<I I H B f f f', data[:base_size])
        adc_config = ADCDriverConfig.from_bytes(data[base_size:])
        return MicrostrainConfig(*unpacked, adc_config=adc_config)

    def to_dict(self):
        data = self.__dict__.copy()
        data['adc_config'] = self.adc_config.to_dict()
        return data

    @staticmethod
    def from_dict(data):
        adc_config = ADCDriverConfig.from_dict(data.get('adc_config', {}))
        return MicrostrainConfig(adc_config=adc_config, **{k: v for k, v in data.items() if k != 'adc_config'})

    def save_to_json(self, filepath):
        with open(filepath, 'w') as file:
            json.dump(self.to_dict(), file, indent=4)

    @staticmethod
    def load_from_json(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)

        #cfg = config_pb2.MicrostrainConfig()
        #ParseDict(data, cfg)  # auto-populates fields

        return bytearray(cfg.SerializeToString())

        #return MicrostrainConfig.from_dict(data)


import struct
import json

class MicrostrainHandler:
    def serialize(self, config):
        """Serializes a MicrostrainConfig object to bytes."""
        return config.to_bytes()

    def deserialize(self, data):
        """Deserializes bytes to a MicrostrainConfig object."""
        return MicrostrainConfig.from_bytes(data)

    def set_microstrain_config(self, json_filepath):
        """
        Loads configuration from a JSON file, serializes it to bytes,
        and returns the serialized configuration.
        """
        serialized_config = MicrostrainConfig.load_from_json(json_filepath)

        print(f"Microstrain config with serialized value {serialized_config.hex()}")
        return serialized_config

    def get_microstrain_config(self, data):
        """
        Deserializes binary data to a MicrostrainConfig object
        and converts it to a dictionary.
        """
        config = MicrostrainConfig.from_bytes(data)
        return config.to_dict()

    def unpack_microstrain_samples(self, buffers: list[bytes]):
        """
        Processes a list of byte arrays containing microstrain sensor data.

        Each buffer starts with an 8-byte timestamp followed by samples.
        Each sample consists of:
        - 4 bytes: adc_value (unsigned int)
        - 4 bytes: delta_r (float)
        - 4 bytes: lp (float)

        :param buffers: List of byte arrays from BLE containing microstrain data
        :return: List of tuples - (timestamp, adc_value, delta_r, lp)
        """
        timestamp_size = 8  # 8 bytes for timestamp
        sample_size = struct.calcsize("<I f f")  # 4 bytes for adc_value, 4 bytes for delta_r, 4 bytes for lp
        all_samples = []

        buffer = buffers
        if len(buffer) > 0:
        #for buffer in buffers:
            if len(buffer) < timestamp_size or (len(buffer) - timestamp_size) % sample_size != 0:
                raise ValueError(f"Invalid buffer length {len(buffer)}. "
                                 f"Expected timestamp + multiples of sample size {sample_size}.")

            # Extract the 8-byte timestamp
            timestamp = struct.unpack("<Q", buffer[:timestamp_size])[0]
            timestamp2 = struct.unpack("<Q", buffer[timestamp_size:2*timestamp_size])[0]

            # Calculate the number of samples in the buffer
            num_samples = (len(buffer) - 2 * timestamp_size) // sample_size

            # Extract and unpack each sample
            for i in range(num_samples):
                offset = 2 * timestamp_size + i * sample_size
                adc_value, delta_r, lp = struct.unpack("<f f f", buffer[offset: offset + sample_size])
                all_samples.append((timestamp, adc_value, delta_r, lp))

        return all_samples

if __name__ == "__main__":
    print("run main...")
    # adc_cfg = ADCDriverConfig(1000, 5, 1, 2, 1, 0, 1)
    # config = MicrostrainConfig(1000000, 16, 250, 12, 1000.0, 0.1, 0.99, 1.0, adc_cfg)
    #
    # handler = MicrostrainHandler()
    # # Serialize and Deserialize to Bytes
    # serialized = handler.serialize(config)
    # print("Serialized:", serialized)
    #
    # deserialized = handler.deserialize(serialized)
    # print("Deserialized:", deserialized.__dict__)
    # print("ADC Config:", deserialized.adc_config.__dict__)
    #
    # # Save to JSON and Load from JSON
    # config.save_to_json("microstrain_config.json")
    # loaded_config = MicrostrainConfig.load_from_json("microstrain_config.json")
    # print("Loaded from JSON:", loaded_config.__dict__)
    # print("Loaded ADC Config:", loaded_config.adc_config.__dict__)