#unfinished
#this should estimate hip position with 3 points
#cuz vrc requires a hip tracker and refuses to work with only 2
#and I3Llamas the standables guy ghosted me lol

import time

import elements as el
import controller_handler as sdl
import settings as se

pos_devices = ["tracker"]
rot_devices = ["tracker"]

title = "hip"

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
    return el.label({"text": f"{title} pos"})

def rot_mode():
    return el.label({"text": f"{title} rot"})

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        settings = se.get_settings()
        print(device)
        # print(sdl.eval_binding(settings["cr_trigger"]))
        time.sleep(0.01)