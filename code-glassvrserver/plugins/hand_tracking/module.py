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

def pos_mode():
    return el.label({"text": ""})

def rot_mode():
    return el.label({"text": ""})

def loop(data):
    global px, py, pz, rx, ry, rz, rw, input, skeletal

    stop_event = data.get("stop_event")

    if device is None:
        return

    prefix = device # "cr" or "cl"

    while not stop_event.is_set():
        settings = se.get_settings()

        # pos and rot ///
        try:
            t = ht.get_hand_world_transform(device)
            px, py, pz = t["pos x"], t["pos y"], t["pos z"]
            rx, ry, rz, rw = t["rot x"], t["rot y"], t["rot z"], t["rot w"]
        except Exception:
            pass

        # bindings for trigger and grip
        trigger = sdl.eval_binding(settings.get(f"{prefix}_trigger", ""))
        raw_input = sdl.eval_binding(settings.get(f"{prefix}_grip", ""))
        grip_pull = min(1.0, raw_input * 2.0)
        grip_force = max(0.0, (raw_input - 0.5) / 0.5)

        # skeletal processing ///
        fingers = ["thumb", "index", "middle", "ring", "pinky"]

        if settings.get("curl", True):
            flexion = list(ht.hand_data["l flexion"] if prefix == "cl" else ht.hand_data["r flexion"])
            for i, finger in enumerate(fingers):
                val = sdl.eval_binding(settings.get(f"{prefix}_{finger}", ""))
                if val > 0.01:
                    flexion[i * 4] = val

            if settings.get("index=trigger", False):
                if trigger < flexion[4]:
                    trigger = -1 + (flexion[4] * 3)

            if settings.get("other=grip", False):
                highest = max(flexion[8], flexion[12], flexion[16])
                if grip_pull < highest - 0.7:
                    grip_pull = highest - 0.7
                    grip_force = max(0.0, (grip_pull - 0.5) / 0.5)
        else:
            flexion = [0.0] * 20
            for i, finger in enumerate(fingers):
                val = sdl.eval_binding(settings.get(f"{prefix}_{finger}", ""))
                if val > 0.01:
                    flexion[i * 4] = val

        if settings.get("splay", True):
            splays_5 = list(ht.hand_data["l splay"] if prefix == "cl" else ht.hand_data["r splay"])
        else:
            splays_5 = [0.0] * 5

        # update skeletal state
        if prefix == "cl":
            skeletal["l flexion"] = flexion
            skeletal["l splay"]   = splays_5
        elif prefix == "cr":
            skeletal["r flexion"] = flexion
            skeletal["r splay"]   = splays_5

        # update triggers, grips, and buttons for all controllers
        trigger_btn = trigger > 0.95
        grip_btn = grip_pull > 0.95 or grip_force > 0.95

        # index
        input["index"]["trigger"] = float(trigger)
        input["index"]["trigger_btn"] = bool(trigger_btn)
        input["index"]["grip_pull"] = float(grip_pull)
        input["index"]["grip_force"] = float(grip_force)
        input["index"]["grip_cap"] = grip_pull > 0.01

        # frame
        input["frame"]["trigger"] = float(trigger)
        input["frame"]["trigger_btn"] = bool(trigger_btn)
        input["frame"]["grip"] = float(grip_pull)
        input["frame"]["grip_btn"] = bool(grip_btn)
        input["frame"]["grip_cap"] = grip_pull > 0.01

        # vive
        input["vive"]["trigger"] = float(trigger)
        input["vive"]["trigger_btn"] = bool(trigger_btn)
        input["vive"]["grip_btn"] = bool(grip_btn)

        # touch
        input["touch"]["trigger"] = float(trigger)
        input["touch"]["trigger_cap"] = trigger > 0.01
        input["touch"]["grip"] = float(grip_pull)

        time.sleep(0.001)