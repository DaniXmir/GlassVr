#this module only pulls data from "hand tracking.py"
import time

import elements as el
import controller_handler as sdl
import settings as se
from . import hand_tracking as ht

pos_devices = ["controller"]#, "tracker"]
rot_devices = ["controller"]#, "tracker"]
input_devices = ["controller"]
skeletal_devices = ["controller"]

title = "hand tracking"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 0.0

input = {
    "a": False, "b": False, "system": False,
    "joy_btn": False, "trigger_btn": False,
    "a_cap": False, "b_cap": False, "system_cap": False,
    "joy_cap": False, "trigger_cap": False,
    "touch_cap": False, "grip_cap": False,
    "joy_x": 0.0, "joy_y": 0.0,
    "touch_x": 0.0, "touch_y": 0.0,
    "trigger": 0.0, "touch_force": 0.0,
    "grip_pull": 0.0, "grip_force": 0.0,
}

skeletal = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
}

def pos_mode():
    return el.label({"text": f"{title} pos"})

def rot_mode():
    return el.label({"text": f"{title} rot"})

def loop(data):
    global px, py, pz, rx, ry, rz, rw, input, skeletal

    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        t = ht.get_hand_world_transform(device)
        px, py, pz = t["pos x"], t["pos y"], t["pos z"]
        rx, ry, rz, rw = t["rot x"], t["rot y"], t["rot z"], t["rot w"]

        if device == "cl":
            skeletal["l flexion"] = ht.hand_data["l flexion"]
            skeletal["l splay"]   = ht.hand_data["l splay"]
            input["trigger"]      = ht.hand_data["l flexion"][4]
            
        elif device == "cr":
            skeletal["r flexion"] = ht.hand_data["r flexion"]
            skeletal["r splay"]   = ht.hand_data["r splay"]
            input["trigger"]      = ht.hand_data["r flexion"][4]

        time.sleep(0.001)