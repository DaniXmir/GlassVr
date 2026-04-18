#pyinstaller --noconfirm --windowed --collect-binaries "sdl3dll" --collect-all "sdl3" --collect-binaries "openvr" --collect-all "mediapipe" --collect-all "cv2" --hidden-import "sdl3dll" main.py
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea

from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QTimer

from PyQt6.QtGui import QPixmap, QIcon, QKeySequence

import shutil
import psutil
import os
import json
import struct
import time
import threading
import math
import openvr as vr
import numpy as np
from scipy.spatial.transform import Rotation as R
import sys

import win32file
from typing import List, Dict, Any, Tuple
import cv2
import mediapipe as mp
import cv2.aruco as aruco

import cvzone
from cvzone.HandTrackingModule import HandDetector

import time

import sdl3 as SDL
from sdl3 import *

import ctypes
import webbrowser
import platform
import requests

import win32pipe
import pywintypes

import settings_core

from collections import deque

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('sdl3dll')

app = QApplication([])#sys.argv)

window = QWidget()
window_layout = QHBoxLayout(window)

tabs = QTabWidget()
#window.setWindowTitle("PuffinVR")
window.setWindowTitle("GlassVR")

window.resize(900, 900)

#ui core/////////////////////////////////////////////////////////////////////////////////////////////////////////////
# layout_main.addWidget(create_group_label([{"text" : "a", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "b", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "c", "alignment" : Qt.AlignmentFlag.AlignCenter}]))
# layout_main.addWidget(create_group_button([{"text" : "a", "enabled" : True},{"text" : "b", "enabled" : True},{"text" : "c", "enabled" : False}]))
# layout_main.addWidget(create_group_checkbox([{"text" : "a", "checked" : True},{"text" : "a", "checked" : False}]))
# layout_main.addWidget(create_group_spinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))
# layout_main.addWidget(create_group_doublespinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())

def create_label(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict.get('text',""))
    label.setAlignment(dict.get('alignment',Qt.AlignmentFlag.AlignCenter))
    group_layout.addWidget(label)

    return group_widget

def create_group_label(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_label(dict))

        return group_widget

def create_button(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    button = QPushButton(dict.get('text',""))
    if 'func' in dict:
        button.clicked.connect(lambda: dict['func']())
    button.setEnabled(dict.get('enabled',True))

    group_layout.addWidget(button)

    return group_widget

def create_group_button(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_button(dict))

        return group_widget

def create_checkbox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    group_layout.addWidget(label)

    checkbox = QCheckBox()
    checkbox.setChecked(dict['default'])
    if 'func' in dict:
        checkbox.clicked.connect(lambda: dict['func']())
    group_layout.addWidget(checkbox)

    return group_widget

def create_group_checkbox(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_checkbox(dict))

        return group_widget

def create_spinbox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    spinbox = QSpinBox()
    spinbox.setRange(dict['min'], dict['max'])
    spinbox.setValue(dict['default'])
    spinbox.setSingleStep(dict.get('steps',1))
    if 'func' in dict:
        spinbox.valueChanged.connect(lambda: dict['func']())
    group_layout.addWidget(spinbox)

    return group_widget

def create_group_spinbox(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_spinbox(dict))

        return group_widget

def create_doublespinbox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    spinbox = QDoubleSpinBox()
    spinbox.setRange(dict['min'], dict['max'])
    spinbox.setValue(dict['default'])
    spinbox.setSingleStep(dict.get('steps',1))
    spinbox.setDecimals(3)
    if 'func' in dict:
        spinbox.valueChanged.connect(lambda: dict['func']())
    group_layout.addWidget(spinbox)

    return group_widget

def create_group_doublespinbox(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_doublespinbox(dict))

        return group_widget
    
def create_lineedit(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    lineedit = QLineEdit()
    lineedit.setText(dict['default'])
    if 'func' in dict:
        lineedit.textChanged.connect(lambda: dict['func']())
    group_layout.addWidget(lineedit)

    return group_widget

def create_group_lineedit(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_lineedit(dict))

        return group_widget

def create_group_horizontal(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            match dict['type']:
                case "label":
                    group_layout.addWidget(create_label(dict))
                case "button":
                    group_layout.addWidget(create_button(dict))
                case "checkbox":
                    group_layout.addWidget(create_checkbox(dict))
                case "spinbox":
                    group_layout.addWidget(create_spinbox(dict))
                case "doublespinbox":
                    group_layout.addWidget(create_doublespinbox(dict))
                case "lineedit":
                    group_layout.addWidget(create_lineedit(dict))
                case "image":
                    group_layout.addWidget(create_image(dict))
                case "combobox":
                    group_layout.addWidget(create_combobox(dict))
        return group_widget
    
def create_image(dict = {}):
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "assets", dict.get("path", "fix"))

    image_label = QLabel()
    image = QPixmap(image_path)
    scaled_pixmap = image.scaled(dict.get("size x", 100), dict.get("size y", 100), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    image_label.setPixmap(scaled_pixmap)
    image_label.setAlignment(dict.get('alignment',Qt.AlignmentFlag.AlignCenter))

    return image_label 

def create_combobox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict.get('text', ""))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    combobox = QComboBox()
    
    if 'items' in dict:
        combobox.addItems(dict['items'])
    
    if 'default' in dict:\
        combobox.setCurrentText(dict['default'])

    if 'func' in dict:
        combobox.currentIndexChanged.connect(lambda: dict['func']())
        
    group_layout.addWidget(combobox)

    return group_widget

def create_group_combobox(arr = [], direction = "h"):
    if arr:
        group_widget = QWidget()
        group_layout = 0

        match direction:
            case "h":
                group_layout = QHBoxLayout(group_widget)
            case "v":
                group_layout = QVBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_combobox(dict))

        return group_widget
#ui core/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#controller handler v3/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class _Signals(QObject):
    controller_connected = pyqtSignal()

signals = _Signals()

SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_WII", b"1")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_COMBINE_JOY_CONS", b"0")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4", b"1")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS5", b"1")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4_RUMBLE", b"1")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_XBOX_ELITE", b"1")
SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")

SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMEPAD)

WIIMOTE_VID    = 0x057E
WIIMOTE_PIDS   = [0x0306, 0x0330]
SDL_TRUE       = 1
SDL_FALSE      = 0

CALIBRATION_SAMPLES = 200
DEFAULT_THRESHOLD   = 0.02
DEADZONE            = 0.1
ALPHA               = 0.98

controllers_dict = {}#{id here(aa-bb-cc-dd-ee) : {"btn1" : false, "axis" " -1 to 1"}}
controllers_lock = threading.Lock()
running          = True

def get_default_state(device_type="unknown", handle=None, unique_id=""):
    return {
        "id":             unique_id,
        "type":           device_type,
        "handle":         handle,
        "active":         True,
        "gyro_quat":      {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "last_good_quat": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "last_ts":        0,
        "gyro_bias": {
            "wx": 0.0, "wy": 0.0, "wz": 0.0,
            "ax": 0.0, "ay": 0.0, "az": 0.0,
            "tx": DEFAULT_THRESHOLD, "ty": DEFAULT_THRESHOLD, "tz": DEFAULT_THRESHOLD,
            "samples": 0
        }
    }

def get_controller(c_id):
    return controllers_dict.get(c_id, get_default_state())

def get_gyro(c_id):
    ctrl = controllers_dict.get(c_id)
    if ctrl is None:
        return {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    return ctrl["gyro_quat"].copy()

def get_all_controllers():
    with controllers_lock:
        return list(controllers_dict.values())

def normalize_quat(q):
    mag = math.sqrt(q["x"]**2 + q["y"]**2 + q["z"]**2 + q["w"]**2)
    if mag == 0: return {"x": 0, "y": 0, "z": 0, "w": 1}
    return {k: q[k] / mag for k in "xyzw"}

def normalize_vec3(v):
    mag = math.sqrt(v["x"]**2 + v["y"]**2 + v["z"]**2)
    if mag == 0: return {"x": 0, "y": 0, "z": 1}
    return {k: v[k] / mag for k in "xyz"}

def quat_multiply(q1, q2):
    return {
        "w": q1["w"]*q2["w"] - q1["x"]*q2["x"] - q1["y"]*q2["y"] - q1["z"]*q2["z"],
        "x": q1["w"]*q2["x"] + q1["x"]*q2["w"] + q1["y"]*q2["z"] - q1["z"]*q2["y"],
        "y": q1["w"]*q2["y"] - q1["x"]*q2["z"] + q1["y"]*q2["w"] + q1["z"]*q2["x"],
        "z": q1["w"]*q2["z"] + q1["x"]*q2["y"] - q1["y"]*q2["x"] + q1["z"]*q2["w"],
    }

def quat_from_two_vectors(v1, v2):
    v1, v2 = normalize_vec3(v1), normalize_vec3(v2)
    cross = {
        "x": v1["y"]*v2["z"] - v1["z"]*v2["y"],
        "y": v1["z"]*v2["x"] - v1["x"]*v2["z"],
        "z": v1["x"]*v2["y"] - v1["y"]*v2["x"],
    }
    dot = sum(v1[k]*v2[k] for k in "xyz")
    if dot < -0.999999:
        axis = normalize_vec3({"x": 1, "y": 0, "z": 0} if abs(v1["x"]) < 0.6 else {"x": 0, "y": 1, "z": 0})
        axis = normalize_vec3({
            "x": v1["y"]*axis["z"] - v1["z"]*axis["y"],
            "y": v1["z"]*axis["x"] - v1["x"]*axis["z"],
            "z": v1["x"]*axis["y"] - v1["y"]*axis["x"],
        })
        return {"w": 0, **axis}
    return normalize_quat({"w": 1.0 + dot, **cross})

def quat_slerp(q1, q2, t):
    dot = sum(q1[k]*q2[k] for k in "wxyz")
    if dot > 0.9995:
        return normalize_quat({k: q1[k] + t*(q2[k] - q1[k]) for k in "wxyz"})
    if dot < 0:
        q2  = {k: -q2[k] for k in "wxyz"}
        dot = -dot
    dot     = max(-1.0, min(1.0, dot))
    theta_0 = math.acos(dot)
    theta   = theta_0 * t
    sin_t   = math.sin(theta)
    sin_t0  = math.sin(theta_0)
    s1 = math.cos(theta) - dot * sin_t / sin_t0
    s2 = sin_t / sin_t0
    return {k: s1*q1[k] + s2*q2[k] for k in "wxyz"}

def _hmd_quat_dict():
    q = R.from_matrix(trackers_arr[0]["rotation matrix"]).as_quat()
    return {"x": q[0], "y": q[1], "z": q[2], "w": q[3]}

def reset_gyro(target_id=None, to_zero=False):
    if to_zero:
        target_quat = {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
    else:
        target_quat = _hmd_quat_dict().copy()

    with controllers_lock:
        for c_id, ctrl in controllers_dict.items():
            if target_id is None or c_id == target_id:
                if "gyro_quat" in ctrl:
                    ctrl["gyro_quat"]      = target_quat.copy()
                    ctrl["last_good_quat"] = target_quat.copy()

def start_calibration(target_id=None):
    with controllers_lock:
        for c_id, ctrl in controllers_dict.items():
            if target_id is None or c_id == target_id:
                if "gyro_bias" in ctrl:
                    ctrl["gyro_bias"] = {
                        "wx": 0.0, "wy": 0.0, "wz": 0.0,
                        "ax": 0.0, "ay": 0.0, "az": 0.0,
                        "tx": DEFAULT_THRESHOLD, "ty": DEFAULT_THRESHOLD, "tz": DEFAULT_THRESHOLD,
                        "samples":    0,
                        "calibrating": True
                    }

def process_sdl_gyro(c_id, raw_data, timestamp_ns):
    target = controllers_dict.get(c_id)
    if target is None:
        return

    all_settings = settings_core.get_settings()
    conf = all_settings.get(c_id, {})

    idx_x = conf.get("index_x", 0)
    idx_y = conf.get("index_y", 1)
    idx_z = conf.get("index_z", 2)
    sens  = conf.get("sensitivity", 1.0)

    rx = raw_data[idx_x] * (-1 if conf.get("invert_x") else 1)
    ry = raw_data[idx_y] * (-1 if conf.get("invert_y") else 1)
    rz = raw_data[idx_z] * (-1 if conf.get("invert_z") else 1)

    bias = target["gyro_bias"]

    if not bias.get("loaded") and not bias.get("calibrating"):
        saved = conf.get("calibration")
        if saved:
            bias["wx"] = saved["wx"]
            bias["wy"] = saved["wy"]
            bias["wz"] = saved["wz"]
        bias["loaded"] = True

    if bias.get("calibrating"):
        n = bias["samples"]
        bias["wx"] = (bias["wx"] * n + rx) / (n + 1)
        bias["wy"] = (bias["wy"] * n + ry) / (n + 1)
        bias["wz"] = (bias["wz"] * n + rz) / (n + 1)
        bias["samples"] += 1

        if bias["samples"] >= CALIBRATION_SAMPLES:
            bias["calibrating"] = False
            bias["loaded"]      = True
            settings_core.update_nested(c_id, {
                "calibration": {
                    "wx": bias["wx"],
                    "wy": bias["wy"],
                    "wz": bias["wz"],
                }
            })
        return

    vx = (rx - bias["wx"]) * sens
    vy = (ry - bias["wy"]) * sens
    vz = (rz - bias["wz"]) * sens

    if target.get("last_ts", 0) == 0:
        target["last_ts"] = timestamp_ns
        return

    dt = (timestamp_ns - target["last_ts"]) / 1_000_000_000.0
    target["last_ts"] = timestamp_ns

    q  = target["gyro_quat"]
    qw, qx, qy, qz = q["w"], q["x"], q["y"], q["z"]

    new_qw = qw + 0.5 * (-qx*vx - qy*vy - qz*vz) * dt
    new_qx = qx + 0.5 * ( qw*vx + qy*vz - qz*vy) * dt
    new_qy = qy + 0.5 * ( qw*vy - qx*vz + qz*vx) * dt
    new_qz = qz + 0.5 * ( qw*vz + qx*vy - qy*vx) * dt

    mag = math.sqrt(new_qw**2 + new_qx**2 + new_qy**2 + new_qz**2)
    if mag > 0:
        target["gyro_quat"] = {
            "w": new_qw / mag,
            "x": new_qx / mag,
            "y": new_qy / mag,
            "z": new_qz / mag,
        }

def run_sdl_event_loop():
    sdl_id_map = {}

    while running:
        event = SDL.SDL_Event()
        while SDL.SDL_PollEvent(ctypes.byref(event)):

            #connected
            if event.type == SDL_EVENT_JOYSTICK_ADDED:
                device_index = event.jdevice.which
                joy_handle   = SDL.SDL_OpenJoystick(device_index)

                if joy_handle:
                    instance_id = SDL.SDL_GetJoystickID(joy_handle)
                    name        = SDL.SDL_GetJoystickName(joy_handle).decode("utf-8", "replace")
                    guid        = SDL.SDL_GetJoystickGUID(joy_handle)
                    guid_str    = "".join([f"{guid.data[i]:02x}" for i in range(16)])
                    serial      = SDL.SDL_GetJoystickSerial(joy_handle)
                    unique_id   = serial.decode("utf-8") if serial else guid_str

                    gamepad_handle      = SDL.SDL_OpenGamepad(device_index)
                    gamepad_instance_id = None
                    if gamepad_handle:
                        SDL.SDL_SetGamepadSensorEnabled(gamepad_handle, SDL.SDL_SENSOR_GYRO,  SDL_TRUE)
                        SDL.SDL_SetGamepadSensorEnabled(gamepad_handle, SDL.SDL_SENSOR_ACCEL, SDL_TRUE)
                        gamepad_instance_id = SDL.SDL_GetGamepadID(gamepad_handle)

                    with controllers_lock:
                        if unique_id in controllers_dict:
                            controllers_dict[unique_id]["joystick_handle"] = joy_handle
                            controllers_dict[unique_id]["gamepad_handle"]  = gamepad_handle
                            controllers_dict[unique_id]["active"]          = True
                            controllers_dict[unique_id]["last_ts"]         = 0
                        else:
                            state = get_default_state(name, joy_handle, unique_id)
                            state["joystick_handle"] = joy_handle
                            state["gamepad_handle"]  = gamepad_handle
                            controllers_dict[unique_id] = state

                    sdl_id_map[instance_id] = unique_id
                    if gamepad_instance_id is not None:
                        sdl_id_map[gamepad_instance_id] = unique_id

                    signals.controller_connected.emit()

            #gyro
            elif event.type == SDL_EVENT_GAMEPAD_SENSOR_UPDATE:
                c_id = sdl_id_map.get(event.gsensor.which)
                if c_id and event.gsensor.sensor == SDL.SDL_SENSOR_GYRO:
                    process_sdl_gyro(c_id, list(event.gsensor.data), event.gsensor.sensor_timestamp)

            #disconnect
            elif event.type == SDL_EVENT_JOYSTICK_REMOVED:
                instance_id = event.jdevice.which
                c_id        = sdl_id_map.get(instance_id)
                if c_id:
                    with controllers_lock:
                        ctrl = controllers_dict.get(c_id, {})
                        if ctrl.get("gamepad_handle"):
                            SDL.SDL_CloseGamepad(ctrl["gamepad_handle"])
                        ctrl["joystick_handle"] = None
                        ctrl["gamepad_handle"]  = None
                        ctrl["active"]          = False
                    keys_to_remove = [k for k, v in sdl_id_map.items() if v == c_id]
                    for k in keys_to_remove:
                        del sdl_id_map[k]

            #btn
            elif event.type in [SDL_EVENT_JOYSTICK_BUTTON_DOWN, SDL_EVENT_JOYSTICK_BUTTON_UP]:
                c_id = sdl_id_map.get(event.jbutton.which)
                if c_id:
                    key      = f"btn_{event.jbutton.button}"
                    is_down  = bool(event.jbutton.down)
                    ctrl     = controllers_dict.get(c_id, {})
                    old_state = ctrl.copy()
                    ctrl[key] = is_down
                    detect_input_change(c_id, {key: is_down}, old_state)

            #axes
            elif event.type == SDL_EVENT_JOYSTICK_AXIS_MOTION:
                c_id = sdl_id_map.get(event.jaxis.which)
                if c_id:
                    key     = f"axis_{event.jaxis.axis}"
                    val     = event.jaxis.value / 32767.0
                    ctrl    = controllers_dict.get(c_id, {})
                    old_val = ctrl.get(key, 0.0)
                    ctrl[key] = val
                    detect_input_change(c_id, {key: val}, {key: old_val})

            #hat
            elif event.type == SDL_EVENT_JOYSTICK_HAT_MOTION:
                c_id = sdl_id_map.get(event.jhat.which)
                if c_id:
                    key     = f"hat_{event.jhat.hat}"
                    val     = event.jhat.value
                    ctrl    = controllers_dict.get(c_id, {})
                    old_val = ctrl.get(key, 0)
                    ctrl[key] = val
                    detect_input_change(c_id, {key: val}, {key: old_val})

        time.sleep(0.001)

def run_hardware_poller():
    while running:
        try:
            with controllers_lock:
                items = list(controllers_dict.items())
            for c_id, ctrl in items:
                if ctrl.get("gamepad_handle"):
                    new_data = poll_hardware(ctrl["gamepad_handle"])
                    detect_input_change(c_id, new_data, ctrl)
                    ctrl.update(new_data)
        except Exception:
            pass
        time.sleep(0.001)

def start_controller_mapping():
    global running
    running = True

    threads = [
        threading.Thread(target=run_sdl_event_loop,   daemon=True, name="SDL_Event_Manager"),
        threading.Thread(target=run_hardware_poller,   daemon=True, name="Hardware_Poller"),
    ]
    for t in threads:
        t.start()
    return threads

def poll_hardware(c):
    def axis(a):
        v = SDL.SDL_GetGamepadAxis(c, a) / 32767.0
        if abs(v) < DEADZONE: return 0.0
        return (v - (DEADZONE if v > 0 else -DEADZONE)) / (1.0 - DEADZONE)

    def btn(b): return bool(SDL.SDL_GetGamepadButton(c, b))

    return {
        "a":             btn(SDL.SDL_GAMEPAD_BUTTON_SOUTH),
        "b":             btn(SDL.SDL_GAMEPAD_BUTTON_EAST),
        "x":             btn(SDL.SDL_GAMEPAD_BUTTON_WEST),
        "y":             btn(SDL.SDL_GAMEPAD_BUTTON_NORTH),
        "back":          btn(SDL.SDL_GAMEPAD_BUTTON_BACK),
        "start":         btn(SDL.SDL_GAMEPAD_BUTTON_START),
        "guide":         btn(SDL.SDL_GAMEPAD_BUTTON_GUIDE),
        "dpup":          btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_UP),
        "dpdown":        btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_DOWN),
        "dpleft":        btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_LEFT),
        "dpright":       btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_RIGHT),
        "leftshoulder":  btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_SHOULDER),
        "rightshoulder": btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER),
        "leftstick":     btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_STICK),
        "rightstick":    btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_STICK),
        "paddle_1":      btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_PADDLE1),
        "paddle_2":      btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_PADDLE2),
        "paddle_3":      btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1),
        "paddle_4":      btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2),
        "touchpad":      btn(SDL.SDL_GAMEPAD_BUTTON_TOUCHPAD),
        "misc1":         btn(SDL.SDL_GAMEPAD_BUTTON_MISC1),
        "leftx":         axis(SDL.SDL_GAMEPAD_AXIS_LEFTX),
        "lefty":         axis(SDL.SDL_GAMEPAD_AXIS_LEFTY),
        "rightx":        axis(SDL.SDL_GAMEPAD_AXIS_RIGHTX),
        "righty":        axis(SDL.SDL_GAMEPAD_AXIS_RIGHTY),
        "lefttrigger":   axis(SDL.SDL_GAMEPAD_AXIS_LEFT_TRIGGER),
        "righttrigger":  axis(SDL.SDL_GAMEPAD_AXIS_RIGHT_TRIGGER),
    }

def detect_input_change(c_id, new_data, old_state):
    global current_binding_btn

    if current_binding_btn is None:
        return

    for key, value in new_data.items():
        if key.startswith("btn_") and value is True:
            current_binding_btn.finish_binding(f"SDL_{c_id}_{key}")
            return
        if key.startswith("hat_") and value != 0:
            current_binding_btn.finish_binding(f"SDL_{c_id}_{key}_{value}")
            return
        if key.startswith("axis_") and abs(value) > 0.7:
            direction = "1.0" if value > 0 else "-1.0"
            current_binding_btn.finish_binding(f"SDL_{c_id}_{key}_{direction}")
            return

def eval_binding(bind_data):
    if isinstance(bind_data, dict):
        buttons = bind_data.get("buttons", [])
        invert = bind_data.get("invert", False)

        max_val = 0.0
        for btn_string in buttons:
            val = eval_binding(btn_string)
            if val > max_val:
                max_val = val

        return 1.0 - max_val if invert else max_val

    if not bind_data or bind_data == "[Unbound]": 
        return 0.0

    parts = bind_data.split("_", 2)

    if parts[0] == "SDL" and len(parts) == 3:
        try:
            c_id = parts[1]
            remainder = parts[2]
            c_dict = controllers_dict.get(c_id)
            if c_dict is None: return 0.0

            if "axis" in remainder:
                r = remainder.split("_")
                key_name = "_".join(r[:-1])
                target_dir = float(r[-1])
                current = float(c_dict.get(key_name, 0.0))
                return max(0.0, current * target_dir)

            if "hat" in remainder:
                r = remainder.split("_")
                key_name = "_".join(r[:-1])
                target_bit = int(r[-1])
                current = int(c_dict.get(key_name, 0))
                return 1.0 if (current & target_bit) else 0.0

            val = c_dict.get(remainder, 0.0)
            return 1.0 if val is True or val > 0.5 else 0.0
        except Exception:
            return 0.0

    if parts[0] in ["Key", "Mouse"]:
        vk = get_vk_code(bind_data)
        return 1.0 if (vk and is_key_pressed_globally(vk)) else 0.0

    return 0.0

#controller handler v3/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#main/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_main = QWidget()
layout_main = QVBoxLayout(tab_main)
layout_main.setSpacing(0)

check_box_hmd = create_checkbox(
    {
        "text" : "enable hmd", 
        "default" : settings_core.get_settings()['enable hmd'], 
        "func" : lambda: settings_core.update_setting("enable hmd",check_box_hmd.findChild(QCheckBox).isChecked())
    })
layout_main.addWidget(check_box_hmd)

#hmd modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def hmdpos_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings['hmdpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        # case "keyboard":
        #     t = create_group_horizontal([{
        #             "type" : "spinbox", 
        #             "text" :"test1", 
        #             "min":0,
        #             "max":999999999, 
        #             "default": settings['hmdpos index'], 
        #             "steps" : 1,
        #             "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
        #         },{
        #             "type" : "spinbox", 
        #             "text" :"test2", 
        #             "min":0, 
        #             "max":999999999, 
        #             "default": settings['hmdpos index'], 
        #             "steps" : 1,
        #             "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
        #         }])
            
        #     layout.addWidget(t)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_hmdpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "hmd position mode",
            "default": settings.get(f'hmdpos mode', "redirect"),
            "items": ["redirect", "offsets"],# "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: hmdpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    hmdpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_main.addWidget(create_hmdpos_widget())
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def hmdrot_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)
            
        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings["hmd gyro id"],
                    "items": list(controllers_dict),
                    "func": lambda: settings_core.update_setting("hmd gyro id", combo_extra.findChildren(QComboBox)[0].currentText())
                })
            
            layout.addWidget(combo_extra)

        case "xr glasses":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "only viture glasses are supported for now(for 3dof rotation)",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                },{
                    "type" : "button",
                    "enabled" : True,
                    "text" :"calibrate on viture site",
                    "func"  : lambda: webbrowser.open("https://www.viture.com/firmware/calibration")
                }])
            layout.addWidget(t)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_hmdrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "hmd rotation mode",
            "default": settings.get(f'hmdrot mode', "redirect"),
            "items": ["redirect", "offsets", "gyro", "xr glasses"],# "mouse"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: hmdrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    hmdrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_main.addWidget(create_hmdrot_widget())
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#hmd modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

trackers_arr = [] #[{"pos x" : m[0][3],
                    #"pos y" : m[1][3],
                    #"pos z" : m[2][3], 
                    #"rotation matrix" :[
                    #[m[0][0], m[0][1], m[0][2]],
                    #[m[1][0], m[1][1], m[1][2]],
                    # [m[2][0], m[2][1], m[2][2]]
                    # ]}]

def is_prosses_running(PROCESS_NAME):
    for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == PROCESS_NAME.lower():
                return True
    
    return False

def check_hardware_key_exists(hardware_name):
    settings = settings_core.get_settings()
    
    return hardware_name in settings.values()

#deprecated dont use! should delete later!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def get_final_transform(device = "hmd", override = None):
    settings = settings_core.get_settings()

    try:
        tracker_pos_idx = settings.get(f'{device}pos index', 0)

        if override == None:
            tracker_pos = trackers_arr[tracker_pos_idx]
        else:
            tracker_pos = override

        tracker_rot_idx = settings.get(f'{device}rot index', 0)

        if override == None:
            tracker_rot = trackers_arr[tracker_rot_idx]
        else:
            tracker_rot = override

        offset_local = np.array([
            settings.get(f'{device} offset local x', 0.0),
            settings.get(f'{device} offset local y', 0.0),
            settings.get(f'{device} offset local z', 0.0)
        ])
        
        offset_world = np.array([
            settings.get(f'{device} offset world x', 0.0),
            settings.get(f'{device} offset world y', 0.0),
            settings.get(f'{device} offset world z', 0.0)
        ])
        
        device_rotation = R.from_matrix(tracker_rot['rotation matrix'])
        
        rotated_local_offset = device_rotation.apply(offset_local)
        
        pos_x = tracker_pos['pos x'] + rotated_local_offset[0] + offset_world[0]
        pos_y = tracker_pos['pos y'] + rotated_local_offset[1] + offset_world[1]
        pos_z = tracker_pos['pos z'] + rotated_local_offset[2] + offset_world[2]
        
        offset_local_angles_rad = [
            settings.get(f'{device} offset local roll', 0.0),
            settings.get(f'{device} offset local yaw', 0.0),
            settings.get(f'{device} offset local pitch', 0.0)
        ]
        
        offset_world_angles_rad = [
            settings.get(f'{device} offset world roll', 0.0),
            settings.get(f'{device} offset world yaw', 0.0),
            settings.get(f'{device} offset world pitch', 0.0)
        ]
        
        offset_local_rotation = R.from_euler('ZYX', offset_local_angles_rad, degrees=False)
        offset_world_rotation = R.from_euler('ZYX', offset_world_angles_rad, degrees=False)
        
        final_rotation = offset_world_rotation * device_rotation * offset_local_rotation
        quat_final = final_rotation.as_quat()
        
        return({
            "pos x" : pos_x, "pos y" : pos_y, "pos z" : pos_z,
            "rot x" : quat_final[0], "rot y" : quat_final[1], "rot z" : quat_final[2], "rot w" : quat_final[3]
        })
    except:
        try:
            offset_local_angles_rad = [
                settings.get(f'{device} offset local roll', 0.0),
                settings.get(f'{device} offset local yaw', 0.0),
                settings.get(f'{device} offset local pitch', 0.0)
            ]
            
            offset_world_angles_rad = [
                settings.get(f'{device} offset world roll', 0.0),
                settings.get(f'{device} offset world yaw', 0.0),
                settings.get(f'{device} offset world pitch', 0.0)
            ]
            
            offset_local_rotation = R.from_euler('ZYX', offset_local_angles_rad, degrees=False)
            offset_world_rotation = R.from_euler('ZYX', offset_world_angles_rad, degrees=False)
            combined_rotation = offset_world_rotation * offset_local_rotation
            quat = combined_rotation.as_quat()
            
            return({
                "pos x" : settings.get(f'{device} offset local x', 0.0) + settings.get(f'{device} offset world x', 0.0),
                "pos y" : settings.get(f'{device} offset local y', 0.0) + settings.get(f'{device} offset world y', 0.0),
                "pos z" : settings.get(f'{device} offset local z', 0.0) + settings.get(f'{device} offset world z', 0.0),
                "rot x" : quat[0], "rot y" : quat[1], "rot z" : quat[2], "rot w" : quat[3]
            })
        except:
            return({
                "pos x" : 0.0, "pos y" : 0.0, "pos z" : 0.0,
                "rot x" : 0.0, "rot y" : 0.0, "rot z" : 0.0, "rot w" : 1.0
            })

#use this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def get_new_transform(device="hmd", px=0.0, py=0.0, pz=0.0, rx=0.0, ry=0.0, rz=0.0, rw=0.0):
    #get the final position of the emulated device with offsets applied,
    #device: from what settings to take offsets
    #other arguments: are what the current pos and rot of the emulated device, example: to copy x from tracker, pass trackers_arr[tracker_pos_idx]['pos x'] to px
    settings = settings_core.get_settings()
    
    try:
        device_rotation = R.from_quat([rx, ry, rz, rw])
        
        offset_local = np.array([
            settings.get(f'{device} offset local x', 0.0),
            settings.get(f'{device} offset local y', 0.0),
            settings.get(f'{device} offset local z', 0.0)
        ])
        
        offset_world = np.array([
            settings.get(f'{device} offset world x', 0.0),
            settings.get(f'{device} offset world y', 0.0),
            settings.get(f'{device} offset world z', 0.0)
        ])
        
        rotated_local_offset = device_rotation.apply(offset_local)
        
        pos_x = px + rotated_local_offset[0] + offset_world[0]
        pos_y = py + rotated_local_offset[1] + offset_world[1]
        pos_z = pz + rotated_local_offset[2] + offset_world[2]
        
        off_loc_angles = [
            settings.get(f'{device} offset local roll', 0.0),
            settings.get(f'{device} offset local yaw', 0.0),
            settings.get(f'{device} offset local pitch', 0.0)
        ]
        
        off_world_angles = [
            settings.get(f'{device} offset world roll', 0.0),
            settings.get(f'{device} offset world yaw', 0.0),
            settings.get(f'{device} offset world pitch', 0.0)
        ]
        
        offset_local_rotation = R.from_euler('ZYX', off_loc_angles, degrees=False)
        offset_world_rotation = R.from_euler('ZYX', off_world_angles, degrees=False)
        
        final_rotation = offset_world_rotation * device_rotation * offset_local_rotation
        quat_final = final_rotation.as_quat()
        
        return {
            "pos x" : pos_x, "pos y" : pos_y, "pos z" : pos_z,
            "rot x" : quat_final[0], "rot y" : quat_final[1], 
            "rot z" : quat_final[2], "rot w" : quat_final[3]
        }

    except Exception as e:
        return {
            "pos x" : px, "pos y" : py, "pos z" : pz,
            "rot x" : rx, "rot y" : ry, "rot z" : rz, "rot w" : rw
        }
    
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def euler_to_quat(pitch, roll, yaw):
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy

    return {
        "w": qw,
        "x": qx,
        "y": qy,
        "z": qz
    }

HMD_PACK_FORMAT = '<9d'
CONTROLLER_PACK_FORMAT = '=37d 6?'
TRACKER_PACK_FORMAT = '<7d'

HMD_PACKER = struct.Struct(HMD_PACK_FORMAT)
CONTROLLER_PACKER = struct.Struct(CONTROLLER_PACK_FORMAT)
TRACKER_PACKER = struct.Struct(TRACKER_PACK_FORMAT)

PIPE_HMD = r'\\.\pipe\GlassVR_HMD'
PIPE_LEFT = r'\\.\pipe\GlassVR_Left'
PIPE_RIGHT = r'\\.\pipe\GlassVR_Right'
PIPE_TRACKER_PREFIX = r'\\.\pipe\GlassVR_Tracker_'

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )

def send_hmd_data():
    while True:
        handle = None
        try:
            handle = create_pipe(PIPE_HMD)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()

                final_transform = get_final_transform("hmd")
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings['hmdpos mode']:
                        case "redirect":
                            pass

                        case "offsets":
                            pos_x = settings["hmd offset world x"]
                            pos_y = settings["hmd offset world y"]
                            pos_z = settings["hmd offset world z"]

                        case "keyboard":
                            pass

                        case _:
                            final_transform = get_final_transform("hmd")

                            pos_x = final_transform['pos x']
                            pos_y = final_transform['pos y']
                            pos_z = final_transform['pos z']
                except:
                    pass
                try:
                    match settings['hmdrot mode']:
                        case "redirect":
                            pass

                        case "offsets":
                            quat = euler_to_quat(settings["hmd offset world yaw"],
                                                 settings["hmd offset world pitch"],
                                                 settings["hmd offset world roll"])

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                        case "mouse":
                            pass

                        case "gyro":
                            quat = get_gyro(settings["hmd gyro id"])

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                        case _:
                            final_transform = get_final_transform("hmd")

                            rot_x = final_transform['rot x']
                            rot_y = final_transform['rot y']
                            rot_z = final_transform['rot z']
                            rot_w = final_transform['rot w']
                except:
                    pass
                hmd_ipd = settings.get('ipd', 0.0)
                hmd_head_to_eye_dist = settings.get('head to eye dist', 0.0)

                buffer = HMD_PACKER.pack(
                    pos_x, pos_y, pos_z,
                    rot_w, rot_x, rot_y, rot_z,
                    hmd_ipd, hmd_head_to_eye_dist
                )
                
                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            pass

        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

def get_hand_world_transform(device):
    try:
        hand_prefix = 'r' if device == "cr" else 'l'
        
        settings = settings_core.get_settings()
        cam_offset_x = settings.get('camera offset x', 0.0)
        cam_offset_y = settings.get('camera offset y', 0.0)
        cam_offset_z = settings.get('camera offset z', 0.0)
        outer_stereo  = settings.get('outer stereo',  41.070)
        inner_stereo  = settings.get('inner stereo',  41.070)
        top_stereo    = settings.get('top stereo',    26.120)
        bottom_stereo = settings.get('bottom stereo', 26.120)

        fov_horizontal = outer_stereo + inner_stereo
        fov_vertical   = top_stereo  + bottom_stereo

        hmd_pos = np.array([
            trackers_arr[0]['pos x'],
            trackers_arr[0]['pos y'],
            trackers_arr[0]['pos z']
        ])
        hmd_rot = R.from_matrix(trackers_arr[0]['rotation matrix'])

        screen_x = hand_data[f'{hand_prefix} pos x']
        screen_y = hand_data[f'{hand_prefix} pos y']
        depth    = abs(hand_data[f'{hand_prefix} pos z'])

        ndc_x = (screen_x - 0.5) * 2.0
        ndc_y = (screen_y - 0.5) * 2.0

        fov_h_rad = np.radians(fov_horizontal / 2)
        fov_v_rad = np.radians(fov_vertical   / 2)

        cam_pos = np.array([
            depth * np.tan(fov_h_rad) * ndc_x,
            depth * np.tan(fov_v_rad) * ndc_y,
            -depth
        ])

        cam_mount = np.array([cam_offset_x, cam_offset_y, cam_offset_z])
        world_pos = hmd_pos + hmd_rot.apply(cam_mount + cam_pos)

        hand_rot_local = R.from_quat([
            hand_data[f'{hand_prefix} rot x'],
            hand_data[f'{hand_prefix} rot y'],
            hand_data[f'{hand_prefix} rot z'],
            hand_data[f'{hand_prefix} rot w']
        ])

        offset_yaw   = settings.get(f'{device} offset world yaw',   0.0)
        offset_pitch = settings.get(f'{device} offset world pitch', 0.0)
        offset_roll  = settings.get(f'{device} offset world roll',  0.0)
        offset_rot   = R.from_euler('ZYX', [offset_yaw, offset_pitch, offset_roll], degrees=False)

        world_rot  = hmd_rot * hand_rot_local * offset_rot
        final_quat = world_rot.as_quat()

        return {
            "pos x": world_pos[0],
            "pos y": world_pos[1],
            "pos z": world_pos[2],
            "rot x": final_quat[0],
            "rot y": final_quat[1],
            "rot z": final_quat[2],
            "rot w": final_quat[3]
        }

    except Exception as e:
        return {
            "pos x": 0.0,
            "pos y": 0.0,
            "pos z": 0.0,
            "rot x": 0.0,
            "rot y": 0.0,
            "rot z": 0.0,
            "rot w": 1.0
        }

#best offsets/////////////////////////////////////////////////////////////////////////////////////////////////////////
#right 2.560 -0.280 2.060
#left 3.860 0.190 1.990

def is_key_pressed_globally(vk_code):
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0

def get_vk_code(bind_str):
    import ctypes

    if bind_str.startswith("Mouse_"):
        mouse_map = {
            "Mouse_Left": 0x01, "Mouse_Right": 0x02, "Mouse_Middle": 0x04,
            "Mouse_M4": 0x05, "Mouse_M5": 0x06, "Mouse_Back": 0x05, "Mouse_Forward": 0x06,
        }
        return mouse_map.get(bind_str)

    if bind_str.startswith("Key_"):
        name = bind_str[4:]

        if len(name) == 1:
            res = ctypes.windll.user32.VkKeyScanA(ctypes.c_char(name.encode()))
            if res != -1 and (res & 0xFF) != 0xFF:
                return res & 0xFF

        if name.startswith("F") and name[1:].isdigit():
            fnum = int(name[1:])
            if 1 <= fnum <= 24:
                return 0x6F + fnum

        numpad = {
            "Numpad0": 0x60, "Numpad1": 0x61, "Numpad2": 0x62, "Numpad3": 0x63,
            "Numpad4": 0x64, "Numpad5": 0x65, "Numpad6": 0x66, "Numpad7": 0x67,
            "Numpad8": 0x68, "Numpad9": 0x69, "NumpadMultiply": 0x6A,
            "NumpadAdd": 0x6B, "NumpadSubtract": 0x6D, "NumpadDecimal": 0x6E,
            "NumpadDivide": 0x6F, "NumpadEnter": 0x0D,
        }
        if name in numpad:
            return numpad[name]

        if not hasattr(get_vk_code, "_vk_name_map"):
            vk_name_map = {}
            buf = ctypes.create_string_buffer(64)
            for vk in range(1, 256):
                scan = ctypes.windll.user32.MapVirtualKeyA(vk, 0)  # VK -> scan
                if scan == 0:
                    continue
                lparam = scan << 16
                if vk in (0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,
                          0x2D,0x2E,0x5B,0x5C,0x5D,0x2C,0x13):
                    lparam |= (1 << 24)
                res = ctypes.windll.user32.GetKeyNameTextA(lparam, buf, 64)
                if res > 0:
                    key_name = buf.value.decode(errors="ignore").strip()
                    vk_name_map[key_name.upper()] = vk
                    vk_name_map[key_name.upper().replace(" ", "")] = vk
                    vk_name_map[key_name.upper().replace(" ", "_")] = vk
            get_vk_code._vk_name_map = vk_name_map

        upper = name.upper()
        vk_map = get_vk_code._vk_name_map
        if upper in vk_map:
            return vk_map[upper]

        fallback = {
            "SPACE": 0x20, "RETURN": 0x0D, "ENTER": 0x0D, "ESCAPE": 0x1B,
            "ESC": 0x1B, "TAB": 0x09, "BACKSPACE": 0x08, "DELETE": 0x2E,
            "INSERT": 0x2D, "HOME": 0x24, "END": 0x23, "PAGEUP": 0x21,
            "PAGEDOWN": 0x22, "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27,
            "DOWN": 0x28, "SHIFT": 0x10, "CONTROL": 0x11, "CTRL": 0x11,
            "ALT": 0x12, "LSHIFT": 0xA0, "RSHIFT": 0xA1, "LCONTROL": 0xA2,
            "RCONTROL": 0xA3, "LCTRL": 0xA2, "RCTRL": 0xA3, "LALT": 0xA4,
            "RALT": 0xA5, "LWIN": 0x5B, "RWIN": 0x5C, "CAPSLOCK": 0x14,
            "NUMLOCK": 0x90, "SCROLLLOCK": 0x91, "PRINTSCREEN": 0x2C,
            "PAUSE": 0x13, "MENU": 0x5D, "APPS": 0x5D,
            "MINUS": 0xBD, "EQUAL": 0xBB, "BRACKETLEFT": 0xDB,
            "BRACKETRIGHT": 0xDD, "BACKSLASH": 0xDC, "SEMICOLON": 0xBA,
            "APOSTROPHE": 0xDE, "COMMA": 0xBC, "PERIOD": 0xBE,
            "SLASH": 0xBF, "GRAVE": 0xC0,
        }
        return fallback.get(upper)

    return None

def send_controller_data(is_right):
    pipe_name = PIPE_RIGHT if is_right else PIPE_LEFT
    device_name = "cr" if is_right else "cl"
    side = "right" if is_right else "left"

    while True:
        handle = None
        try:
            handle = create_pipe(pipe_name)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()

                final_transform = get_final_transform(device_name)
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings[f'{device_name}pos mode']:
                        case "offsets":
                            pos_x = float(settings.get(f"{device_name} offset world x", 0.0))
                            pos_y = float(settings.get(f"{device_name} offset world y", 0.0))
                            pos_z = float(settings.get(f"{device_name} offset world z", 0.0))

                        case "hand tracking":
                            if settings_core.get_settings()['hand tracking'] != False:
                                final_transform = get_hand_world_transform(device_name)

                                pos_x = final_transform['pos x']
                                pos_y = final_transform['pos y']
                                pos_z = final_transform['pos z']
                            else:
                                final_transform = get_final_transform(device_name)

                                pos_x = final_transform['pos x']
                                pos_y = final_transform['pos y']
                                pos_z = final_transform['pos z']
                        case _:
                            final_transform = get_final_transform(device_name)

                            pos_x = final_transform['pos x']
                            pos_y = final_transform['pos y']
                            pos_z = final_transform['pos z']

                except:
                    pass
                try:
                    match settings[f'{device_name}rot mode']:
                        case "offsets":
                            quat = euler_to_quat(settings[f"{device_name} offset world yaw"],
                                                 settings[f"{device_name} offset world pitch"],
                                                 settings[f"{device_name} offset world roll"])

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                        case "hand tracking":
                            if settings_core.get_settings()['hand tracking'] != False:
                                final_transform = get_hand_world_transform(device_name)

                                rot_x = final_transform['rot x']
                                rot_y = final_transform['rot y']
                                rot_z = final_transform['rot z']
                                rot_w = final_transform['rot w']
                            else:
                                final_transform = get_final_transform(device_name)

                                rot_x = final_transform['rot x']
                                rot_y = final_transform['rot y']
                                rot_z = final_transform['rot z']
                                rot_w = final_transform['rot w']

                        case "gyro":
                            quat = get_gyro(settings[f'{device_name} gyro id'])

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                        case _:
                            final_transform = get_final_transform(device_name)

                            rot_x = final_transform['rot x']
                            rot_y = final_transform['rot y']
                            rot_z = final_transform['rot z']
                            rot_w = final_transform['rot w']
                except:
                    pass
                
                prefix = "cl" if side == "left" else "cr"
                settings = settings_core.get_settings()

                trigger = eval_binding(settings.get(f"{prefix}_trigger", ""))
                a       = eval_binding(settings.get(f"{prefix}_a", "")) > 0.5
                b       = eval_binding(settings.get(f"{prefix}_b", "")) > 0.5
                grip    = eval_binding(settings.get(f"{prefix}_grip", "")) > 0.5
                menu    = eval_binding(settings.get(f"{prefix}_menu", "")) > 0.5

                touch_mod = eval_binding(settings.get(f"{prefix}_touch mod", "")) > 0.5

                joy_x = eval_binding(settings.get(f"{prefix}_joy right", "")) - eval_binding(settings.get(f"{prefix}_joy left", ""))
                joy_y = eval_binding(settings.get(f"{prefix}_joy up", "")) - eval_binding(settings.get(f"{prefix}_joy down", ""))
                joy_btn   = eval_binding(settings.get(f"{prefix}_joy click", "")) > 0.5

                touch_x = eval_binding(settings.get(f"{prefix}_touch right", "")) - eval_binding(settings.get(f"{prefix}_touch left", ""))
                touch_y = eval_binding(settings.get(f"{prefix}_touch up", "")) - eval_binding(settings.get(f"{prefix}_touch down", ""))
                touch_btn = eval_binding(settings.get(f"{prefix}_touch click", "")) > 0.5

                #touch: if no dedicated input for touch pad is mapped, you can hold the touch mode key and joy input will became touch input(index controller)
                if touch_mod:
                    touch_x = joy_x
                    touch_y = joy_y
                    touch_btn = joy_btn

                    joy_x = 0.0
                    joy_y = 0.0

                #skeletal input
                fingers = ["thumb", "index", "middle", "ring", "pinky"]

                if settings.get("curl",True):
                    flexion  = list(hand_data["l flexion"] if prefix == "cl" else hand_data["r flexion"])

                    for i, finger in enumerate(fingers):
                        val = eval_binding(settings.get(f"{prefix}_{finger}", ""))
                        if val > 0.01:
                            flexion[i * 4] = val

                    if settings.get("index=trigger", False):
                        if trigger < flexion[4]:
                            trigger = -1 + (flexion[4] * 3)

                    if settings.get("other=grip", False):
                        highest = max(flexion[8], flexion[12], flexion[16])
                        if grip < highest - 0.7:
                            grip = highest - 0.7

                else:
                    flexion = [0.0] * 20

                    for i, finger in enumerate(fingers):
                        val = eval_binding(settings.get(f"{prefix}_{finger}", ""))
                        if val > 0.01:
                            flexion[i * 4] = val

                if settings.get("splay",True):
                    splays_5 = list(hand_data["l splay"]   if prefix == "cl" else hand_data["r splay"])

                    if prefix == "cl":
                        splays_5 = hand_data["l splay"]
                    else:
                        splays_5 = hand_data["r splay"]

                # flexion[0] = 1.0 #thumb
                # flexion[4] = 1.0 #index
                # flexion[8] = 1.0 #middle
                # flexion[12] = 1.0 #ring
                # flexion[16] = 1.0 #pinky

                buffer = CONTROLLER_PACKER.pack(
                    float(pos_x), float(pos_y), float(pos_z),
                    float(rot_w), float(rot_x), float(rot_y), float(rot_z),
                    float(joy_x), float(joy_y),
                    float(touch_x), float(touch_y),
                    float(trigger),
                    *[float(f) for f in flexion],
                    *[float(s) for s in splays_5],
                    bool(a), bool(b), bool(menu),
                    bool(joy_btn), bool(touch_btn), bool(grip)
                )

                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        break
                    raise
                time.sleep(0.001)
                
        except Exception as e:
            pass
        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

def send_tracker_data(tracker_id):
    pipe_name = f"{PIPE_TRACKER_PREFIX}{tracker_id}"
    
    while True:
        handle = None
        try:
            handle = create_pipe(pipe_name)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()
                override = None

                final_transform = get_final_transform(f'{tracker_id}tracker')
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings.get(f"{tracker_id}trackerpos mode", "redirect"):
                        case "redirect":
                            pass

                        case "offsets":
                            pos_x = settings[f"{tracker_id}tracker offset world x"]
                            pos_y = settings[f"{tracker_id}tracker offset world y"]
                            pos_z = settings[f"{tracker_id}tracker offset world z"]

                        case "hip emulation":
                            pass

                        case _:
                            final_transform = get_final_transform(f'{tracker_id}tracker')

                            pos_x = final_transform['pos x']
                            pos_x = final_transform['pos y']
                            pos_x = final_transform['pos z']
                except:
                    pass
                try:
                    match settings.get(f"{tracker_id}trackerrot mode", "redirect"):
                        case "redirect":
                            pass

                        case "offsets":
                            quat = euler_to_quat(settings[f"{tracker_id}tracker offset world yaw"],
                                                 settings[f"{tracker_id}tracker offset world pitch"],
                                                 settings[f"{tracker_id}tracker offset world roll"])

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                        case "gyro":
                            quat = get_gyro(settings.get(f'{tracker_id}tracker gyro id',""))

                            rot_x = quat["x"]
                            rot_y = quat["y"]
                            rot_z = quat["z"]
                            rot_w = quat["w"]

                except:
                    pass
                buffer = TRACKER_PACKER.pack(
                    float(pos_x), float(pos_y), float(pos_z),
                    float(rot_w), float(rot_x), float(rot_y), float(rot_z)
                )
                
                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            pass
        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

def start_send_data():
    threads = []
    
    t_hmd = threading.Thread(target=send_hmd_data, daemon=True)
    t_hmd.start()
    threads.append(t_hmd)
    
    t_left = threading.Thread(target=lambda: send_controller_data(False), daemon=True)
    t_left.start()
    threads.append(t_left)
    
    t_right = threading.Thread(target=lambda: send_controller_data(True), daemon=True)
    t_right.start()
    threads.append(t_right)
    
    settings = settings_core.get_settings()
    max_trackers = settings.get('trackers num', 0)
    for tracker_id in range(max_trackers):
        t_tracker = threading.Thread(target=lambda tid=tracker_id: send_tracker_data(tid), daemon=True)
        t_tracker.start()
        threads.append(t_tracker)
    
    return threads

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def update_vrlabel():
    can_enter = True
    while True:
        if can_enter and is_prosses_running("vrserver.exe"):
            can_enter = False

            first_label.findChild(QLabel).setText("steamvr is running!")

            start_vr_utility()
            #steamvr opened

        if not can_enter and not is_prosses_running("vrserver.exe"):
            can_enter = True

            first_label.findChild(QLabel).setText("steamvr is not running :(")

            end_vr_utility()
            #steamvr closed

        time.sleep(1)

def start_update_vrlabel():
    t = threading.Thread(target=update_vrlabel, daemon=True)
    t.start()
    return t

trackers_dict = {}

def start_vr_utility():
    global trackers_dict, trackers_arr

    try:
        vr.init(vr.VRApplication_Utility)
        vr_system = vr.VRSystem()
        
        PROP_SERIAL = vr.Prop_SerialNumber_String
        PROP_MODEL = vr.Prop_ControllerType_String
        PROP_RENDER = vr.Prop_RenderModelName_String

        while True:
            try:
                poses = vr_system.getDeviceToAbsoluteTrackingPose(2, 0.0, vr.k_unMaxTrackedDeviceCount)
                
                new_dict = {}
                new_arr = []

                for i in range(vr.k_unMaxTrackedDeviceCount):
                    device_class = vr_system.getTrackedDeviceClass(i)
                    
                    if device_class in (vr.TrackedDeviceClass_HMD, 
                                      vr.TrackedDeviceClass_Controller, 
                                      vr.TrackedDeviceClass_GenericTracker, 
                                      vr.TrackedDeviceClass_TrackingReference):
                        
                        serial = vr_system.getStringTrackedDeviceProperty(i, PROP_SERIAL)
                        model = vr_system.getStringTrackedDeviceProperty(i, PROP_MODEL)
                        render = vr_system.getStringTrackedDeviceProperty(i, PROP_RENDER)
                        
                        role_hint = "Unknown"
                        if device_class in (vr.TrackedDeviceClass_Controller, vr.TrackedDeviceClass_GenericTracker):
                            role_enum = vr_system.getControllerRoleForTrackedDeviceIndex(i)
                            role_map = {
                                vr.TrackedControllerRole_LeftHand: "LeftHand",
                                vr.TrackedControllerRole_RightHand: "RightHand",
                                vr.TrackedControllerRole_OptOut: "OptOut",
                                vr.TrackedControllerRole_Treadmill: "Treadmill",
                                vr.TrackedControllerRole_Stylus: "Stylus"
                            }
                            role_hint = role_map.get(role_enum, "Tracker/Controller")
                        elif device_class == vr.TrackedDeviceClass_HMD:
                            role_hint = "HMD"
                        elif device_class == vr.TrackedDeviceClass_TrackingReference:
                            role_hint = "BaseStation"

                        pose = poses[i]
                        is_connected = pose.bDeviceIsConnected
                        is_valid = pose.bPoseIsValid

                        device_data = {
                            "index": i,
                            "class": device_class,
                            "model": model,
                            "render": render,
                            "role": role_hint,
                            "connected": is_connected,
                            "pose_valid": is_valid,
                            "serial": serial
                        }

                        if is_connected and is_valid:
                            m = pose.mDeviceToAbsoluteTracking
                            
                            pos_x, pos_y, pos_z = m[0][3], m[1][3], m[2][3]
                            
                            rotation_matrix = np.array([
                                [m[0][0], m[0][1], m[0][2]],
                                [m[1][0], m[1][1], m[1][2]],
                                [m[2][0], m[2][1], m[2][2]]
                            ])

                            device_data.update({
                                "pos x": pos_x,
                                "pos y": pos_y,
                                "pos z": pos_z,
                                "rotation matrix": rotation_matrix
                            })

                            new_arr.append({
                                "pos x": pos_x,
                                "pos y": pos_y,
                                "pos z": pos_z,
                                "rotation matrix": rotation_matrix
                            })

                        new_dict[serial] = device_data

                trackers_dict = new_dict
                trackers_arr = new_arr

                update_found_label()
                time.sleep(0.001)

            except Exception as e:
                time.sleep(0.001)
                continue

    except Exception as e:
        time.sleep(1)
        start_vr_utility()

def end_vr_utility():
    vr.shutdown()

def update_found_label():
    global trackers_dict
    display_text = ""
    count = 0
    for serial, data in trackers_dict.items():
        display_text += f'[{count}] '
        display_text += f"ROLE: {data['role']} | {data['model']}\n"
        display_text += f"Serial: {serial}\n"
        
        if data.get('connected'):# and data.get('pose_valid'):
            px, py, pz = data['pos x'], data['pos y'], data['pos z']
            display_text += f"Pos: X:{px:+.3f} Y:{py:+.3f} Z:{pz:+.3f}\n"
            
            if "rotation matrix" in data:
                m = data['rotation matrix']
                display_text += "Rot Matrix:\n"
                display_text += f"  [{m[0][0]:+.2f}, {m[0][1]:+.2f}, {m[0][2]:+.2f}]\n"
                display_text += f"  [{m[1][0]:+.2f}, {m[1][1]:+.2f}, {m[1][2]:+.2f}]\n"
                display_text += f"  [{m[2][0]:+.2f}, {m[2][1]:+.2f}, {m[2][2]:+.2f}]\n"
        else:
            display_text += "OFFLINE"# OR UNTRACKED\n"
        
        display_text += "-----------------------------------\n"

        count += 1

    try:
        label = trackers_label1.findChild(QLabel)
        if label:
            label.setText(display_text)
    except Exception as e:
        pass

#camera (hand tracking)//////////////////////////////////////////////////////////////////////////////////////////////////
SHOW_FEED           = True
RESOLUTION_X        = 640
RESOLUTION_Y        = 480
SWAP_HANDS_MODE     = False

REFERENCE_DEPTH_CM  = 0.5
REFERENCE_BBOX = 200.0

ref_3d_mag_right    = 0.08
ref_3d_mag_left     = 0.08

hand_data = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "l pos x": 0.0, "l pos y": 0.0, "l pos z": 0.0,
    "l rot x": 0.0, "l rot y": 0.0, "l rot z": 0.0, "l rot w": 1.0,

    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
    "r pos x": 0.0, "r pos y": 0.0, "r pos z": 0.0,
    "r rot x": 0.0, "r rot y": 0.0, "r rot z": 0.0, "r rot w": 1.0,
}

camera_running = False
camera_thread  = None
camera_ready   = threading.Event()

def _vec(l1, l2):
    return np.array([l2[0]-l1[0], l2[1]-l1[1], l2[2]-l1[2]], dtype=float)

def _angle(v1, v2):
    n = np.linalg.norm(v1) * np.linalg.norm(v2)
    return np.arccos(np.clip(np.dot(v1, v2) / n, -1.0, 1.0)) if n > 1e-9 else 0.0

def _norm01(v, lo, hi):
    return float(np.clip((v - lo) / (hi - lo), 0.0, 1.0)) if hi != lo else 0.0

def _mat_to_quat(m):
    tr = m[0,0] + m[1,1] + m[2,2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        return (m[2,1]-m[1,2])/s, (m[0,2]-m[2,0])/s, (m[1,0]-m[0,1])/s, 0.25*s
    elif (m[0,0] > m[1,1]) and (m[0,0] > m[2,2]):
        s = np.sqrt(1.0 + m[0,0] - m[1,1] - m[2,2]) * 2
        return 0.25*s, (m[0,1]+m[1,0])/s, (m[0,2]+m[2,0])/s, (m[2,1]-m[1,2])/s
    elif m[1,1] > m[2,2]:
        s = np.sqrt(1.0 + m[1,1] - m[0,0] - m[2,2]) * 2
        return (m[0,1]+m[1,0])/s, 0.25*s, (m[1,2]+m[2,1])/s, (m[0,2]-m[2,0])/s
    else:
        s = np.sqrt(1.0 + m[2,2] - m[0,0] - m[1,1]) * 2
        return (m[0,2]+m[2,0])/s, (m[1,2]+m[2,1])/s, 0.25*s, (m[1,0]-m[0,1])/s


FINGER_BASES  = [1, 5, 9, 13, 17]
FINGER_TIPS   = [4, 8, 12, 16, 20]
FINGER_MIDS   = [3, 7, 11, 15, 19]

FLEXION_MIN, FLEXION_MAX     = 0.0, 20.5
SPLAY_THUMB_MIN,  SPLAY_THUMB_MAX  = 0.0, 20.0
SPLAY_FINGER_MIN, SPLAY_FINGER_MAX = 0.0, 20.35

def _process_hand(lm_list, is_right, img_w, img_h):
    prefix = "r" if is_right else "l"

    P = [(r[0], r[1]) for r in lm_list]

    P3 = [(r[0]/img_w, 1.0-(r[1]/img_h), -r[2]) for r in lm_list]

    #pos////////////////////////////////////////////////////////////////////////////////////////////
    wx, wy = P[0]
    hand_data[f"{prefix} pos x"] = wx / img_w
    hand_data[f"{prefix} pos y"] = 1.0 - (wy / img_h)

    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    bbox_size = max(max(xs) - min(xs), max(ys) - min(ys))
    raw_z = -(REFERENCE_DEPTH_CM * REFERENCE_BBOX / bbox_size) if bbox_size > 1 else -REFERENCE_DEPTH_CM
    hand_data[f"{prefix} pos z"] = raw_z

    #rot////////////////////////////////////////////////////////////////////////////////////////////
    p_wrist  = np.array(P3[0],  dtype=float)
    p_index  = np.array(P3[5],  dtype=float)
    p_middle = np.array(P3[9],  dtype=float)
    p_pinky  = np.array(P3[17], dtype=float)

    v_fwd_raw = p_middle - p_wrist
    v_fwd_raw /= np.linalg.norm(v_fwd_raw) + 1e-6
    v_z = -v_fwd_raw

    if is_right:
        v_right_raw = p_pinky - p_index
    else:
        v_right_raw = p_index - p_pinky
    v_right_raw /= np.linalg.norm(v_right_raw) + 1e-6

    v_y = np.cross(v_z, v_right_raw)
    v_y /= np.linalg.norm(v_y) + 1e-6

    v_x = np.cross(v_y, v_z)
    v_x /= np.linalg.norm(v_x) + 1e-6

    mat = np.stack([v_x, v_y, v_z], axis=1)
    qx, qy, qz, qw = _mat_to_quat(mat)

    if v_x[2] > 0:
        qx, qy, qz, qw = -qx, -qy, -qz, -qw

    hand_data[f"{prefix} rot x"] = qx
    hand_data[f"{prefix} rot y"] = qy
    hand_data[f"{prefix} rot z"] = qz
    hand_data[f"{prefix} rot w"] = qw
    
    #curl////////////////////////////////////////////////////
    finger_lms = [
        (1,  2,  3,  4),
        (5,  6,  7,  8),
        (9,  10, 11, 12),
        (13, 14, 15, 16),
        (17, 18, 19, 20),
    ]
    flexion = [0.0] * 20
    curl_values = []

    for fi, (base, k1, k2, tip) in enumerate(finger_lms):
        pb   = np.array(P[base], dtype=float)
        pk1  = np.array(P[k1],   dtype=float)
        ptip = np.array(P[tip],  dtype=float)

        if fi == 0:
            p1, p2, p3, p4 = [np.array(P[i], dtype=float) for i in range(1, 5)]
            total_angle = _angle(p1-p2, p3-p2) + _angle(p2-p3, p4-p3)
            curl = _norm01(total_angle, 6.0, 4.5)
            flexion[fi * 4] = curl
            curl_values.append(curl)
        else:
            seg_len  = np.linalg.norm(pk1 - pb)
            extended = seg_len * 3.0
            actual   = np.linalg.norm(ptip - pb)
            curl     = 1.0 - np.clip(actual / (extended + 1e-6), 0.0, 1.0)
            flexion[fi * 4] = curl
            curl_values.append(curl)

    hand_data[f"{prefix} flexion"] = flexion

    #curl also affect pos, that a bug, this should fix that///////////////////////////////////////////////////////////////////
    wx, wy = P[0]
    hand_data[f"{prefix} pos x"] = wx / img_w
    hand_data[f"{prefix} pos y"] = 1.0 - (wy / img_h)

    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    bbox_size = max(max(xs) - min(xs), max(ys) - min(ys))
    raw_z = -(REFERENCE_DEPTH_CM * REFERENCE_BBOX / bbox_size) if bbox_size > 1 else -REFERENCE_DEPTH_CM
    
    global_min_curl = min(curl_values) 
    
    z_offset = global_min_curl * 0.28 
    final_z = raw_z + z_offset

    hand_data[f"{prefix} pos z"] = final_z
    
    #splay/////////////////////////////////////////////////////////////////////////////////
    splay_range = 0.1
    splay = [0.0] * 5

    p_w = np.array(P3[0],  dtype=float) 
    tips = [
        np.array(P3[4],  dtype=float),#thumb
        np.array(P3[8],  dtype=float),#index
        np.array(P3[12], dtype=float),#mid
        np.array(P3[16], dtype=float),#ring
        np.array(P3[20], dtype=float)#pinky
    ]

    def get_angle(t1, t2, wrist):
        v1, v2 = t1 - wrist, t2 - wrist
        u1 = v1 / (np.linalg.norm(v1) + 1e-6)
        u2 = v2 / (np.linalg.norm(v2) + 1e-6)
        return np.arccos(np.clip(np.dot(u1, u2), -1.0, 1.0))

    def map_splay_dynamic(angle, min_a, max_a, r_scale):
        n = (angle - min_a) / (max_a - min_a + 1e-6)
        n = np.clip(n, 0.0, 1.0)
        
        return ((n ** 0.3) * 2.0 - 1.0) * r_scale

    splay[0] = map_splay_dynamic(get_angle(tips[0], tips[1], p_w), 0.10, 0.40, splay_range)
    splay[1] = map_splay_dynamic(get_angle(tips[1], tips[2], p_w), 0.05, 0.20, splay_range)*5
    splay[2] = map_splay_dynamic(get_angle(tips[2], tips[3], p_w), 0.05, 0.18, splay_range)*5
    splay[3] = map_splay_dynamic(get_angle(tips[3], tips[4], p_w), 0.05, 0.20, splay_range)*5
    splay[4] = map_splay_dynamic(get_angle(tips[3], tips[4], p_w), 0.05, 0.22, splay_range)*5

    hand_data[f"{prefix} splay"] = splay

hand_side_buffer = [0, 0] 
side_threshold = 1
last_known_x = {"l": 0.1, "r": 0.9}

def camera_loop():
    global camera_running, last_known_x

    try:
        idx = settings_core.get_settings().get("camera index", 0)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            camera_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  RESOLUTION_X)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_Y)

        detector = HandDetector(maxHands=2, detectionCon=0.5, minTrackCon=0.5)
        camera_ready.set()

        while camera_running:
            success, image = cap.read()
            if not success:
                time.sleep(0.001)
                continue

            try:
                hands_found, image = detector.findHands(image, draw=True)
            except Exception as e:
                continue

            if hands_found:
                h, w = image.shape[:2]
                num_hands = len(hands_found)

                current_hands = []
                for i in range(num_hands):
                    raw_lms = detector.results.multi_hand_landmarks[i].landmark
                    current_hands.append({
                        "x": raw_lms[0].x, 
                        "raw_lms": raw_lms
                    })

                assignments = []
                if num_hands == 2:
                    sorted_hands = sorted(current_hands, key=lambda x: x["x"])
                    assignments = [("l", sorted_hands[0]), ("r", sorted_hands[1])]
                else:
                    hand = current_hands[0]
                    dist_l = abs(hand["x"] - last_known_x["l"])
                    dist_r = abs(hand["x"] - last_known_x["r"])
                    side = "l" if dist_l < dist_r else "r"
                    assignments = [(side, hand)]

                for side, hand_info in assignments:
                    prefix = side
                    is_right = (side == "r")
                    label = "Right" if is_right else "Left"
                    
                    last_known_x[side] = hand_info["x"]

                    lm = [[int(l.x * w), int(l.y * h), l.z] for l in hand_info["raw_lms"]]
                    _process_hand(lm, is_right, w, h)

                    try:
                        px, py, pz = hand_data[f"{prefix} pos x"], hand_data[f"{prefix} pos y"], hand_data[f"{prefix} pos z"]
                        rx, ry, rz, rw = hand_data[f"{prefix} rot x"], hand_data[f"{prefix} rot y"], hand_data[f"{prefix} rot z"], hand_data[f"{prefix} rot w"]
                        fl = hand_data[f"{prefix} flexion"]
                        sp = hand_data[f"{prefix} splay"]

                        cx, cy = lm[0][0], lm[0][1]
                        lines = [
                            f"{label} pos x:{px:.2f} y:{py:.2f} z:{pz:.3f}",
                            f"rot x:{rx:.2f} y:{ry:.2f} z:{rz:.2f} w:{rw:.2f}",
                            f"flex T:{fl[0]:.2f} I:{fl[4]:.2f} M:{fl[8]:.2f} R:{fl[12]:.2f} P:{fl[16]:.2f}",
                            f"splay T:{sp[0]:.2f} I:{sp[1]:.2f} M:{sp[2]:.2f} R:{sp[3]:.2f} P:{sp[4]:.2f}",
                        ]
                        for j, line in enumerate(lines):
                            cv2.putText(image, line, (cx, cy - 20 - j*18),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0), 1)
                    except KeyError:
                        continue

            if SHOW_FEED:
                cv2.imshow("Hand Tracking", image)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    camera_running = False

            time.sleep(0.0001)

    except Exception as e:
        import traceback
        camera_running = False
    finally:
        cap.release()
        cv2.destroyAllWindows()


def start_camera():
    global camera_running, camera_thread

    if camera_running:
        camera_running = False
        if camera_thread:
            camera_thread.join(timeout=2.0)
        time.sleep(0.2)

    camera_ready.clear()

    if settings_core.get_settings().get("hand tracking"):
        camera_running = True
        camera_thread  = threading.Thread(target=camera_loop, daemon=True)
        camera_thread.start()

        if not camera_ready.wait(timeout=3.0):
            camera_running = False
#camera//////////////////////////////////////////////////////////////////////////////////////////////////

first_label = create_label({
    "text" : "steamvr is not running :(", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})

layout_main.addWidget(create_label({
    "text" : "---------Resolution---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

res = create_group_horizontal([
    {
        "type" : "spinbox", 
        "text" :"X", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['resolution x'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("resolution x", res.findChildren(QSpinBox)[0].value())
    },
    {
        "type" : "spinbox", 
        "text" :"Y", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['resolution y'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("resolution y", res.findChildren(QSpinBox)[1].value())
    },
    {
        "type" : "spinbox", 
        "text" :"Refresh Rate", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['refresh rate'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("refresh rate", res.findChildren(QSpinBox)[2].value())
    }
])
layout_main.addWidget(res)

layout_main.addWidget(create_label({
    "text" : "---------Misc---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
misc_group1 = create_group_checkbox([
    {
        "text" : "Stereoscopic(SBS)", 
        "default" : settings_core.get_settings()['stereoscopic'], 
        "func" : lambda: settings_core.update_setting("stereoscopic", misc_group1.findChildren(QCheckBox)[0].isChecked())
    },
    {
        "text" : "Fullscreen", 
        "default": settings_core.get_settings()['fullscreen'],
        "func"  : lambda: settings_core.update_setting("fullscreen", misc_group1.findChildren(QCheckBox)[1].isChecked())
    }
])
layout_main.addWidget(misc_group1)

misc = create_group_doublespinbox([
    {
        "text" : "IPD", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['ipd'] * 1000, 
        "steps" : 1.0,
        "func" : lambda: settings_core.update_setting("ipd", misc.findChildren(QDoubleSpinBox)[0].value() * 0.001)
    },
    {
        "text" : "Distance from tracker to eyes", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['head to eye dist'], 
        "steps" : 0.1, 
        "func" : lambda: settings_core.update_setting("head to eye dist", misc.findChildren(QDoubleSpinBox)[1].value()) 
    }
])
layout_main.addWidget(misc)

def calculate_vr_fov():
    settings_core.update_setting("convergence", recommended_label.findChildren(QDoubleSpinBox)[0].value())
    settings_core.update_setting("fov", recommended_label.findChildren(QDoubleSpinBox)[1].value())

    settings = settings_core.get_settings()

    diagonal_fov_deg = settings.get("fov", 0.0)
    convergence_deg = settings.get('convergence', 0.0)

    width = settings['resolution x']
    height = settings['resolution y']

    diag_rad = math.radians(diagonal_fov_deg)
    aspect = width / height
    
    tan_half_diag = math.tan(diag_rad / 2)
    tan_half_v = tan_half_diag / math.sqrt(aspect**2 + 1)
    tan_half_h = aspect * tan_half_v
    
    h_half_fov = math.degrees(math.atan(tan_half_h))
    v_half_fov = math.degrees(math.atan(tan_half_v))

    outer_fov_deg = h_half_fov + convergence_deg
    inner_fov_deg = h_half_fov - convergence_deg
    
    top_fov_deg = v_half_fov
    bottom_fov_deg = v_half_fov

    outer_fov_deg = max(0.0, outer_fov_deg)
    inner_fov_deg = max(0.0, inner_fov_deg)

    settings_core.update_setting("outer stereo", outer_fov_deg)
    settings_core.update_setting("inner stereo", inner_fov_deg)
    settings_core.update_setting("top stereo", top_fov_deg)
    settings_core.update_setting("bottom stereo", bottom_fov_deg)
    settings_core.update_setting("outer mono", outer_fov_deg)
    settings_core.update_setting("inner mono", inner_fov_deg)
    settings_core.update_setting("top mono", top_fov_deg)
    settings_core.update_setting("bottom mono", bottom_fov_deg)

recommended_label = create_group_horizontal([
    {
        "type" : "doublespinbox",
        "text" : "convergence",
        "min":-999999999,
        "max":999999999,
        "default": settings_core.get_settings()['convergence'],
        "steps" : 0.01,
        "func"  : lambda: calculate_vr_fov()
    },{
        "type" : "doublespinbox",
        "text" : "FOV",
        "min":-999999999,
        "max":999999999,
        "default": settings_core.get_settings()['fov'],
        "steps" : 0.01,
        "func"  : lambda: calculate_vr_fov()
    }])

layout_main.addWidget(recommended_label)

layout_main.addWidget(create_label({
    "text" : "---------Offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world x", offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world y", offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world z", offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world yaw", offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world pitch", offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world roll", offsets_world.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_main.addWidget(offsets_world)

offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local x", offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local y", offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local z", offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local yaw", offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local pitch", offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local roll", offsets_local.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_main.addWidget(offsets_local)
#main/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#driver/////////////////////////////////////////////////////////////////////////////////////////////////////////////
def set_activateMultipleDrivers_true():
    file_path = settings_core.get_settings()['vrsettings path'] + "/steamvr.vrsettings"
    #C:\Program Files (x86)\Steam\config\steamvr.vrsettings
    #"activateMultipleDrivers" : true,
    try:
        if not os.path.exists(file_path):
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        if "steamvr" not in data:
            data["steamvr"] = {}
        
        if data["steamvr"].get("activateMultipleDrivers") is True:
            return

        data["steamvr"]["activateMultipleDrivers"] = True

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        pass

def get_activateMultipleDrivers_true():
    file_path = settings_core.get_settings()['vrsettings path'] + "/steamvr.vrsettings"
    #C:\Program Files (x86)\Steam\config\steamvr.vrsettings
    #"activateMultipleDrivers" : true,
    try:
        if not os.path.exists(file_path):
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        if "steamvr" not in data:
            data["steamvr"] = {}
            return False
        
        if data["steamvr"].get("activateMultipleDrivers") is True:
            return True
        
        return False

    except Exception as e:
        return False

set_activateMultipleDrivers_true()

def install_driver():
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    source_folder = os.path.join(script_dir, "assets", "driver to copy")

    destination_folder = settings_core.get_settings()['drivers path']
    
    if not os.path.exists(source_folder):
        update_install_and_config_label(True)
        return

    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        update_install_and_config_label(False)
    except Exception as e:
        update_install_and_config_label(True)

def remove_driver():
    folder_path = settings_core.get_settings()['drivers path'] + '/glassvrdriver'

    if not os.path.exists(folder_path):
            return

    try:
        shutil.rmtree(folder_path)
        update_install_and_config_label(False)

    except:
        update_install_and_config_label(True)

tab_driver = QWidget()
layout_driver = QVBoxLayout(tab_driver)
layout_driver.setSpacing(0)

def folder_exist(path: str):
    return os.path.isdir(path)

def driver_path_changed():
    set_activateMultipleDrivers_true()
    settings_core.update_setting('drivers path',driver_path.findChild(QLineEdit).text())
    update_install_and_config_label()

def config_path_changed():
    set_activateMultipleDrivers_true()
    settings_core.update_setting('vrsettings path',vr_config_path.findChild(QLineEdit).text())
    update_install_and_config_label()

driver_path = create_lineedit({
    "text" : "steamvr drivers folder path",
    "default" : settings_core.get_settings()['drivers path'],
    "func" : lambda: driver_path_changed()
})
layout_driver.addWidget(driver_path)
vr_config_path = create_lineedit({
    "text" : "steam config folder path",
    "default" : settings_core.get_settings()['vrsettings path'],
    "func" : lambda: config_path_changed()
})
layout_driver.addWidget(vr_config_path)

install_label = create_label({
    "text" : "driver is not installed, click to install to install!", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(install_label)

config_label = create_label({
    "text" : "config", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(config_label)

install_buttons = create_group_horizontal([
    {
        "type" : "button", 
        "text" : "install", 
        "enabled" : True,
        "func"  : lambda: install_driver()
    },
    {
        "type" : "button", 
        "text" : "uninstall", 
        "enabled" : True,
        "func"  : lambda: remove_driver()
    }
])
layout_driver.addWidget(install_buttons)

def update_install_and_config_label(failed = False):
    install_leb =  install_label.findChild(QLabel)
    config_leb =  config_label.findChild(QLabel)

    if failed:
        install_leb.setText("action failed, close steam completely and try again")
        install_buttons.findChildren(QPushButton)[0].setText("install")
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            install_leb.setText("driver is installed!")
            install_buttons.findChildren(QPushButton)[0].setText("reinstall")
            install_buttons.findChildren(QPushButton)[1].setEnabled(True)
        else:
            install_leb.setText("driver is not installed, click to install to install!")
            install_buttons.findChildren(QPushButton)[0].setText("install")
            install_buttons.findChildren(QPushButton)[1].setEnabled(False)

    #//////////////////////////////////////////////////////////////////////////////////////////////

    if get_activateMultipleDrivers_true():
        config_leb.setText("steamvr.vrsettings has activateMultipleDrivers : true, all good :)")
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            config_leb.setText("steamvr.vrsettings is missing: activateMultipleDrivers : false, set the correct path and click to reinstall to add it!")
        else:
            config_leb.setText("steamvr.vrsettings is missing: activateMultipleDrivers : false, set the correct path and click to install to add it!")

update_install_and_config_label()

layout_driver.addWidget(create_label({
    "text" : "---------Config---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
layout_driver.addWidget(create_button({
        "text" : "reset config(ui won't update)",
        "enabled" : True,
        "func"  : lambda: settings_core.reset_settings()
    }))
config = create_group_horizontal([{
        "type" : "button", 
        "text" : "open config", 
        "enabled" : True,
        "func"  : lambda: os.startfile(settings_core.get_path())#.removesuffix("\settings.json"))
    },
    {"type" : "label",
     "text" :settings_core.get_path().removesuffix("\settings.json"),
     "alignment" : Qt.AlignmentFlag.AlignCenter
    }])
layout_driver.addWidget(config)

config2 = create_group_horizontal([{
        "type" : "button", 
        "text" : "open steamvr.vrsettings", 
        "enabled" : True,
        "func"  : lambda: os.startfile(settings_core.get_settings()["vrsettings path"] + "\steamvr.vrsettings")#.removesuffix("\settings.json"))
    },
    {"type" : "label",
     "text" : settings_core.get_settings()["vrsettings path"],
     "alignment" : Qt.AlignmentFlag.AlignCenter
    }])
layout_driver.addWidget(config2)

#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.RequestException:
        return "NO INTERNET???"
    
def list_mac_addresses():
    interfaces = psutil.net_if_addrs()
    for interface_name, snics in interfaces.items():
        for snic in snics:
            if snic.family in (psutil.AF_LINK, -1):
                #p(f"Interface: {interface_name}")
                #p(f"  MAC Address: {snic.address}")
                #get first mac address
                return snic.address

dialog = 0
def click():
    global dialog

    match dialog:
        case 0:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "OUCH!!!!!!!!!!!", ":)", 0)
            ctypes.windll.user32.MessageBoxW(0, "why???????????????", ":)", 0)
        case 1:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "STOP!!!!", ":)", 0)
        case 2:
            ctypes.windll.user32.MessageBoxW(0, "if i'll show you something cool, will you stop clicking?", ":)", 0)
            dialog += 1
            webbrowser.open("https://danixmir.itch.io/hyperlost")
            ctypes.windll.user32.MessageBoxW(0, "its a game i made!", ":>", 0)
        case 3:
            response = ctypes.windll.user32.MessageBoxW(0, "do you like it?", ":)", 4)
            if response == 6:
                dialog += 1
                ctypes.windll.user32.MessageBoxW(0, "thank you!!!", ":)", 0)
            else:
                system = platform.system()
                if system == "Windows":
                    os.system("shutdown /p")#"shutdown /p" #"shutdown /s /t"
                elif system == "Linux" or system == "Darwin":
                    os.system("sudo shutdown -h now")
        case 4:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "AHH!!!!!!!!!!!!!!!!!!!!!!!!", ":)", 0)
        case 5:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you promised you'll stop", ":)", 0)
        case 6:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i feel betrayed", ":)", 0)
        case 7:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 8:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "go do something else!!!!!!!!", ":)", 0)
        case 9:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "can you stop??????????", ":)", 0)
        case 10:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "plz stop", ":)", 0)
        case 11:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i have nothing more to show you", ":)", 0)
        case 12:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "(ignores)", ":)", 0)
        case 13:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i know where you live", ":)", 0)
        case 14:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "ip: " + get_public_ip() + "\nmac: " + list_mac_addresses(), ":)", 0)
        case 15:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "now will you stop?", ":)", 0)
        case 16:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i don't understand", ":)", 0)
        case 17:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "since when you were the one in control?", ":)", 0)
        case 18:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "hehe, that was a reference", ":)", 0)
        case 19:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "seriously stop", ":)", 0)
        case 20:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you don't know what you're doing", ":)", 0)
        case 21:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "YOU WILL KILL US BOTH", ":)", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "or not", ":)", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "this is the last straw", ":)", 0)
        case 23:
            dialog += 1
            os.startfile("C:\Windows\System32")
            ctypes.windll.user32.MessageBoxW(0, "I'M GONNA DO IT", ":)", 0)
        case 24:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "wow", ":)", 0)
        case 25:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i give up", ":)", 0)
        case 26:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 27:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 28:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 29:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "so.....?", ":)", 0)
        case 30:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "error", "Alert", 0)
        case 31:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "click one more time i dare you", ":)", 0)
        case 32:
            dialog += 1
            for n in range(2147483647):
                time.sleep(0.01)
                webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        case 34:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you know what, you win", ":)", 0)
        case 35:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "the next dialog is the last, check the source code if you don't believe me", ":)", 0)
        case _:
            ctypes.windll.user32.MessageBoxW(0, ";P", ";P", 0)

tab_credits = QWidget()
layout_credits = QVBoxLayout(tab_credits)
layout_credits.setSpacing(0)

def create_credits():
    create_group = QWidget()
    layout_credits1 = QVBoxLayout(create_group)

    label = QLabel("Made by: DaniXmir")# ;P
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)

    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    image_path = os.path.join(script_dir, "assets", "fix")

    image_button = QPushButton()
    image = QPixmap(image_path)
    scaled_pixmap = image.scaled(
        100, 100, 
        Qt.AspectRatioMode.KeepAspectRatio, 
        Qt.TransformationMode.FastTransformation
    )
    image_button.setIcon(QIcon(scaled_pixmap))
    image_button.setIconSize(QSize(100, 100))
    image_button.setStyleSheet("QPushButton { border: none; background: none; }")
    image_button.clicked.connect(lambda: click())
    layout_credits1.addWidget(image_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    group_links = QWidget()
    layout_link = QHBoxLayout(group_links)
    
    #todo: add icons!
    link = '<a href="https://github.com/DaniXmir/GlassVr" style="color: #4da6ff;">github!</a>'
    label1 = QLabel("open the project on " + link)
    label1.setTextFormat(Qt.TextFormat.RichText)
    label1.setOpenExternalLinks(True)
    label1.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_link.addWidget(label1)

    link = '<a href="https://discord.gg/jyvWdKBpPj" style="color: #4da6ff;">discord server!</a>'
    label2 = QLabel("join the " + link)
    label2.setTextFormat(Qt.TextFormat.RichText)
    label2.setOpenExternalLinks(True)
    label2.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_link.addWidget(label2)

    layout_credits1.addWidget(group_links)

    return create_group
layout_credits.addWidget(create_credits())
#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_controllers = QWidget()
layout_controllers = QVBoxLayout(tab_controllers)
layout_controllers.setSpacing(0)

scroll_controllers = QScrollArea()
scroll_controllers.setWidgetResizable(True)
scroll_controllers.setWidget(tab_controllers)

scroll_controllers.setMinimumWidth(1800)

#/////////////
tab_enable = QWidget()
layout_enable = QHBoxLayout(tab_enable)

check_cr = create_checkbox(
    {
        "text" : "enable left controller", 
        "default" : settings_core.get_settings()['enable cl'], 
        "func" : lambda: settings_core.update_setting("enable cl",check_cr.findChild(QCheckBox).isChecked())
    })
layout_enable.addWidget(check_cr)

label3 = create_label({
    "text" : "<- left (enable) right ->", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_enable.addWidget(label3)

check_cl = create_checkbox(
    {
        "text" : "enable right controller", 
        "default" : settings_core.get_settings()['enable cr'], 
        "func" : lambda: settings_core.update_setting("enable cr",check_cl.findChild(QCheckBox).isChecked())
    })
layout_enable.addWidget(check_cl)
layout_controllers.addWidget(tab_enable)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cr modes//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crpos_specific_widget(layout, combo):
    settings_core.update_setting(f'crpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        case "keyboard":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

        case "hand tracking":
            t = create_label({"text" : ""})
            
            layout.addWidget(t)

        case "marker":
            t = create_group_horizontal([{
            "type" : "spinbox", 
            "text" :"controller index", 
            "min":0, 
            "max":999999999, 
            "default": settings_core.get_settings().get(f'cr gyro index',0), 
            "steps" : 1,
            "func"  : lambda: settings_core.update_setting("cr gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_crpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right position mode",
            "default": settings.get(f'crpos mode', "redirect"),
            "items": ["redirect", "offsets", "hand tracking"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_crpos_widget())
#pos///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crrot_specific_widget(layout, combo):
    settings_core.update_setting(f'crrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    #settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "button",
                    "enabled" : True,
                    "text" :"apply recommendet offsets", 
                    "func"  : lambda: apply_hand_offsets("cr")
                }])
            layout.addWidget(t)

        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings_core.get_settings()["cr gyro id"],
                    "items": list(controllers_dict),
                    "func": lambda: settings_core.update_setting("cr gyro id", combo_extra.findChildren(QComboBox)[0].currentText())
                })
            
            layout.addWidget(combo_extra)
            
        case "marker":
            t = create_group_horizontal([{
            "type" : "spinbox", 
            "text" :"controller index", 
            "min":0, 
            "max":999999999, 
            "default": settings_core.get_settings().get(f'cr gyro index',0), 
            "steps" : 1,
            "func"  : lambda: settings_core.update_setting("cr gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)      

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_crrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right rotation mode",
            "default": settings.get(f'crrot mode', "redirect"),
            "items": ["redirect", "offsets", "hand tracking", "gyro"],# "hand+gyro", "marker", "marker+gyro",#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_crrot_widget())
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cr modes////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cl modes////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def clpos_specific_widget(layout, combo):
    settings_core.update_setting(f'clpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        case "keyboard":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

        case "hand tracking":
            t = create_label({"text" : ""})
            
            layout.addWidget(t)

        case "marker":
            t = create_group_horizontal([{
            "type" : "spinbox", 
            "text" :"controller index", 
            "min":0, 
            "max":999999999, 
            "default": settings_core.get_settings().get(f'cr gyro index',0), 
            "steps" : 1,
            "func"  : lambda: settings_core.update_setting("cr gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_clpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left position mode",
            "default": settings.get(f'clpos mode', "redirect"),
            "items": ["redirect", "offsets", "hand tracking"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_clpos_widget())
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def clrot_specific_widget(layout, combo):
    settings_core.update_setting(f'clrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "button",
                    "enabled" : True,
                    "text" :"apply recommendet offsets", 
                    "func"  : lambda: apply_hand_offsets("cl")
                }])
            layout.addWidget(t)

        case "marker":
            t = create_group_horizontal([{
            "type" : "spinbox", 
            "text" :"controller index", 
            "min":0, 
            "max":999999999, 
            "default": settings_core.get_settings().get(f'cr gyro index',0), 
            "steps" : 1,
            "func"  : lambda: settings_core.update_setting("cr gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings_core.get_settings()["cl gyro id"],
                    "items": list(controllers_dict),
                    "func": lambda: settings_core.update_setting("cl gyro id", combo_extra.findChildren(QComboBox)[0].currentText())
                })
            
            layout.addWidget(combo_extra)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_clrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left rotation mode",
            "default": settings.get(f'clrot mode', "redirect"),
            "items": ["redirect", "offsets", "hand tracking", "gyro"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_clrot_widget())
#rot///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cl modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def apply_hand_offsets(device):
    if device == "cr":
        settings_core.update_setting(f"{device} offset world yaw", 1.660)
        cr_offsets_world.findChildren(QDoubleSpinBox)[3].setValue(1.660)

        settings_core.update_setting(f"{device} offset world pitch", -0.680)
        cr_offsets_world.findChildren(QDoubleSpinBox)[4].setValue(-0.680)

        settings_core.update_setting(f"{device} offset world roll", 0.670)
        cr_offsets_world.findChildren(QDoubleSpinBox)[5].setValue(0.670)

    else:
        settings_core.update_setting(f"{device} offset world yaw", -1.660)
        cl_offsets_world.findChildren(QDoubleSpinBox)[3].setValue(-1.660)

        settings_core.update_setting(f"{device} offset world pitch", 0.680)
        cl_offsets_world.findChildren(QDoubleSpinBox)[4].setValue(0.680)

        settings_core.update_setting(f"{device} offset world roll", 0.670)
        cl_offsets_world.findChildren(QDoubleSpinBox)[5].setValue(0.670)

#mapping v2/////////////////////////////////////////////////////////////////////

button_config = [    
    ("a", "a"),
    ("b", "b"),
    ("x", "x"),
    ("y", "y"),
    
    ("d-pad down", "dpdown"),
    ("d-pad left", "dpleft"),
    ("d-pad right", "dpright"),
    ("d-pad up", "dpup"),

    ("left trigger", "lefttrigger"),
    ("left bumper", "leftshoulder"),
    ("right trigger", "righttrigger"),
    ("right bumper", "rightshoulder"),

    ("left joy x", "leftx"),
    ("left joy y", "lefty"),
    ("left stick click", "leftstick"),

    ("right joy x", "rightx"),
    ("right joy y", "righty"),
    ("right stick click", "rightstick"),

    ("paddle 1", "paddle1"),
    ("paddle 2", "paddle2"),
    ("paddle 3", "paddle3"),
    ("paddle 4", "paddle4"),

    ("back", "back"),
    ("start", "start"),
    ("guide", "guide"),
]

combos = []

mapping = ["a", "b", "trigger", "grip", "menu", 
           "joy up", "joy down", "joy left", "joy right", "joy click", 
           "touch up", "touch down", "touch left", "touch right", "touch click", 
           "thumb", "index", "middle", "ring", "pinky", 
           "touch mod"]

current_binding_btn = None

class SingleBindButton(QPushButton):
    def __init__(self, mapping_name, current_bind, callback, parent=None):
        super().__init__("", parent)
        self.mapping_name = mapping_name
        self.current_bind = current_bind
        self.callback = callback
        self.is_binding = False
        
        self.refresh_display()
        self.clicked.connect(self.start_binding)

    def refresh_display(self):
        self.setText(f"{self.mapping_name}: {self.current_bind}")

    def start_binding(self):
        global current_binding_btn
        if current_binding_btn and current_binding_btn != self:
            current_binding_btn.cancel_binding()
            
        current_binding_btn = self
        self.is_binding = True
        self.setText("Press something (ESC to unbind)")
        self.setFocus() 

    def cancel_binding(self):
        self.is_binding = False
        self.refresh_display()

    def finish_binding(self, input_name):
        global current_binding_btn
        self.is_binding = False
        current_binding_btn = None
        self.current_bind = input_name
        self.refresh_display()
        
        self.callback()

    def keyPressEvent(self, event):
        if self.is_binding:
            if event.key() == Qt.Key.Key_Escape:
                self.finish_binding("[Unbound]")
            else:
                key_name = QKeySequence(event.key()).toString()
                self.finish_binding(f"Key_{key_name}")
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.is_binding:
            btn_map = {
                Qt.MouseButton.LeftButton: "Left",
                Qt.MouseButton.RightButton: "Right",
                Qt.MouseButton.MiddleButton: "Middle",
                Qt.MouseButton.XButton1: "M4",
                Qt.MouseButton.XButton2: "M5",
                Qt.MouseButton.BackButton: "Back",
                Qt.MouseButton.ForwardButton: "Forward",
                Qt.MouseButton.TaskButton: "Task"
            }
            
            button_id = event.button()
            button_name = btn_map.get(button_id, f"Extra_{button_id.value}")
            self.finish_binding(f"Mouse_{button_name}")
        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        if self.is_binding:
            delta = event.angleDelta().y()
            if delta > 0:
                self.finish_binding("Mouse_WheelUp")
            elif delta < 0:
                self.finish_binding("Mouse_WheelDown")
            event.accept()
        else:
            super().wheelEvent(event)

#bindable button!
#layout_controllers.addWidget(BindingButton("a", "b"))
#prefix = what device
#mapping_name = what action
#prefix_mapping_name in settings (cr_trigger)
class BindingGroupWidget(QWidget):
    def __init__(self, prefix, mapping_name, parent=None):
        super().__init__(parent)
        self.prefix = prefix
        self.mapping_name = mapping_name
        self.setting_key = f"{self.prefix}_{self.mapping_name}"
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QCheckBox("Invert")
        self.checkbox.stateChanged.connect(self.save_settings)
        
        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addWidget(self.checkbox)
        self.button_widgets = []
        
        self.load_settings()

    def load_settings(self):
        current_settings = settings_core.get_settings()
        bind_data = current_settings.get(self.setting_key, {})
        
        if not isinstance(bind_data, dict):
            bind_data = {}

        is_inverted = bind_data.get("invert", False)
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(is_inverted)
        self.checkbox.blockSignals(False)

        saved_buttons = bind_data.get("buttons", [])
        
        active_binds = [b for b in saved_buttons if b != "[Unbound]"]
        
        self.render_buttons(active_binds)

    def render_buttons(self, binds):
        while self.button_widgets:
            btn = self.button_widgets.pop()
            self.buttons_layout.removeWidget(btn)
            btn.setParent(None)
            btn.deleteLater()
        
        display_list = binds + ["[Unbound]"]
        
        for bind_value in display_list:
            btn = SingleBindButton(self.mapping_name, bind_value, self.on_button_changed)
            self.buttons_layout.addWidget(btn)
            self.button_widgets.append(btn)
            btn.show()

    def on_button_changed(self):
        QTimer.singleShot(10, self.save_settings)

    def save_settings(self):
        active_binds = []
        for btn in self.button_widgets:
            if btn.current_bind != "[Unbound]":
                active_binds.append(btn.current_bind)
        new_data = {
            "buttons": active_binds,
            "invert": self.checkbox.isChecked()
        }
        
        settings_core.update_nested(self.setting_key, new_data)
        
        self.render_buttons(active_binds)

def make_mapping_buttons(prefix):
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    label = QLabel(f"{prefix} mapping")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    for n in mapping:
        group_layout.addWidget(BindingGroupWidget(prefix, n))

    return group_widget

def make_mapping():
    group_widget = QWidget()
    main_layout = QHBoxLayout(group_widget)

    main_layout.addWidget(make_mapping_buttons("cl"))
    
    main_layout.addWidget(create_image({"path" : "index black", "size x" : 681, "size y" : 418}))
    
    main_layout.addWidget(make_mapping_buttons("cr"))

    return group_widget

layout_controllers.addWidget(make_mapping())

#real controllers settings/////////////////////////////////////////////////////////////////////////////
scroll_content_layout = None

def make_controller_block(ctrl):
    c_id   = ctrl.get("id", "unknown")
    c_name = ctrl.get("type", "Unknown Controller")
    
    settings = settings_core.get_settings()
    c_conf   = settings.get(c_id, {})

    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    group_layout.addWidget(create_label({"text": f"Name: {c_name}\nID: {c_id}"}))

    #todo: add images later!
    #group_layout.addWidget(create_image({"path": "fix.png", "size x": 100, "size y": 100}))

    group_layout.addWidget(create_label({"text": "Gyro Settings:"}))

    gyro_inverts = create_group_horizontal([
        {"type": "label",    "text": "Invert:", "alignment": Qt.AlignmentFlag.AlignCenter},
        {"type": "checkbox", "text": "X", "default": c_conf.get("invert_x", False),
         "func": lambda: settings_core.update_nested(c_id, {"invert_x": gyro_inverts.findChildren(QCheckBox)[0].isChecked()})},
        {"type": "checkbox", "text": "Y", "default": c_conf.get("invert_y", False),
         "func": lambda: settings_core.update_nested(c_id, {"invert_y": gyro_inverts.findChildren(QCheckBox)[1].isChecked()})},
        {"type": "checkbox", "text": "Z", "default": c_conf.get("invert_z", False),
         "func": lambda: settings_core.update_nested(c_id, {"invert_z": gyro_inverts.findChildren(QCheckBox)[2].isChecked()})}
    ])
    group_layout.addWidget(gyro_inverts)

    gyro_indices = create_group_horizontal([
        {"type": "label",   "text": "Direction:", "alignment": Qt.AlignmentFlag.AlignCenter},
        {"type": "spinbox", "text": "X", "min": 0, "max": 2, "default": c_conf.get("index_x", 0),
         "func": lambda: settings_core.update_nested(c_id, {"index_x": gyro_indices.findChildren(QSpinBox)[0].value()})},
        {"type": "spinbox", "text": "Y", "min": 0, "max": 2, "default": c_conf.get("index_y", 1),
         "func": lambda: settings_core.update_nested(c_id, {"index_y": gyro_indices.findChildren(QSpinBox)[1].value()})},
        {"type": "spinbox", "text": "Z", "min": 0, "max": 2, "default": c_conf.get("index_z", 2),
         "func": lambda: settings_core.update_nested(c_id, {"index_z": gyro_indices.findChildren(QSpinBox)[2].value()})}
    ])
    group_layout.addWidget(gyro_indices)

    gyro_sens = create_group_horizontal([
        {"type": "doublespinbox", "text": "Sensitivity:", "min": -99999, "max": 99999, "steps": 0.1,
         "default": c_conf.get("sensitivity", 1.0),
         "func": lambda: settings_core.update_nested(c_id, {"sensitivity": gyro_sens.findChild(QDoubleSpinBox).value()})}
    ])
    group_layout.addWidget(gyro_sens)

    group_layout.addWidget(create_button({
        "text": "Calibrate Gyro",
        "func": lambda: start_calibration(c_id)
    }))

    group_layout.addWidget(BindingGroupWidget(c_id, "reset_gyro"))
    #group_layout.addWidget(BindingButton(c_id, "reset_gyro"))

    return group_widget

def update_controller_ui():
    global scroll_content_layout
    if scroll_content_layout is None:
        return

    clear_layout(scroll_content_layout)

    with controllers_lock:
        ctrls = list(controllers_dict.values())

    for ctrl in ctrls:
        block = make_controller_block(ctrl)
        scroll_content_layout.addWidget(block)

signals.controller_connected.connect(update_controller_ui)

def make_base_scroll():
    global scroll_content_layout

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMinimumHeight(500)

    scroll_content        = QWidget()
    scroll_content_layout = QHBoxLayout(scroll_content)
    scroll_area.setWidget(scroll_content)

    layout_controllers.addWidget(scroll_area)
    update_controller_ui()

make_base_scroll()
#real controllers settings/////////////////////////////////////////////////////////////////////////////

#//////////////////////////////////////////////////////////
label5 = create_label({
    "text" : "---------camera(super experimental!!!)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(label5)

webcam = create_group_horizontal([
    {
        "type" : "checkbox", 
        "text" : "enable hand tracking",
        "default" : settings_core.get_settings()['hand tracking'],
        "func" : lambda: start_hand_tracking()
    },
    {
        "type" : "checkbox", 
        "text" : "curl",
        "default" : settings_core.get_settings().get("curl", True),
        "func" : lambda: settings_core.update_setting("curl",webcam1.findChildren(QCheckBox)[1].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "splay",
        "default" : settings_core.get_settings().get("splay", True),
        "func" : lambda: settings_core.update_setting("splay",webcam1.findChildren(QCheckBox)[2].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "index curl effects trigger",
        "default" : settings_core.get_settings().get("index=trigger", False),
        "func" : lambda: settings_core.update_setting("index=trigger",webcam1.findChildren(QCheckBox)[3].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "other curl effects grip",
        "default" : settings_core.get_settings().get("other=grip", False),
        "func" : lambda: settings_core.update_setting("other=grip",webcam1.findChildren(QCheckBox)[4].isChecked())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(webcam)

webcam1 = create_group_horizontal([
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset x", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset x", webcam.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset y", webcam.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset z", webcam.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "spinbox", 
        "text" :"camera index", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera index'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("camera index", webcam.findChildren(QSpinBox)[0].value())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(webcam1)

def start_hand_tracking():
    enabled = webcam.findChild(QCheckBox).isChecked()
    settings_core.update_setting("hand tracking", enabled)

    if enabled:
        start_camera()
    else:
        pass

#camera markers/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# webcam2 = create_group_horizontal([
#     {
#         "type" : "checkbox", 
#         "text" : "enable markers",
#         "default" : settings_core.get_settings()['markers'], 
#         "func" : lambda: start_stop_markers()
#     }#,
#     # {
#     #     "type" : "spinbox", 
#     #     "text" :"camera index", 
#     #     "min":0, 
#     #     "max":999999999, 
#     #     "default": settings_core.get_settings()['camera index'], 
#     #     "steps" : 1,
#     #     "func"  : lambda: settings_core.update_setting("camera index", webcam2.findChildren(QSpinBox)[0].value())
#     # },
# ])
# layout_controllers.addWidget(webcam2)

# def start_stop_markers():
#     enabled = webcam2.findChild(QCheckBox).isChecked()
#     settings_core.update_setting("markers", enabled)

#     if enabled:
#         start_markers()
#     else:
#         pass

# markers_active = False
# def start_markers():
#     global markers_active, marker_thread

#     if not markers_active:
#         if not markers_active:
#             markers_active = True
#             marker_thread = threading.Thread(target=markers_loop, daemon=True)
#             marker_thread.start()

# focal_length = 800
# center = (320, 240)
# marker_size = 0.10

# camera_matrix = np.array([
#     [focal_length, 0, center[0]],
#     [0, focal_length, center[1]],
#     [0, 0, 1]
# ], dtype="double")
# dist_coeffs = np.zeros((4,1))

# marker_3d_edges = np.array([
#     [-marker_size/2,  marker_size/2, 0],
#     [ marker_size/2,  marker_size/2, 0],
#     [ marker_size/2, -marker_size/2, 0],
#     [-marker_size/2, -marker_size/2, 0]
# ], dtype="double")

# # dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
# dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

# parameters = cv2.aruco.DetectorParameters()
# parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
# parameters.adaptiveThreshWinSizeMin = 3
# parameters.adaptiveThreshWinSizeMax = 23

# detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
# cap.set(cv2.CAP_PROP_EXPOSURE, -6)

# latest_markers = [] 
# data_lock = threading.Lock()

# def markers_loop():
#     global latest_markers, data_lock 
    
#     while True:
#         ret, frame = cap.read()
#         if not ret: break
        
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         corners, ids, _ = detector.detectMarkers(gray)
        
#         all_markers_data = [] 
        
#         if ids is not None:
#             for i in range(len(ids)):
#                 # 1. Calculate Pose
#                 success, rvec, tvec = cv2.solvePnP(
#                     marker_3d_edges, corners[i][0], camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_IPPE_SQUARE
#                 )
                
#                 if success:
#                     # 2. Prepare Data
#                     rot_matrix, _ = cv2.Rodrigues(rvec)
#                     quat = R.from_matrix(rot_matrix).as_quat() 
                    
#                     marker_dict = {
#                         "id": int(ids[i][0]),
#                         "pos x": round(float(tvec[0][0]), 3),
#                         "pos y": round(float(tvec[1][0]), 3),
#                         "pos z": round(float(tvec[2][0]), 3),
#                         "rot x": round(float(quat[0]), 3),
#                         "rot y": round(float(quat[1]), 3),
#                         "rot z": round(float(quat[2]), 3),
#                         "rot w": round(float(quat[3]), 3)
#                     }
#                     all_markers_data.append(marker_dict)

#                     top_left = tuple(corners[i][0][0].astype(int))
                    
#                     line_height = 18
#                     for j, (key, value) in enumerate(marker_dict.items()):
#                         text = f"{key}: {value}"
#                         y_pos = top_left[1] - 15 + (j * line_height)
                        
#                         cv2.putText(frame, text, (top_left[0] + 5, y_pos), 
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2)
#                         cv2.putText(frame, text, (top_left[0] + 5, y_pos), 
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

#                     cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, 0.05)

#         with data_lock:
#             latest_markers = all_markers_data

#         cv2.imshow('6DoF Multi-Marker Tracking', frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()

# def get_marker_transform(target_id=0):
#     global latest_markers, data_lock

#     fallback = {
#         "id": target_id,
#         "pos x": 0.0, "pos y": 0.0, "pos z": 0.0,
#         "rot x": 0.0, "rot y": 0.0, "rot z": 0.0, "rot w": 0.0
#     }

#     with data_lock:
#         for marker in latest_markers:
#             if marker["id"] == target_id:
#                 return marker
                
#     return fallback

# def get_marker_world_transform(device, marker_id):
#     try:
#         marker = get_marker_transform(marker_id)
#         if marker["pos z"] == 0:
#             raise ValueError("Marker not visible")

#         settings = settings_core.get_settings()

#         hmd_pos = np.array([
#             trackers_arr[0]['pos x'],
#             trackers_arr[0]['pos y'],
#             trackers_arr[0]['pos z']
#         ])
        
#         if 'rotation matrix' in trackers_arr[0]:
#             hmd_rot = R.from_matrix(trackers_arr[0]['rotation matrix'])
#         else:
#             hmd_rot = R.from_quat([
#                 trackers_arr[0]['rot x'], trackers_arr[0]['rot y'], 
#                 trackers_arr[0]['rot z'], trackers_arr[0]['rot w']
#             ])

#         camera_relative_pos = np.array([
#             marker["pos x"],
#             -marker["pos y"], 
#             -marker["pos z"]
#         ])

#         world_relative_pos = hmd_rot.apply(camera_relative_pos)
        
#         mod_x = settings.get('markers x', 1.0)
#         mod_y = settings.get('markers y', 1.0)
#         mod_z = settings.get('markers z', 1.0)

#         world_pos = hmd_pos + (world_relative_pos * np.array([mod_x, mod_y, mod_z]))

#         marker_rot_raw = R.from_quat([
#             marker['rot x'], marker['rot y'], 
#             marker['rot z'], marker['rot w']
#         ])

#         euler = marker_rot_raw.as_euler('xyz', degrees=False)
        
#         marker_rot_corrected = R.from_euler('xyz', [euler[0], -euler[1], -euler[2]], degrees=False)

#         off_y = settings.get(f'{device} offset world yaw', 0.0)
#         off_p = settings.get(f'{device} offset world pitch', 0.0)
#         off_r = settings.get(f'{device} offset world roll', 0.0)
#         offset_rotation = R.from_euler('ZYX', [off_y, off_p, off_r], degrees=False)
        
#         world_rot = hmd_rot * marker_rot_corrected * offset_rotation
#         final_quat = world_rot.as_quat()

#         return {
#             "pos x": world_pos[0], "pos y": world_pos[1], "pos z": world_pos[2],
#             "rot x": final_quat[0], "rot y": final_quat[1], "rot z": final_quat[2], "rot w": final_quat[3]
#         }

#     except Exception:
#         return {"pos x": 0.0, "pos y": 0.0, "pos z": 0.0, "rot x": 0.0, "rot y": 0.0, "rot z": 0.0, "rot w": 1.0}

# controller_states = {
#     1: {"active": False, "pos": np.zeros(3), "vel": np.zeros(3), "rot": R.identity(), 
#         "offset_quat": R.identity(), "last_time": 0.0, "lost_time": 0},
#     2: {"active": False, "pos": np.zeros(3), "vel": np.zeros(3), "rot": R.identity(), 
#         "offset_quat": R.identity(), "last_time": 0.0, "lost_time": 0},
# }

# def get_marker_gyro_transform(device, marker_id, controller_num):
#     global controller_states, trackers_arr, controller_1_dict, controller_2_dict
#     try:
#         current_time = time.time()
#         state = controller_states[controller_num]
#         settings = settings_core.get_settings()

#         c_dict = controller_1_dict if controller_num == 1 else controller_2_dict
#         if "gyro_quat" not in c_dict:
#             raise ValueError("No gyro data")

#         g_quat = c_dict["gyro_quat"]
#         norm = g_quat['x']**2 + g_quat['y']**2 + g_quat['z']**2 + g_quat['w']**2
#         gyro_rot = R.identity() if norm < 0.0001 else R.from_quat([g_quat['x'], g_quat['y'], g_quat['z'], g_quat['w']])

#         marker = get_marker_transform(marker_id)
#         tracking_active = marker["pos z"] != 0

#         if tracking_active:
#             optical = get_marker_world_transform(device, marker_id)
#             world_pos = np.array([optical["pos x"], optical["pos y"], optical["pos z"]])

#             if state["active"]:
#                 dt = current_time - state["last_time"]
#                 if dt > 0.005:
#                     new_vel = (world_pos - state["pos"]) / dt
#                     speed = np.linalg.norm(new_vel)
#                     if speed > 5.0:
#                         new_vel = (new_vel / speed) * 5.0
#                     state["vel"] = state["vel"] * 0.6 + new_vel * 0.4

#             if not state["active"] or state["lost_time"] != 0:
#                 optical_rot = R.from_quat([optical["rot x"], optical["rot y"], optical["rot z"], optical["rot w"]])
#                 state["offset_quat"] = optical_rot * gyro_rot.inv()

#             state["pos"] = world_pos
#             state["last_time"] = current_time
#             state["active"] = True
#             state["lost_time"] = 0

#             final_pos = world_pos
#             final_rot = state["offset_quat"] * gyro_rot

#         else:
#             if not state["active"]:
#                 raise ValueError("Tracking never initialized")

#             if state["lost_time"] == 0:
#                 state["lost_time"] = current_time

#             dt = current_time - state["last_time"]

#             final_rot = state["offset_quat"] * gyro_rot
#             final_pos = state["pos"] + state["vel"] * dt

#             state["pos"] = final_pos
#             state["last_time"] = current_time

#         final_quat = final_rot.as_quat()
#         return {
#             "pos x": final_pos[0], "pos y": final_pos[1], "pos z": final_pos[2],
#             "rot x": final_quat[0], "rot y": final_quat[1], "rot z": final_quat[2], "rot w": final_quat[3]
#         }

#     except Exception as e:
#         return {
#             "pos x": 0.0, "pos y": 0.0, "pos z": 0.0,
#             "rot x": 0.0, "rot y": 0.0, "rot z": 0.0, "rot w": 1.0
#         }

#camera markers/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

layout_controllers.addWidget(create_label({
    "text" : "---------Right offsets---------",
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cr_offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world x", cr_offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world y", cr_offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world z", cr_offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world yaw", cr_offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world pitch", cr_offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world roll", cr_offsets_world.findChildren(QDoubleSpinBox)[5].value())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(cr_offsets_world)

cr_offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local x", cr_offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local y", cr_offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local z", cr_offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local yaw", cr_offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local pitch", cr_offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local roll", cr_offsets_local.findChildren(QDoubleSpinBox)[5].value())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(cr_offsets_local)

layout_controllers.addWidget(create_label({
    "text" : "---------Left offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cl_offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world x", cl_offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world y", cl_offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world z", cl_offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },    
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world yaw", cl_offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world pitch", cl_offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world roll", cl_offsets_world.findChildren(QDoubleSpinBox)[5].value())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(cl_offsets_world)

cl_offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local x", cl_offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local y", cl_offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local z", cl_offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local yaw", cl_offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local pitch", cl_offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local roll", cl_offsets_local.findChildren(QDoubleSpinBox)[5].value())
    },
    {#spacing label!
        "type" : "label",
        "text":"",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    }
])
layout_controllers.addWidget(cl_offsets_local)
#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_trackers = QWidget()
layout_trackers = QVBoxLayout(tab_trackers)
layout_trackers.setSpacing(0)


def trackerpos_specific_widget(index, layout, combo):
    settings_core.update_setting(f'{index}trackerpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            tracker_redirect_group = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index",
                    "min":0,
                    "max":999999999, 
                    "default": settings.get(f'{index}trackerpos index', 0),
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting(f'{index}trackerpos index', tracker_redirect_group.findChildren(QSpinBox)[0].value())
                }
                ])
            layout.addWidget(tracker_redirect_group)

        case "hip emulation":

            t = create_group_spinbox([{
                "text" : "hmd index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker hmd index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker hmd index', t.findChildren(QSpinBox)[0].value())
            },{
                "text" : "left foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker left foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker left foot index', t.findChildren(QSpinBox)[1].value())
            },{
                "text" : "right foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker right foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker right foot index', t.findChildren(QSpinBox)[2].value())
            }])
            layout.addWidget(t)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def trackerrot_specific_widget(index, layout, combo):
    settings_core.update_setting(f'{index}trackerrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            tracker_redirect_group = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index",
                    "min":0,
                    "max":999999999, 
                    "default": settings.get(f'{index}trackerrot index', 0),
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting(f'{index}trackerrot index', tracker_redirect_group.findChildren(QSpinBox)[0].value())
                }
                ])
            layout.addWidget(tracker_redirect_group)

        case "hip emulation":

            t = create_group_spinbox([{
                "text" : "hmd index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker hmd index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker hmd index', t.findChildren(QSpinBox)[0].value())
            },{
                "text" : "left foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker left foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker left foot index', t.findChildren(QSpinBox)[1].value())
            },{
                "text" : "right foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker right foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker right foot index', t.findChildren(QSpinBox)[2].value())
            }])
            layout.addWidget(t)

        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings_core.get_settings().get(f'{index}tracker gyro id', ""),
                    "items": list(controllers_dict),
                    "func": lambda: settings_core.update_setting(f'{index}tracker gyro id', combo_extra.findChildren(QComboBox)[0].currentText())
                })
            
            layout.addWidget(combo_extra)

        case "offsets":
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_tracker_widget(index = 0):
    settings = settings_core.get_settings()

    widget_group = QWidget()
    layout_group = QVBoxLayout(widget_group)

    t = create_label({"text" : f"---index {index}---",
                    "alignment" : Qt.AlignmentFlag.AlignCenter
    })
    layout_group.addWidget(t)

    tab_extrapos = QWidget()
    layout_extrapos = QHBoxLayout(tab_extrapos)
    combopos_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} position mode',
            "default": settings.get(f'{index}trackerpos mode', "redirect"),
            "items": ["redirect", "offsets"],
            "func": lambda: trackerpos_specific_widget(index, layout_extrapos, combopos_extra.findChild(QComboBox))
        })
    layout_extrapos.addWidget(combopos_extra)
    trackerpos_specific_widget(index, layout_extrapos, combopos_extra.findChild(QComboBox))
    layout_group.addWidget(tab_extrapos)

    tab_extrarot = QWidget()
    layout_extrarot = QHBoxLayout(tab_extrarot)
    comborot_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} rotation mode',
            "default": settings.get(f'{index}trackerrot mode', "redirect"),
            "items": ["redirect", "offsets", "gyro"],
            "func": lambda: trackerrot_specific_widget(index, layout_extrarot, comborot_extra.findChild(QComboBox))
        })
    layout_extrarot.addWidget(comborot_extra)
    trackerrot_specific_widget(index, layout_extrarot, comborot_extra.findChild(QComboBox))
    layout_group.addWidget(tab_extrarot)

    tracker_offsets_world = create_group_horizontal([
        {
            "type" : "label",
            "text":"world",
            "alignment" : Qt.AlignmentFlag.AlignCenter
        },
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world x', 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world x', tracker_offsets_world.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world y', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world y', tracker_offsets_world.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world z', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world z', tracker_offsets_world.findChildren(QDoubleSpinBox)[2].value())
        },    
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world yaw', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world yaw', tracker_offsets_world.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world pitch', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world pitch', tracker_offsets_world.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world roll', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world roll', tracker_offsets_world.findChildren(QDoubleSpinBox)[5].value())
        }
    ])
    layout_group.addWidget(tracker_offsets_world)

    tracker_offsets_local = create_group_horizontal([
        {
            "type" : "label",
            "text":"local",
            "alignment" : Qt.AlignmentFlag.AlignCenter
        },
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local x', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local x', tracker_offsets_local.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local y', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local y', tracker_offsets_local.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local z', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local z', tracker_offsets_local.findChildren(QDoubleSpinBox)[2].value())
        },    
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local yaw', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local yaw', tracker_offsets_local.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local pitch', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local pitch', tracker_offsets_local.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local roll', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local roll', tracker_offsets_local.findChildren(QDoubleSpinBox)[5].value())
        }
    ])
    layout_group.addWidget(tracker_offsets_local)
    return widget_group

tab_devices = QWidget()
layout_devices = QVBoxLayout(tab_devices)

devices_arr = []

def create_trackers_display():
    settings_core.update_setting("trackers num", tracker_num.findChild(QSpinBox).value())
    settings = settings_core.get_settings()
    devices_arr.clear()
    clear_layout(layout_devices)

    if settings['trackers num'] > 0:
        for n in range(settings['trackers num']):
            devices_arr.append(create_tracker_widget(n))

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        for widget in devices_arr:
            container_layout.addWidget(widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        layout_devices.addWidget(scroll_area)

tracker_num = create_spinbox({
        "text" : "tracker number",
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['trackers num'], 
        "steps" : 1,
        "func"  : lambda: create_trackers_display()
    })
create_trackers_display()

layout_trackers.addWidget(tracker_num)
layout_trackers.addWidget(tab_devices)
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#////////////////////////////////////////////////////
group_widget = QWidget()
group_layout = QVBoxLayout(group_widget)

group_layout.addWidget(first_label)

tracker_title_label1 = create_label({
    "text" : "---------Trackers---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
group_layout.addWidget(tracker_title_label1)

#////////////////////////////////////////////////////
scroll_detected = QScrollArea()
scroll_detected.setWidgetResizable(True)

scroll_detected.setMinimumHeight(720)
# scroll_detected.setMaximumHeight(720)

scroll_detected.setMinimumWidth(250)
# scroll_detected.setMaximumWidth(250)

container = QWidget()
layout = QVBoxLayout(container)

trackers_label1 = create_label({
    "text" : "0 found", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout.addWidget(trackers_label1)

scroll_detected.setWidget(container)

group_layout.addWidget(scroll_detected)
#////////////////////////////////////////////////////

def start_reset_gyro():
    thread = threading.Thread(target=reset_gyro_on_input, daemon=True)
    thread.start()

def reset_gyro_on_input():
    while True:
        for n in list(controllers_dict):
            settings = settings_core.get_settings()
            config_key = f"{n}_reset_gyro"
            binding = settings.get(config_key)

            if binding and eval_binding(binding):
                if settings.get("hmd gyro id", "") == n:
                    reset_gyro(n, True)
                else:
                    reset_gyro(n)

        time.sleep(0.001)

if __name__ == '__main__':
    if settings_core.get_settings()['hand tracking']:
        start_camera()
    # if settings_core.get_settings()['markers']:
    #     start_markers()

    start_controller_mapping()

    start_send_data()
    start_update_vrlabel()

    # start_wiimote_threads()

    start_reset_gyro()

tabs.addTab(tab_main, "Hmd")
tabs.addTab(scroll_controllers, "Controllers")

tabs.addTab(tab_trackers, "Trackers")
tabs.addTab(tab_driver, "Driver")
tabs.addTab(tab_credits, "Credits")

window_layout.addWidget(tabs)
window_layout.addWidget(group_widget)
window.show()
app.exec()

#;P