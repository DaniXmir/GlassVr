import time

import elements as el
import settings as se

import controller_handler as sdl
import steamvr as svr

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

input_devices = ["controller"]
skeletal_devices = ["controller"]

title = "serial"

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
    "index": {
        "a": False, "b": False, "system": False,
        "joy_btn": False, "trigger_btn": False,
        "a_cap": False, "b_cap": False, "system_cap": False,
        "joy_cap": False, "trigger_cap": False,
        "touch_cap": False, "grip_cap": False,
        "joy_x": 0.0, "joy_y": 0.0,
        "touch_x": 0.0, "touch_y": 0.0,
        "trigger": 0.0, "touch_force": 0.0,
        "grip_pull": 0.0, "grip_force": 0.0,
    },
    "frame": {
        "y_up": False, "y_up_cap": False,
        "a_down": False, "a_down_cap": False,
        "x_left": False, "x_left_cap": False,
        "b_right": False, "b_right_cap": False,
        "select": False, "select_cap": False,
        "bumper": False, "bumper_cap": False,
        "system": False, "system_cap": False,
        "trigger_btn": False, "trigger_cap": False,
        "grip_btn": False, "grip_cap": False,
        "joy_btn": False, "joy_cap": False,
        "trigger": 0.0, "grip": 0.0,
        "joy_x": 0.0, "joy_y": 0.0,
    },
    "vive": {
        "system": False,
        "grip_btn": False,
        "select": False,
        "trigger_btn": False,
        "touch_btn": False,
        "touch_cap": False,
        "trigger": 0.0,
        "touch_x": 0.0,
        "touch_y": 0.0,
    },
    "touch": {
        "system": False,
        "a_x": False, "a_x_cap": False,
        "b_y": False, "b_y_cap": False,
        "trigger_cap": False,
        "joy_btn": False, "joy_cap": False,
        "trigger": 0.0,
        "grip": 0.0,
        "joy_x": 0.0,
        "joy_y": 0.0,
    }
}

skeletal = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
}

def comm_lineedit(mode):
    current_device = device
    current_mode = mode

    if se.get_settings().get(f"{current_device} {current_mode} comm port", f"{current_device} {current_mode} comm port"):
        se.update_setting(f"{current_device} {current_mode} comm port", "COM9")

    le = el.lineedit({
        "text" : "comm port",
        "placeholder" : "COM9",
        "default" : se.get_settings().get(f"{current_device} {current_mode} comm port", f"{current_device} {current_mode} comm port"),
        "func" : lambda value: se.update_setting(f"{current_device} {current_mode} comm port", value)
    })

    return le

def pos_mode():
    return comm_lineedit("pos")

def rot_mode():
    return comm_lineedit("rot")

def input_mode():
    return comm_lineedit("input")

def skeletal_mode():
    return comm_lineedit("skeletal")

def both_mode():
    return el.label({"text": " "})

def loop(data):
    global px, py, pz, rx, ry, rz, rw, input, skeletal, device, mode

    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        #write your loop here!
        time.sleep(0.01)