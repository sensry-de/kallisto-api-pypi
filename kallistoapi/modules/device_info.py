from kallistoapi.modules.base import ModuleBase


class DeviceInfo(ModuleBase):

    def __init__(self, device):
        ModuleBase.__init__(self, device, "device_info")

        # used by this service only
        self._manufacturer_uuid = "00002a29-0000-1000-8000-00805f9b34fb"
        self._software_revision_uuid = "00002a28-0000-1000-8000-00805f9b34fb"
        self._hardware_revision_uuid = "00002a27-0000-1000-8000-00805f9b34fb"
        self._firmware_revision_uuid = "00002a26-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        return "0000180a-0000-1000-8000-00805f9b34fb"

    @classmethod
    def identity_uuid(cls):
        return "00002a29-0000-1000-8000-00805f9b34fb"

    ## ----------------------------------------------------
    ## special functions of this service

    def manufacturer_name(self):
        b_data = self.read(self._manufacturer_uuid)
        return b_data.decode("utf-8")

    def software_revision_name(self):
        b_data = self.read(self._software_revision_uuid)
        return b_data.decode("utf-8")

    def hardware_revision_name(self):
        b_data = self.read(self._hardware_revision_uuid)
        return b_data.decode("utf-8")

    def firmware_revision_name(self):
        b_data = self.read(self._firmware_revision_uuid)
        return b_data.decode("utf-8")
