
def get_conf_uuid(name):
    uuid_map = {
        "log_global_conf": "00002021-702b-69b5-b243-d6094a2b0e24",
        "log_start_cond": "00002022-702b-69b5-b243-d6094a2b0e24",
        "log_mem_ctrl": "00002024-702b-69b5-b243-d6094a2b0e24",
        "log_mem_stat": "00002025-702b-69b5-b243-d6094a2b0e24",
        "log_temp_dump": "00002101-702b-69b5-b243-d6094a2b0e24",
        "log_temp_conf": "00002104-702b-69b5-b243-d6094a2b0e24",
        "log_vibration_dump": "00002111-702b-69b5-b243-d6094a2b0e24",
        "log_vibration_conf": "00002114-702b-69b5-b243-d6094a2b0e24",
        "vibration_conf": "00001022-702b-69b5-b243-d6094a2b0e24"
    }
    if name not in uuid_map:
        raise Exception("unknown requested UUID")

    return uuid_map[name]


def get_compare_value(name):
    uuid_map = {
        "log_global_disable": bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
        "log_global_enable": bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
        "log_vibration_disable": bytearray([0x00]),
        "log_vibration_enable": bytearray([0x01]),
        "log_vibration_dump": bytearray([0x02]),
        "log_manual_trigger": bytearray([0x00]),
        "log_timestamp_trigger": bytearray([0x01, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, ]),

    }
    if name not in uuid_map:
        raise Exception("unknown requested UUID")

    return uuid_map[name]


def log_dumping_callback(sender, data):
    print(f"{sender}: {data}")


def log_vibration_callback(context, sender, data):
    print(f"{sender}: {data}")
    context.vibration_dump = data

def kallisto_connect(context, mac_address):
    if mac_address == "default":
        mac_address = context.default_mac

    if context.ble_manager.connect(mac_address):
        return True
    context.ble_manager.scan_for_devices()

    if context.ble_manager.connect(mac_address):
        return True

    print(f"failed again to connect device {mac_address}")
    return False
