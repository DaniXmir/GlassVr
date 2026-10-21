# sends sdl inputs received by the python side
import time

import elements as el
import controller_handler as sdl
import settings as se

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

input_devices = ["controller"]
skeletal_devices = ["controller"]

title = "app (named pipe)"

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

CLICK_AT = 0.95
FINGERS = ["thumb", "index", "middle", "ring", "pinky"]
skeletal = {
    "l flexion": [0.0] * 20, "l splay": [0.0] * 5,
    "r flexion": [0.0] * 20, "r splay": [0.0] * 5,
}

def _disable_pipe_checkbox(slot):
    d = device
    key = f"{d} disable pipe {slot}"
    c = el.checkbox({
        "type": "checkbox",
        "text": f"disable internal pipe",
        "default": se.get_settings().get(key, False),
        "func": lambda: se.update_setting(key, c.findChildren(el.QCheckBox)[0].isChecked())
    })
    return c

def pos_mode():
    return _disable_pipe_checkbox("pos")

def rot_mode():
    return _disable_pipe_checkbox("rot")

def input_mode():
    return _disable_pipe_checkbox("input")

def skeletal_mode():
    return _disable_pipe_checkbox("skeletal")

def both_mode():
    return el.label({"text": " "})

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device_name = data.get("device")
    stop_event = data.get("stop_event")

    if device_name is None:
        return

    prefix = device_name
    side = "l" if prefix == "cl" else "r"

    while not stop_event.is_set():
        settings = se.get_settings()
        con_type = settings.get("con type", "touch")

        def eval_act(con_subtype, action, default=False):
            keys = [
                f"{prefix}_{con_subtype}_{action}",
                f"{prefix}_{action}",
            ]
            for k in keys:
                b = settings.get(k, "")
                if b:
                    val = sdl.eval_binding(b)
                    if isinstance(default, bool):
                        return val > 0.5
                    return float(val)
            return default

        if con_type == "index":
            ix = input["index"]

            joy_x = eval_act("index", "joy_right", 0.0) - eval_act("index", "joy_left", 0.0)
            joy_y = eval_act("index", "joy_up", 0.0) - eval_act("index", "joy_down", 0.0)
            touch_x = eval_act("index", "touch_right", 0.0) - eval_act("index", "touch_left", 0.0)
            touch_y = eval_act("index", "touch_up", 0.0) - eval_act("index", "touch_down", 0.0)

            touchmod = eval_act("index", "touchmod", False)
            if touchmod:
                touch_x = max(-1.0, min(1.0, touch_x + joy_x))
                touch_y = max(-1.0, min(1.0, touch_y + joy_y))
                joy_x = 0.0
                joy_y = 0.0

            ix["joy_x"] = joy_x
            ix["joy_y"] = joy_y
            ix["touch_x"] = touch_x
            ix["touch_y"] = touch_y
            ix["trigger"] = eval_act("index", "trigger", 0.0)
            ix["touch_force"] = eval_act("index", "touch_click", 0.0)
            ix["grip_pull"] = eval_act("index", "grip", 0.0)
            ix["grip_force"] = ix["grip_pull"]

            ix["a"] = eval_act("index", "a", False)
            ix["b"] = eval_act("index", "b", False)
            ix["system"] = eval_act("index", "system", False)
            joy_click = eval_act("index", "joy_click", False)
            if touchmod:
                if joy_click:
                    ix["touch_force"] = 1.0
                joy_click = False
            ix["joy_btn"] = joy_click
            ix["trigger_btn"] = ix["trigger"] >= CLICK_AT

            ix["a_cap"] = ix["a"]
            ix["b_cap"] = ix["b"]
            ix["system_cap"] = ix["system"]
            ix["joy_cap"] = ix["joy_btn"]
            ix["trigger_cap"] = ix["trigger_btn"] or (ix["trigger"] > 0.05)
            ix["touch_cap"] = (ix["touch_x"] != 0.0) or (ix["touch_y"] != 0.0) or (ix["touch_force"] > 0.05)
            ix["grip_cap"] = (ix["grip_pull"] > 0.05)

        elif con_type == "frame":
            is_right = (prefix == "cr")
            fr = input["frame"]

            if is_right:
                fr["a_down"] = eval_act("frame", "a", False)
                fr["b_right"] = eval_act("frame", "b", False)
                fr["x_left"] = eval_act("frame", "x", False)
                fr["y_up"] = eval_act("frame", "y", False)
                fr["select"] = eval_act("frame", "menu", False)
            else:
                fr["y_up"] = eval_act("frame", "up", False)
                fr["a_down"] = eval_act("frame", "down", False)
                fr["x_left"] = eval_act("frame", "left", False)
                fr["b_right"] = eval_act("frame", "right", False)
                fr["select"] = eval_act("frame", "select", False)

            fr["trigger"] = eval_act("frame", "trigger", 0.0)
            fr["grip"] = eval_act("frame", "grip", 0.0)
            fr["joy_x"] = eval_act("frame", "joy_right", 0.0) - eval_act("frame", "joy_left", 0.0)
            fr["joy_y"] = eval_act("frame", "joy_up", 0.0) - eval_act("frame", "joy_down", 0.0)

            fr["bumper"] = eval_act("frame", "bumper", False)
            fr["system"] = eval_act("frame", "system", False)
            fr["trigger_btn"] = fr["trigger"] >= CLICK_AT
            fr["grip_btn"] = fr["grip"] >= CLICK_AT
            fr["joy_btn"] = eval_act("frame", "joy_click", False)

            fr["y_up_cap"] = fr["y_up"]
            fr["a_down_cap"] = fr["a_down"]
            fr["x_left_cap"] = fr["x_left"]
            fr["b_right_cap"] = fr["b_right"]
            fr["select_cap"] = fr["select"]
            fr["bumper_cap"] = fr["bumper"]
            fr["system_cap"] = fr["system"]
            fr["trigger_cap"] = fr["trigger_btn"] or (fr["trigger"] > 0.05)
            fr["grip_cap"] = fr["grip_btn"] or (fr["grip"] > 0.05)
            fr["joy_cap"] = fr["joy_btn"]

        elif con_type == "vive":
            vv = input["vive"]

            vv["trigger"] = eval_act("vive", "trigger", 0.0)
            vv["touch_x"] = eval_act("vive", "touch_right", 0.0) - eval_act("vive", "touch_left", 0.0)
            vv["touch_y"] = eval_act("vive", "touch_up", 0.0) - eval_act("vive", "touch_down", 0.0)

            vv["system"] = eval_act("vive", "system", False)
            vv["grip_btn"] = eval_act("vive", "grip_btn", 0.0) >= CLICK_AT
            vv["select"] = eval_act("vive", "select", False)
            vv["trigger_btn"] = vv["trigger"] >= CLICK_AT
            vv["touch_btn"] = eval_act("vive", "touch_btn", False)

            vv["touch_cap"] = vv["touch_btn"] or (vv["touch_x"] != 0.0) or (vv["touch_y"] != 0.0)

        elif con_type == "touch":
            is_right = (prefix == "cr")
            tc = input["touch"]

            tc["trigger"] = eval_act("touch", "trigger", 0.0)
            tc["grip"] = eval_act("touch", "grip", 0.0)
            tc["joy_x"] = eval_act("touch", "joy_right", 0.0) - eval_act("touch", "joy_left", 0.0)
            tc["joy_y"] = eval_act("touch", "joy_up", 0.0) - eval_act("touch", "joy_down", 0.0)

            tc["system"] = eval_act("touch", "system", False)
            if is_right:
                tc["a_x"] = eval_act("touch", "a", False)
                tc["b_y"] = eval_act("touch", "b", False)
            else:
                tc["a_x"] = eval_act("touch", "x", False)
                tc["b_y"] = eval_act("touch", "y", False)

            tc["joy_btn"] = eval_act("touch", "joy_click", False)

            tc["a_x_cap"] = tc["a_x"]
            tc["b_y_cap"] = tc["b_y"]
            tc["trigger_cap"] = (tc["trigger"] > 0.05)
            tc["joy_cap"] = tc["joy_btn"] or abs(tc["joy_x"]) > 0.1 or abs(tc["joy_y"]) > 0.1

        flex = [0.0] * 20
        for i, finger in enumerate(FINGERS):
            flex[i * 4] = min(1.0, max(0.0, eval_act(con_type, finger, 0.0)))
        skeletal[f"{side} flexion"] = flex

        time.sleep(0.001)