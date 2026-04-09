import subprocess
import re
import os
import time
from pathlib import Path
from pip._internal.exceptions import CommandError

expected_version = "mcumgr 0.0.0-dev"


def _execute_mcumgr_command(args):
    # Command to execute mcumgr binary with arguments
    command = ['mcumgr'] + args
    print("Executing: " + " ".join(command))

    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        # Check for errors
        if process.returncode != 0:
            print(f"Error executing command: {stderr}")
            return [None, None]

        error_lines = stderr.splitlines()
        for line in error_lines:
            print(f"Error: {line}")

        # Parse the output for details
        # For demonstration purposes, we'll split the output by lines
        output_lines = stdout.splitlines()

        # Process each line as needed
        for line in output_lines:
            # Example: Print each line
            print(line)

        # Return the parsed output
        return [output_lines, error_lines]

    except FileNotFoundError:
        print("Error: mcumgr binary not found.")
        return [None, None]


def _exec(args, pattern):
    [output, errors] = _execute_mcumgr_command(args)
    if output is None:
        raise CommandError("mcumgr - return code invalid")

    if pattern is None:
        return output

    for line in output:
        matches = re.findall(pattern, line)
        if matches:
            return matches[0]
    return None


def _get_std_args(device_name, extra_args=None):
    if extra_args is None:
        extra_args = []
    return ['--conntype', 'ble', '--connstring', 'peer_name=' + device_name] + extra_args


def _mcumgr_get_info(device_name):
    args = _get_std_args(device_name, ['image', 'list'])
    res = _exec(args, None)
    if res[0] != 'Images:':
        raise CommandError("invalid return - expected 'Images:' but got " + res[0])
    if len(res) == 12:
        info = {
            "current": {
                "version": res[2].strip().split(":")[1].strip(),
                "flags": res[4].strip().split(":")[1].strip(),
                "hash": res[5].strip().split(":")[1].strip()
            },
            "next": {
                "version": res[7].strip().split(":")[1].strip(),
                "flags": res[9].strip().split(":")[1].strip(),
                "hash": res[10].strip().split(":")[1].strip()
            }
        }
        print(info)
        return info

    if len(res) == 7:
        if res[6] == 'Split status: N/A (0)':
            info = {
                "current": {
                    "version": res[2].strip().split(":")[1].strip(),
                    "flags": res[4].strip().split(":")[1].strip(),
                    "hash": res[5].strip().split(":")[1].strip()
                },
                "next": {
                    "version": "",
                    "flags": "",
                    "hash": ""
                }
            }
            print(info)
            return info

    raise CommandError("invalid return - format not expected")
    return None


def _mcumgr_upload(device_name, image_name):
    print(f"uploading image [{image_name}] to device {device_name}, this may take several minutes, please be patient...")
    args = _get_std_args(device_name, ['image', 'upload', image_name])
    res = _exec(args, "Done")
    if res is None:
        raise CommandError("failed to finish upload for " + device_name)


def _mcumgr_activate_test(device_name, hash):
    args = _get_std_args(device_name, ['image', 'test', hash])
    res = _exec(args, None)
    if res is None:
        raise CommandError("failed to finish upload for " + device_name)


def _mcumgr_reset_device(device_name):
    args = _get_std_args(device_name, ['reset'])
    res = _exec(args, "Done")
    if res is None:
        raise CommandError("failed to finish upload for " + device_name)


def _mcumgr_confirm(device_name, hash):
    args = _get_std_args(device_name, ['image', 'confirm', hash])
    res = _exec(args, None)
    if res is None:
        raise CommandError("failed to confirm hash " + hash + " for " + device_name)


def _mcumgr_wait_for_back_online(device_name):
    start_time = time.time()
    while True:
        try:
            _mcumgr_get_info(device_name)
            break
        except CommandError:
            print("still offline")

        if time.time() - start_time > 60:
            raise(EOFError("timeout -- device did not came back online " + device_name))
    print("device online " + device_name)
    return


def mcumgr_init():

    # Example: Execute mcumgr with arguments
    args = ['version']  # Example arguments
    res = _exec(args, expected_version)
    if res is None:
        raise FileNotFoundError("invalid mcumgr version")


def mcumgr_update(device_name, image_name, expected_version):
    file_path = Path(image_name)
    if not os.path.exists(file_path):
        raise FileExistsError("file is not accessible or does not exist " + image_name)

    info = _mcumgr_get_info(device_name)

    if info["current"]["version"] != expected_version:

        if info["next"]["version"] != expected_version and info["current"]["version"] != expected_version:
            # we must not load the same image in both slots !!!
            _mcumgr_upload(device_name, image_name)

        info = _mcumgr_get_info(device_name)
        if info["next"]["version"] != expected_version:
            raise IOError("expected firmware was not uploaded, expected " + expected_version + " but got " + info["next"]["version"])

        _mcumgr_activate_test(device_name, info["next"]["hash"])

        info = _mcumgr_get_info(device_name)
        if info["next"]["flags"] != "pending":
            raise IOError("could not set test mode")

        _mcumgr_reset_device(device_name)
        _mcumgr_wait_for_back_online(device_name)

    info = _mcumgr_get_info(device_name)
    if info["current"]["version"] != expected_version:
        raise IOError("expected firmware is not active")

    if info["current"]["flags"] == "active":
        _mcumgr_confirm(device_name, info["current"]["hash"])

    info = _mcumgr_get_info(device_name)
    if info["current"]["version"] != expected_version:
        raise IOError("expected firmware is not active")
    if info["current"]["flags"] != "active confirmed":
        raise IOError("actually new firmware is not confirmed")

    version = info["current"]["version"]
    state = info["current"]["flags"]
    print(f"firmware of device {device_name} is {version}, state is {state} -- success")
