import threading

from bleak import BleakClient, BleakScanner
import asyncio
# from pydbus import SystemBus

class BluetoothGatt:
    def __init__(self):
        self._client = None
        self._mac = "none"

        # bleak runs in async, we need to have a way to run the loop in parallel to pythons
        # sync calls. so we let the loop run in a thread
        self._bleak_loop_thread = None
        self._bleak_client_loop = None
        self._bleak_loop_thread_started = threading.Event()
        self._start_bleak_loop_thread()

        self.context = None
        self.notify_dict = {}
        self.service_handlers = {}

        self.disconnect_handler = None

    def connect(self, mac_address: str, disconnect_callback=None):
    # if self.is_device_connected(mac_address):
    #            print(f"Device {mac_address} is already connected")
    #        return False

        if self.is_connected():
            if mac_address == self._mac:
                return True
            print(f"disconnecting from {self._mac}")
            self.disconnect()

        self._mac = mac_address

        self.disconnect_handler = disconnect_callback
        if not self._await_bleak_loop(self._connect(self._mac), 60):
            self.disconnect_handler = None
            print("connection timed out")
            return False
        self._discover_services()
        return True

    def disconnect(self):
        return self._await_bleak_loop(self._disconnect())

#    def is_device_connected(self, mac_address):
#        dbus_path = "/org/bluez/hci0/dev_" + mac_address.replace(":", "_")
#        bus = SystemBus()
#        mngr = bus.get("org.bluez", "/")
#        objects = mngr.GetManagedObjects()
#        device = objects.get(dbus_path, {}).get("org.bluez.Device1")
#        return device.get("Connected", False) if device else False
#
    def scan_for_devices(self):
        return self._await_bleak_loop(self._scan_for_devices())

    def detect_services(self):
        return self._await_bleak_loop(self._detect_services())

    def read_gatt_characteristics(self, characteristic_uuid):
        return self._await_bleak_loop(self._read_gatt_characteristics(characteristic_uuid))

    def get_service(self, characteristic_uuid):
        return self._client.services.get_service(characteristic_uuid)

    def start_gatt_notify(self, characteristic_uuid, notify_cb):
        return self._await_bleak_loop(self._start_gatt_notify(characteristic_uuid, notify_cb))

    def stop_gatt_notify(self, characteristic_uuid):
        return self._await_bleak_loop(self._stop_gatt_notify(characteristic_uuid))

    def write_gatt_characteristics(self, characteristic_uuid, data):
        return self._await_bleak_loop(self._write_gatt_characteristics(characteristic_uuid, data))

    def get_mac_address(self):
        return self._mac

    def is_connected(self):
        if self._client is None:
            return False
        return self._client.is_connected

    def get_uuid_from_handle(self, handle):
        if handle in self.service_handlers:
            return self.service_handlers[handle]
        else:
            return None

    ###############################
    # internal functions
    def _discover_services(self):
        for service in self._client.services:
            for characteristic in service.characteristics:
                self.service_handlers[characteristic.handle] = characteristic.uuid

    ###############################
    # async functions

    def _start_bleak_loop_thread(self):
        self._bleak_thread = threading.Thread(target=self._run_bleak_loop_thread)
        self._bleak_thread.daemon = True
        self._bleak_thread.start()
        # finally wait for the thread to have properly started
        self._bleak_loop_thread_started.wait()

    def _run_bleak_loop_thread(self):
        self._bleak_client_loop = asyncio.new_event_loop()
        self._bleak_loop_thread_started.set()
        self._bleak_client_loop.run_forever()

    def _await_bleak_loop(self, coro, timeout=10):
        future = asyncio.run_coroutine_threadsafe(coro, self._bleak_client_loop)
        try:
            return future.result(timeout)
        except asyncio.TimeoutError:
            print("Timeout waiting for bluetooth operation")
            return False

    async def _connect(self, mac_address):
        self._client = BleakClient(mac_address, disconnected_callback=self._disconnect_handler)
        if self._client is None:
            print(f"Failed to create client for {mac_address}")
            return False
        try:
            await self._client.connect()
        except Exception as e:
            print(f"Failed to connect to {mac_address}: {e}")
            return False
        if self._client.is_connected:
            print(f"Connected to {mac_address}")
            self._mac = mac_address
            return True
        else:
            self._mac = "none"
            print(f"Failed to connect to {mac_address}")
            return False

    async def _disconnect(self):
        if self._client:
            await self._client.disconnect()
            print(f"Disconnected successfully")
        else:
            print("No device to disconnect")

    def _disconnect_handler(self, client):
        print(f"Device disconnected: {self._mac}")
        if self.disconnect_handler is not None:
            self.disconnect_handler()
        return

    @staticmethod
    async def _scan_for_devices():
        devices = await BleakScanner.discover(timeout=3.0)
#        for device in devices:
#            print(f"Device found: {device.name} ({device.address})")
        return devices

    async def _detect_services(self):
        if not self.is_connected():
            print("Not connected")
            return {}

        # This implicitly fetches services
        services = self._client.services

        s = {}
        for service in services:
            s[service.uuid] = {}
            for char in service.characteristics:
                s[service.uuid][char.uuid] = {
                    "uuid": char.uuid,
                    "description": char.description,
                    "properties": char.properties,
                }
        return s

    # characteristics
    async def _read_gatt_characteristics(self, characteristic_uuid):
        return await self._client.read_gatt_char(characteristic_uuid)

    async def _write_gatt_characteristics(self, characteristic_uuid, data):
        return await self._client.write_gatt_char(characteristic_uuid, data)

    async def _get_mtu(self):
        return await self._client._acquire_mtu()

    # notification
    def _notify_callback(self, sender, data):
        print(f"{sender}: {data}")
        self.context.notify_dict.update({"uuid": data})

    async def _start_gatt_notify(self, characteristic_uuid, notify_cb):
        return await self._client.start_notify(characteristic_uuid, notify_cb)

    async def _stop_gatt_notify(self, characteristic_uuid):
        return await self._client.stop_notify(characteristic_uuid)
