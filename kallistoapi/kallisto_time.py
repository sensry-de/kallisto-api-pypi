#!/bin/python3

import asyncio
import logging
from datetime import datetime, timezone
from bleak import BleakClient, BleakGATTCharacteristic

SENSRY_SERVICE_UUID = "00002000-702b-69b5-b243-d6094a2b0e24"

# CTS
CURRENT_TIME_SERVICE_UUID = "1805"
CURRENT_TIME_SERVICE_CURRENT_TIME_UUID = "2A2B"

class TimeService:
    def update_time(self, manager):
        try:
            cts = manager.get_service(CURRENT_TIME_SERVICE_UUID)
        except StopIteration:
            logger.error("[%s] CTS service is unavailable" % self.mac_address)

        if cts is not None:
            current_time = cts.get_characteristic(CURRENT_TIME_SERVICE_CURRENT_TIME_UUID)

            now = datetime.now(tz=timezone.utc)
            logger.info(now)

            config = now.year.to_bytes(2, "little")
            config += now.month.to_bytes(1, "little")
            config += now.day.to_bytes(1, "little")
            config += now.hour.to_bytes(1, "little")
            config += now.minute.to_bytes(1, "little")
            config += now.second.to_bytes(1, "little")
            config += b'\x00'  # day of the week (undefined)
            config += b'\x00'  # fractions of 256th of a second (undefined)
            config += b'\x01'  # Adjust reason: manual time update

            manager.write_gatt_characteristics(current_time, config)


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

    def read_time(self, manager):
        try:
            cts = manager.get_service(CURRENT_TIME_SERVICE_UUID)
        except StopIteration:
            logger.error("[%s] CTS service is unavailable" % self.mac_address)

        if cts is not None:
            current_time = cts.get_characteristic(CURRENT_TIME_SERVICE_CURRENT_TIME_UUID)
            readValue = manager.read_gatt_characteristics(current_time)

            timestamp = self.timestamp_from_bytearray(readValue)
            return timestamp

            # now = datetime.now(tz=timezone.utc)
            # logger.info(now)
            #
            # config = now.year.to_bytes(2, "little")
            # config += now.month.to_bytes(1, "little")
            # config += now.day.to_bytes(1, "little")
            # config += now.hour.to_bytes(1, "little")
            # config += now.minute.to_bytes(1, "little")
            # config += now.second.to_bytes(1, "little")
            # config += b'\x00'  # day of the week (undefined)
            # config += b'\x00'  # fractions of 256th of a second (undefined)
            # config += b'\x01'  # Adjust reason: manual time update
            #
            # await client.write_gatt_char(current_time, config)
logging.basicConfig()
logger = logging.getLogger("Kallisto")
logger.setLevel(logging.WARNING)

