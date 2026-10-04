import time

import elements as el
import settings as se

import controller_handler as sdl
import steamvr as svr

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

input_devices = []#["controller"]
skeletal_devices = []#["controller"]

title = "template"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 1.0

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
    current_device = device
    current_mode = mode

    return el.label({"text": f"{title} pos"})

def rot_mode():
    current_device = device
    current_mode = mode
    return el.label({"text": f"{title} rot"})

def both_mode():
    current_device = device
    current_mode = mode
    return el.label({"text": f"{title} both"})

def loop(data):
    global px, py, pz, rx, ry, rz, rw, input, skeletal, device, mode

    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        #write your loop here!
        time.sleep(0.01)