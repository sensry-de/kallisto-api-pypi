# KallistoAPI  Python Library

**KallistoAPI** is a Python library for interacting with Kallisto sensor nodes over BLE (Bluetooth Low Energy). It provides easy access to device information, time synchronization, and readings from a wide range of environmental and motion sensors.

This library is designed for developers and researchers who want to integrate Kallisto sensor data into Python applications with minimal setup.

## Features

- Connect to Kallisto sensor nodes via BLE
- Read and update device time
- Access a variety of sensor modules including temperature, humidity, accelerometer, gyrometer, light, pressure, gas sensors, and more

## Installation

```bash
pip install kallistoapi
```

## Quick Start

Here’s a simple example showing how to connect to a Kallisto device, and get the accelerometer values:

```python
from time import sleep
from kallistoapi.kallisto_manager import KallistoManager

import argparse

parser = argparse.ArgumentParser(description="Connect to a BLE device using KallistoSensorsManager")
parser.add_argument(
    "-m", "--mac",
    help=f"BLE MAC address"
)

args = parser.parse_args()
mac_address = args.mac

kallisto = KallistoManager()

if not kallisto.connect(mac_address):
    print("Failed to connect to Kallisto")
    exit(1)

modules = kallisto.discover_modules()
print("available modules")
for module in modules:
    print(f" - {module}")

accelerometer0 = kallisto.get_module("accelerometer", 0)

parameters = accelerometer0.parameters()
print(f"available parameters for {accelerometer0}")
for parameter, desc in parameters.items():
    print(f" - {parameter}: {desc}")

accelerometer0.configure("enable", True)
accelerometer0.configure("sample_rate", "200Hz")
accelerometer0.configure("sensitivity", "8g")
accelerometer0.apply_config()

def handle_accel(sender, data_array):
    value_list = accelerometer0.decode(data_array)
    print("handle_accel value_list {}".format(value_list))

accelerometer0.start_notify(handle_accel)

sleep(20)

accelerometer0.stop_notify()

kallisto.disconnect()

```

## Available Sensor Modules

Kallisto currently supports the following sensor modules:

### Motion & Orientation (IMU)
- `vibration`
- `magnetometer`
- `accelerometer`
- `gyrometer`

### Environmental / Air Quality
- `temperature`
- `light`
- `pressure`
- `humidity`
- `eco2`
- `bvoc`
- `iaq`

### ADC Sensors
- `pt100`

### Device & Power
- `fuel_gauge`
- `tx_power`
- `device_info`




