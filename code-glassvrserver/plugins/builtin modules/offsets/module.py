#ghost module, doesnt send data
import time

import elements as el
import controller_handler as sdl
import settings as se

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

title = "offsets"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 0.0

def pos_mode():
    return el.label({"text": f" "})


def rot_mode():
    return el.label({"text": f" "})


def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        time.sleep(0.01)