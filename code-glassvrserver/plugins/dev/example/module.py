#example module!
#note: "mode" and "module" used interchangeably

#some modules dont send data and just add an entry for the driver to read, 
#i can theme ghost modules only add an entry for the driver to read

import time

import elements as el
import settings as se

import controller_handler as sdl
import steamvr as svr

#what devies this module is compatible with
pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

#if it has input/skeletal data, if the module is only pos/rot (headsets trackers can also have buttons but i havent implemented that)
input_devices = []#["controller"]
skeletal_devices = []#["controller"]

#module title that shows up when selecting
title = "example"

#gets a value when activating the module, 
#internal names: hmd/cl-cr/0tracker-1tracker-etc...
device = None
#internal names: pos/rot
mode = None

#position and rotaion globals that get sent
px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 1.0

#input(temp), will get change later!
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

#fingers, only every forth value of flexion is actually used
#[0]thumb
#[4]index
#[8]middle
#[12]ring
#[16]pinky
#will change later to be per hand
skeletal = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
}

#pos/rot shows when the module is selected
def pos_mode():
    current_device = device #sometimes buggy, plz save device as local var
    current_mode = mode

    #dont write logic here, only ui for settings

    #bindable
    e_bind = el.bindable({
        "prefix" : current_device, #prefix
        "mapping" : "example bind", #action
    })

    e_spin = el.spinbox({
        "text" : "spin",
        "min" : -10,
        "max" : 10,
        "default" : se.get_settings().get(f"{current_device} example spin", 0),
        "func" : lambda value: se.update_setting(f"{current_device} example spin", value)
    })

    e_check = el.checkbox({
        "text" : "spin",
        "default" : se.get_settings().get(f"{current_device} example check", False),
        "func" : lambda value: se.update_setting(f"{current_device} example check", value)
    })

    pos_g = el.group(
        {
            "text": "example pos settings",
            "box": "v",
            "arr": [e_bind,e_spin,e_check],
        }
    )

    return pos_g

def rot_mode():
    current_device = device
    current_mode = mode
    return el.label({"text": f"{title} rot"})
#both is special, shows when either pos or rot is selected
def both_mode():
    current_device = device
    current_mode = mode
    return el.label({"text": f"{title} both"})

#runs 2 threads for pos/rot
#if your system updates 2 or more devices like hand tracking(2 controllers) or fbt(lots of trackers)
#make it run in a seperet thread and poll data to here, see hand tracking module
def loop(data):
    global px, py, pz, rx, ry, rz, rw, input, skeletal, device, mode

    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        #write your loop here!
        settings = se.get_settings()

        #reads the action of "{device}_example bind" from settings, bindables need "_" between prefix and mapping (prefix_mapping)
        px = sdl.eval_binding(settings.get(f"{device}_example bind","")) * 10 #live read the binded action
        #reads "{device} spin" from settings
        py = settings.get(f"{device} example spin", 0)
        #reads "{device} check" from settings
        if settings.get(f"{device} example check", False):
            pz = 0
        else:
            pz = 10

        #rx = 0.0
        #ry = 0.0
        #rz = 0.0
        #rw = 1.0

        #etc...
        time.sleep(0.01)