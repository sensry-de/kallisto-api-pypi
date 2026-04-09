

class ModuleBase:


    def __init__(self, device, name):
        self._device = device
        self._name = name
        self._idx = -1
        #
        self._notify_callback = None
        self._notify_data = []
        #
        self.parameter_func = {}

    def __str__(self):
        return f"{self._name}-{self._idx}"

    def get_type(self):
        return self._name

    def name(self):
        return f"{self._name}-{self._idx}"

    def set_idx(self, idx):
        self._idx = idx

    def is_type(self, module_class):
        base_classes = type(self).__bases__
        for base_class in base_classes:
            if base_class.__name__ == module_class:
                return True
        return False


    def read(self, characteristic_uuid):
        data_bytes = self._device.read_gatt_characteristics(characteristic_uuid)
        return data_bytes

    def write(self, characteristic_uuid, data_bytes):
        self._device.write_gatt_characteristics(characteristic_uuid, data_bytes)

    def register(self, key, _read, _write, description="" ):
        self.parameter_func[key] = {"read": _read, "write": _write, "description": description}
        return

    def parameters(self):
        ret = {}
        for key in self.parameter_func:
            ret[key] = self.parameter_func[key]["description"]
        return ret

    def configure(self, key, value):
        if key not in self.parameter_func:
            raise NotImplementedError()

        func = self.parameter_func[key]["write"]
        func(value)
        return

    def get(self, key):
        if key not in self.parameter_func:
            raise NotImplementedError()

        func = self.parameter_func[key]["read"]
        return func()

    def start_notify(self, notify_callback=None):
        print(f"Start notify on uuid: {self.data_uuid()}")
        if notify_callback is None:
            print("using default notify callback")
            notify_callback = self.__notify_callback

        self._device.start_gatt_notify(self.data_uuid(), notify_callback)

    def stop_notify(self):
        print(f"Stop notify on uuid: {self.data_uuid()}")
        self._device.stop_gatt_notify(self.data_uuid())
        print(self._notify_data)

    def __notify_callback(self, sender, data):
        uuid = f"{sender.uuid}"
        print(f"{uuid}: {data}")
        self._notify_data.append({uuid: data})

    ## ----------------------------------------------------
    ## used to identify this service

    @classmethod
    def service_uuid(cls):
        raise NotImplementedError()


    @classmethod
    def identity_uuid(cls):
        # by default, we use the data uuid
        return cls.data_uuid()

    ## ----------------------------------------------------
    ## used to start / stop notifications

    @classmethod
    def data_uuid(cls):
        raise NotImplementedError()
