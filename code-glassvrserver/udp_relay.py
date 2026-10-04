#relay to get udp packets from the driver

#use ur.get_relay_dict() to get the packets!

import struct
import time
import threading
import win32file
import win32pipe
import pywintypes
import settings as settings_core

# Keyed by device or port: { "hmd": {"P": {...}, "R": {...}}, ... }
packets = {}
_packets_lock = threading.Lock()

_active_threads = {}
_threads_lock = threading.Lock()

def parse_packet(prefix: str, raw_data: bytes):
    if not raw_data:
        return None

    try:
        match prefix:
            case 'P':
                if len(raw_data) >= 24:
                    x, y, z = struct.unpack('3d', raw_data[:24])
                    return {"x": x, "y": y, "z": z}

            case 'R':
                if len(raw_data) >= 32:
                    w, x, y, z = struct.unpack('4d', raw_data[:32])
                    return {"w": w, "x": x, "y": y, "z": z}

            case 'I':
                if len(raw_data) >= 76:
                    unpacked = struct.unpack('12?8d', raw_data[:76])
                    return {
                        "btn": unpacked[0:5],
                        "cap": unpacked[5:12],
                        "joy": (unpacked[12], unpacked[13]),
                        "touch": (unpacked[14], unpacked[15]),
                        "trigger": unpacked[16],
                        "force": unpacked[17:20]
                    }

            case 'S':
                if len(raw_data) >= 200:
                    unpacked = struct.unpack('25d', raw_data[:200])
                    return {
                        "flexions": unpacked[:20],
                        "splays": unpacked[20:]
                    }

            case 'E':
                if len(raw_data) >= 1:
                    reset_flag, = struct.unpack('?', raw_data[:1])
                    return {"reset": reset_flag}

            case _:
                return None

    except struct.error:
        pass

    return None

def pipe_listener_worker(device: str):
    while True:
        settings = settings_core.get_settings()
        port = settings.get(f"{device} port")

        if not port:
            time.sleep(1.0)
            continue

        pipe_name = f"\\\\.\\pipe\\UDP_RELAY_{port}"

        try:
            win32pipe.WaitNamedPipe(pipe_name, 1000)
        except pywintypes.error:
            time.sleep(1.0)
            continue

        try:
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
        except pywintypes.error:
            time.sleep(1.0)
            continue

        last_check_time = time.time()

        while True:
            try:
                _, avail, _ = win32pipe.PeekNamedPipe(handle, 0)

                if avail > 0:
                    _, data = win32file.ReadFile(handle, 1024)
                    if data:
                        prefix = data[0:1].decode('ascii', errors='ignore')
                        payload = data[1:]
                        parsed = parse_packet(prefix, payload)

                        with _packets_lock:
                            if device not in packets:
                                packets[device] = {}
                            packets[device][prefix] = parsed
                else:
                    current_time = time.time()
                    if current_time - last_check_time > 1.0:
                        last_check_time = current_time
                        new_settings = settings_core.get_settings()
                        new_port = new_settings.get(f"{device} port")

                        if new_port and new_port != port:
                            break

                    time.sleep(0.005)

            except pywintypes.error as e:
                if e.args[0] in [109, 233]:
                    break
                time.sleep(0.001)

        try:
            win32file.CloseHandle(handle)
        except pywintypes.error:
            pass

def enable_device(device: str):
    with _threads_lock:
        if device in _active_threads and _active_threads[device].is_alive():
            return

        t = threading.Thread(
            target=pipe_listener_worker,
            args=(device,),
            daemon=True,
            name=f"UDP_Relay_{device}"
        )
        _active_threads[device] = t
        t.start()

def start():
    settings = settings_core.get_settings()

    enable_device("hmd")
    enable_device("cr")
    enable_device("cl")

    trackers_num = settings.get("trackers num", 0)
    for n in range(trackers_num):
        enable_device(f"{n}tracker")

def get_relay_dict() -> dict:
    with _packets_lock:
        return {dev: dict(prefixes) for dev, prefixes in packets.items()}


def get_latest_packet(device: str, prefix: str):
    with _packets_lock:
        return packets.get(device, {}).get(prefix)

start()