#this need some cleanup ;P
#pyinstaller --noconfirm --windowed --name="GlassVR" --icon="assets/;Prism.ico" --collect-binaries "sdl3dll" --collect-all "sdl3" --collect-binaries "openvr" --collect-all "mediapipe" --collect-all "cv2" --hidden-import "sdl3dll" main.py
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea, QGroupBox,QFrame

from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QTimer, QEvent

from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QColor, QPalette, QMovie

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
import win32api

import win32file
from typing import List, Dict, Any, Tuple
import cv2
import mediapipe as mp
import cv2.aruco as aruco

import cvzone
from cvzone.HandTrackingModule import HandDetector

import time
import socket

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

import win32con
import win32gui
import win32ui
from flask import Flask, Response

#binaries = collect_dynamic_libs('sdl3dll')

app = QApplication([])#sys.argv)

window = QWidget()
window_layout = QVBoxLayout(window)

#tab///
tabs = QTabWidget()
tabs.setMovable(True)
# tabs.tabBarClicked.connect(lambda index: print(f"User clicked tab index: {index} ('{tabs.tabText(index)}')"))
# tabs.tabBar().tabMoved.connect(lambda from_idx, to_idx: print(f"Moved tab from index {from_idx} to {to_idx}"))
#tab///

tabs.tabBarClicked.connect(lambda index: change_label_on_click(tabs.tabText(index)))
def change_label_on_click(text):
    match text:
        case "Hmd":
            help_label.findChild(QLabel).setText('headset tab! (ignore the "Direct Display Mode" popup)')
        case "Controllers":
            help_label.findChild(QLabel).setText("controllers tab!")
        case "Trackers":
            help_label.findChild(QLabel).setText("trackers tab!")
        case "Driver":
            help_label.findChild(QLabel).setText("driver tab!")
        case "Credits":
            help_label.findChild(QLabel).setText("hello!!!!")
    

#window.setWindowTitle("PuffinVR")
window.setWindowTitle("GlassVR")

# window.resize(900, 900)
window.resize(1550, 900)

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
    
    if "style" in dict:
        button.setStyleSheet(dict.get('style', ""))
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
    
    combobox.addItems(dict.get('items',""))
    combobox.setCurrentText(dict.get('default',""))

    if 'index change' in dict:
        combobox.currentIndexChanged.connect(lambda: dict['index change']())

    if 'pre show' in dict:
        def wrapped_popup():
            dict['pre show'](combobox)
            QComboBox.showPopup(combobox)
        
        combobox.showPopup = wrapped_popup

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
    q = R.from_matrix(list(trackers_dict.values())[0]["rotation matrix"]).as_quat() #trackers_arr[0]["rotation matrix"]).as_quat()
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

#vr utility/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
trackers_arr = []

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
                
                current_frame_dict = {}
                current_frame_arr = []

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

                            current_frame_arr.append(device_data)

                        current_frame_dict[serial] = device_data

                trackers_dict = current_frame_dict
                trackers_arr = current_frame_arr

                vr_signals.devices_updated.emit(trackers_dict)
                
                time.sleep(0.001)

            except Exception as e:
                time.sleep(0.01)
                continue

    except Exception as e:
        time.sleep(1)
        start_vr_utility()

def end_vr_utility():
    vr.shutdown()

device_widgets = {}

def update_found_label(data_dict):
    global device_widgets

    for count, (serial, data) in enumerate(data_dict.items()):
        if serial in device_widgets:
            w = device_widgets[serial]
            conn = data.get('connected')
            valid = data.get('pose_valid')

            if not conn:
                w['status'].setText("DISCONNECTED")
                w['status'].setStyleSheet("color: red; font-weight: bold;")
            elif not valid:
                w['status'].setText("SEARCHING...")
                w['status'].setStyleSheet("color: yellow; font-weight: bold;")
            else:
                w['status'].setText("TRACKING")
                w['status'].setStyleSheet("color: green; font-weight: bold;")

            if "pos x" in data:
                px, py, pz = data['pos x'], data['pos y'], data['pos z']
                w['pos'].setText(f"(X:{px:+.4f}  Y:{py:+.4f}  Z:{pz:+.4f})")

            if "rotation matrix" in data:
                m = data['rotation matrix']
                yaw, pitch, roll = R.from_matrix(m).as_euler('yxz', degrees=True)
                w['rot'].setText(f"(Yaw:{yaw:+.1f}°  Pitch:{pitch:+.1f}°  Roll:{roll:+.1f}°)")
            continue

        # Color per device
        hue = (count * 36) % 360
        bg = QColor.fromHsv(hue, 40, 50)
        border = QColor.fromHsv(hue, 120, 180)

        group = QGroupBox(f"[{count}]  {data['role']}  |  {data['model']}")
        group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {bg.name()};
                border: 1px solid {border.name()};
                border-radius: 8px;
                margin-top: 1.5ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: {border.name()};
            }}
        """)

        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(0)
        group_layout.setContentsMargins(8, 8, 8, 8)

        conn = data.get('connected')
        valid = data.get('pose_valid')
        if not conn:
            status_text, status_color = "DISCONNECTED", "red"
        elif not valid:
            status_text, status_color = "SEARCHING...", "yellow"
        else:
            status_text, status_color = "TRACKING", "green"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        group_layout.addWidget(status_label)

        pos_label = QLabel("(X: —  Y: —  Z: —)")
        rot_label = QLabel("(Yaw: —  Pitch: —  Roll: —)")

        if "pos x" in data:
            px, py, pz = data['pos x'], data['pos y'], data['pos z']
            pos_label.setText(f"(X:{px:+.4f}  Y:{py:+.4f}  Z:{pz:+.4f})")

        if "rotation matrix" in data:
            yaw, pitch, roll = R.from_matrix(data['rotation matrix']).as_euler('yxz', degrees=True)
            rot_label.setText(f"(Yaw:{yaw:+.1f}°  Pitch:{pitch:+.1f}°  Roll:{roll:+.1f}°)")

        serial_btn = QPushButton(f"Serial: {serial}")
        serial_btn.setToolTip("Click to copy serial to clipboard")
        serial_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {border.name()};
                border-radius: 4px;
                padding: 2px 6px;
                margin-top: 4px;
                color: {border.name()};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {border.name()};
                color: white;
            }}
        """)

        def on_copy(_, s=serial, btn=serial_btn):
            QApplication.clipboard().setText(s)
            btn.setText("Copied to clipboard!")
            QTimer.singleShot(500, lambda: btn.setText(f"Serial: {s}"))

        serial_btn.clicked.connect(on_copy)

        group_layout.addWidget(status_label)

        pos_header = QLabel("Position:")
        pos_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        group_layout.addWidget(pos_header)
        group_layout.addWidget(pos_label)

        rot_header = QLabel("Rotation:")
        rot_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        group_layout.addWidget(rot_header)
        group_layout.addWidget(rot_label)

        group_layout.addWidget(serial_btn)
        detected_layout.addWidget(group)

        device_widgets[serial] = {
            'group': group,
            'status': status_label,
            'pos': pos_label,
            'rot': rot_label,
        }

class VRSignals(QObject):
    devices_updated = pyqtSignal(dict)

vr_signals = VRSignals()
vr_signals.devices_updated.connect(update_found_label)

#vr utility/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#style/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def set_style(widget, style = "{ background: #242424; border: 1px solid #444; border-radius: 6px; }", name = "default"):
    final_style = f"QWidget#{name} {style}"
    widget.setStyleSheet(final_style)
    widget.setObjectName(name)

class HoverGroupBox(QGroupBox):
    def __init__(self, name, text):
        super().__init__(name)
        self.hover_text = text

    def enterEvent(self, event):
        if self.hover_text != "":
            help_label.findChild(QLabel).setText(self.hover_text)
        super().enterEvent(event)

group_count = 0
def set_group(name = "Group", arr = [], box = "v", style = """
        QGroupBox {
            background-color: #242424;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 1ex; /* Leaves space for the title */
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center; /* Positions the title */
            padding: 0 5px;
            left: 10px;
            color: #2470ED;
        }
    """, text = ""):

    global group_count
    group_count += 1

    #rainbow style///
    # hue = (group_count * 36) % 360
    # bg = QColor.fromHsv(hue, 40 + group_count, 50)
    # border = QColor.fromHsv(hue, 40 + group_count, 128)

    # group_style = f"""
    #     QGroupBox {{
    #         background-color: {bg.name()};
    #         border: 1px solid {border.name()};
    #         border-radius: 8px;
    #         margin-top: 1.5ex;
    #         font-weight: bold;
    #     }}

    #     QGroupBox::title {{
    #         subcontrol-origin: margin;
    #         subcontrol-position: top center;
    #         padding: 0 10px;
    #         color: {border.name()};
    #     }}
    # """
    #rainbow style///

    if style == """
        QGroupBox {
            background-color: #242424;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 1ex; /* Leaves space for the title */
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center; /* Positions the title */
            padding: 0 5px;
            left: 10px;
            color: #2470ED;
        }
    """:
        if group_count %2 == 0:
            style = """
            QGroupBox {
                background-color: #242424;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 1ex; /* Leaves space for the title */
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Positions the title */
                padding: 0 5px;
                left: 10px;
                color: #2470ED;
            }
        """
        else:
            style = """
            QGroupBox {
                background-color: #292929;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 1ex; /* Leaves space for the title */
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Positions the title */
                padding: 0 5px;
                left: 10px;
                color: #2470ED;
            }
        """
    else:
        pass

    group_widget = HoverGroupBox(name, text)
    if box == "v":
        misc_layout = QVBoxLayout()
    else:
        misc_layout = QHBoxLayout()
    group_widget.setLayout(misc_layout)

    for n in arr:
        misc_layout.addWidget(n)

    group_widget.setStyleSheet(style)

    return group_widget

offsets_style = """
        QGroupBox {
            background-color: #1F1F1F;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 1ex; /* Leaves space for the title */
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center; /* Positions the title */
            padding: 0 5px;
            left: 10px;
            color: #2470ED;
        }
    """

#UDP relay/////////////////////////////////////////////////////////////////////////////////////////////////////
packets = {} 
packets_lock = threading.Lock()

def get_latest_packet(device, prefix):
    raw_data = get_data(device, prefix)
    
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
                    return {
                        "reset": reset_flag
                    }

            case _:
                return None
                
    except struct.error as e:
        pass
    
    return None

def pipe_listener_worker(device):
    while True:
        settings = settings_core.get_settings()
        port = settings.get(f"{device} port")
        
        if not port:
            time.sleep(1.0)
            continue

        pipe_name = f"\\\\.\\pipe\\UDP_RELAY_{port}"

        with packets_lock:
            if port not in packets:
                packets[port] = {}

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
                    resp, data = win32file.ReadFile(handle, 1024)
                    if data:
                        prefix = data[0:1].decode('ascii', errors='ignore')
                        payload = data[1:]
                        with packets_lock:
                            packets[port][prefix] = payload
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

def start_udp_thread():
    settings = settings_core.get_settings()
    enable_device("hmd")
    enable_device("cr")
    enable_device("cl")
    
    for n in range(settings['trackers num']):
        enable_device(f"{n}tracker")

def get_data(device, prefix):
    settings = settings_core.get_settings()
    port = settings.get(f"{device} port")
    
    if not port:
        return None
        
    with packets_lock:
        return packets.get(port, {}).get(prefix)
#UDP relay/////////////////////////////////////////////////////////////////////////////////////////////////////

#bindable button/////////////////////////////////////////////////////////////////////////////
#example for thread with one bindable button:////////////////////////////////////////////////////////////////////////////
# layout_controllers.addWidget(set_group("PlaySpace",[BindingGroupWidget("cr", "reset playspace")]))
# def start_reset_playspace():
#     thread = threading.Thread(target=reset_playspace_on_input, daemon=True)
#     thread.start()
# def reset_playspace_on_input():
#     while True:
#         settings = settings_core.get_settings()
#         if eval_binding(settings.get(f"cr_reset playspace", "")):
#             pass
#         time.sleep(0.001)

#bindable button!
#layout_controllers.addWidget(BindingButton("a", "b"))
#prefix = what device
#mapping_name = what action
#prefix_mapping_name in settings (cr_trigger)
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

class BindingGroupWidget(QWidget):
    def __init__(self, prefix, mapping_name, parent=None):
        super().__init__(parent)
        self.prefix = prefix
        self.mapping_name = mapping_name
        self.setting_key = f"{self.prefix}_{self.mapping_name}"
        
        self.main_layout = QHBoxLayout(self)
        
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
#bindable button/////////////////////////////////////////////////////////////////////////////

#main/////////////////////////////////////////////////////////////////////////////////////////////////////////////

tab_main = QWidget()
layout_main = QVBoxLayout(tab_main)
set_style(tab_main, "{ background: #1F1F1F; border: 0px solid #444; border-radius: 0px; }", "t")

scroll_hmd = QScrollArea()
scroll_hmd.setWidgetResizable(True)
scroll_hmd.setWidget(tab_main)

# scroll_hmd.setMinimumWidth(1800)
# scroll_hmd.setMinimumHeight(800)

check_box_hmd = create_checkbox(
    {
        "text" : "enable hmd", 
        "default" : settings_core.get_settings()['enable hmd'], 
        "func" : lambda: enable_device("hmd")
    })
layout_main.addWidget(set_group("Enable", [check_box_hmd], text = 'enables headset emulation (ignore the "Direct Display Mode" popup)'))

active_threads = set()  
active_threads_lock = threading.Lock() 

def enable_device(device=""):
    ui_mapping = {
        "hmd": check_box_hmd,
        "cr": check_cr,
        "cl": check_cl
    }

    should_start_thread = False

    if device in ui_mapping:
        is_checked = ui_mapping[device].findChild(QCheckBox).isChecked()
        settings_core.update_setting(f"enable {device}", is_checked)
        
        if not is_checked:
            with active_threads_lock:
                if device in active_threads:
                    active_threads.remove(device)
            return

        settings = settings_core.get_settings()
        if settings.get(f"enable {device}"):
            should_start_thread = True
            
    elif "tracker" in device:
        should_start_thread = True

    if should_start_thread:
        with active_threads_lock:
            if device in active_threads:
                return
            
            active_threads.add(device)
            
        t = threading.Thread(target=pipe_listener_worker, args=(device,), daemon=True)
        t.start()

#hmd modes v2///////////////////////////////////////////////////////////////////////////
hmd_shared_layout = None

def update_hmd_shared():
    settings = settings_core.get_settings()

    p_mode = settings.get('hmdpos mode', 'copy')
    r_mode = settings.get('hmdrot mode', 'copy')

    clear_layout(hmd_shared_layout)

    if p_mode == "UDP" or r_mode == "UDP":
        t = create_group_horizontal([{
                "type"   : "spinbox",
                "text"   : "port",
                "min"    : 0,
                "max"    : 999999999,
                "default": settings.get('hmd port', 9000),
                "steps"  : 1,
                "func"   : lambda: settings_core.update_setting("hmd port", t.findChildren(QSpinBox)[0].value())
            }])
        hmd_shared_layout.addWidget(t)

    if p_mode == "named pipe" or r_mode == "named pipe":
        t = create_label({"text" : "external named pipe require the ui to be closed"})
        hmd_shared_layout.addWidget(t)

    if p_mode == "xr glasses 6dof" or r_mode == "xr glasses 6dof" or r_mode == "xr glasses":
        t = BindingGroupWidget("hmd", "reset xr")
        hmd_shared_layout.addWidget(t)

        y = create_group_horizontal([
            {
        "type" : "label",
        "text" : "only viture xr glasses are supported for now",
        "alignment" : Qt.AlignmentFlag.AlignCenter,
        },
        {
        "type" : "button",
        "enabled" : True,
        "text" :"calibrate on viture site",
        "func"  : lambda: webbrowser.open("https://www.viture.com/firmware/calibration")
        }])
        hmd_shared_layout.addWidget(y)

    # if p_mode == "X" or r_mode == "X":
    #     hmd_shared_layout.addWidget(???)

def hmdpos_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    update_hmd_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("hmdpos copy serial",""),
                    "items": list(set([settings.get("hmdpos copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("hmdpos copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("hmdpos copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        # case "xr glasses 6dof":
        #     t = create_group_horizontal([{
        #             "type" : "label",
        #             "text" : "viture luma ultra 6dof",
        #             "alignment" : Qt.AlignmentFlag.AlignCenter,
        #         },{
        #             "type" : "button",
        #             "enabled" : True,
        #             "text" :"calibrate on viture site",
        #             "func"  : lambda: webbrowser.open("https://www.viture.com/firmware/calibration")
        #         }])
        #     layout.addWidget(t)

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

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def hmdrot_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    update_hmd_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("hmdrot copy serial",""),
                    "items": list(set([settings.get("hmdrot copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("hmdrot copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("hmdrot copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

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
                    "default": settings.get("hmd gyro id", ""),
                    "items": list({str(settings.get("hmd gyro id", "")), *controllers_dict}) if settings.get("hmd gyro id") else list(controllers_dict),
                    "index change": lambda: settings_core.update_setting("hmd gyro id", combo_extra.findChild(QComboBox).currentText()),
                    "pre show": lambda cb: (
                        saved := str(settings.get("hmd gyro id", "")),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *controllers_dict}) if saved else list(controllers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("hmdrot copy serial",""),
                    "items": list(set([settings.get("hmdrot copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("hmdrot copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("hmdrot copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        # case "xr glasses":
        #     t = create_group_horizontal([{
        #             "type" : "label",
        #             "text" : "only viture glasses are supported for now",
        #             "alignment" : Qt.AlignmentFlag.AlignCenter,
        #         },{
        #             "type" : "button",
        #             "enabled" : True,
        #             "text" :"calibrate on viture site",
        #             "func"  : lambda: webbrowser.open("https://www.viture.com/firmware/calibration")
        #         }])
        #     layout.addWidget(t)

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_hmd_pos():
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    settings = settings_core.get_settings()

    combo = create_combobox({
            "type" : "combobox",
            "text": "hmd position mode",
            "default": settings.get(f'hmdpos mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "xr glasses 6dof"],# "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: hmdpos_specific_widget(group_layout, combo.findChild(QComboBox))
        })
    
    group_layout.addWidget(combo)
    hmdpos_specific_widget(group_layout, combo.findChild(QComboBox))

    return group_widget

def create_hmd_rot():
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    settings = settings_core.get_settings()
    
    combo = create_combobox({
            "type" : "combobox",
            "text": "hmd rotation mode",
            "default": settings.get(f'hmdrot mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "xr glasses 6dof", "xr glasses", "gyro"],# "mouse"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: hmdrot_specific_widget(group_layout, combo.findChild(QComboBox))
        })
    
    group_layout.addWidget(combo)
    hmdrot_specific_widget(group_layout, combo.findChild(QComboBox))

    return group_widget

def create_hmd_shared():
    global hmd_shared_layout

    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    hmd_shared_layout = group_layout
    
    group_layout.addWidget(create_label({"text" : "shared"}))

    return group_widget

def create_hmd_widget():
    root_widget = QWidget()
    root_layout = QHBoxLayout(root_widget)

    modes_widget = QWidget()
    modes_layout = QVBoxLayout(modes_widget)

    settings = settings_core.get_settings()

    s = create_hmd_shared()

    modes_layout.addWidget(create_hmd_pos())
    modes_layout.addWidget(create_hmd_rot())

    root_layout.addWidget(modes_widget)
    root_layout.addWidget(s)

    #style///
    modes_widget.setStyleSheet("QWidget#hmd_modes { background: #1F1F1F; border: 1px solid #444; border-radius: 6px; }")
    modes_widget.setObjectName("hmd_modes")
    #style///

    return root_widget

layout_main.addWidget(set_group("Modes", [create_hmd_widget()], text = "headset position and rotation modes"))
#hmd modes v2 ///////////////////////////////////////////////////////////////////////////

def is_prosses_running(PROCESS_NAME):
    for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == PROCESS_NAME.lower():
                return True
    
    return False

def check_hardware_key_exists(hardware_name):
    settings = settings_core.get_settings()
    
    return hardware_name in settings.values()

def get_new_transform(device="hmd", 
                      px=0.0, py=0.0, pz=0.0, 
                      rx=0.0, ry=0.0, rz=0.0, rw=0.0):
    #get the final position of the emulated device with offsets applied,
    #device: from what settings to take offsets
    #other arguments: are what the current pos and rot of the emulated device, example: to copy x from tracker, pass trackers_arr[tracker_pos_idx]['pos x'] to px

    #//////////////////////////////////////////////////
    # copy = trackers_dict["hmdpos copy serial"]
    # matrix = copy["rotation matrix"]
    # r = R.from_matrix(matrix)
    # quat = r.as_quat()
    # final_transform = get_new_transform("hmd", copy['pos x'], copy['pos y'], copy['pos z'], rx=quat[0], ry=quat[1], rz=quat[2], rw=quat[3])

    # pos_x = final_transform['pos x']
    # pos_y = final_transform['pos y']
    # pos_z = final_transform['pos z']
    # rot_x = final_transform['rot x']
    # rot_y = final_transform['rot y']
    # rot_z = final_transform['rot z']
    # rot_w = final_transform['rot w']
    #//////////////////////////////////////////////////

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
    
def offset_transform(
    px=0.0, py=0.0, pz=0.0, 
    rx=0.0, ry=0.0, rz=0.0, rw=0.0,
    lpx=0.0, lpy=0.0, lpz=0.0, lry=0.0, lrp=0.0, lrr=0.0,
    wpx=0.0, wpy=0.0, wpz=0.0, wry=0.0, wrp=0.0, wrr=0.0):
    try:
        device_rotation = R.from_quat([rx, ry, rz, rw])
        
        offset_local_vec = np.array([lpx, lpy, lpz])
        rotated_local_offset = device_rotation.apply(offset_local_vec)
        
        pos_x = px + rotated_local_offset[0] + wpx
        pos_y = py + rotated_local_offset[1] + wpy
        pos_z = pz + rotated_local_offset[2] + wpz
        
        offset_local_rotation = R.from_euler('ZYX', [lrr, lry, lrp], degrees=False)
        offset_world_rotation = R.from_euler('ZYX', [wrr, wry, wrp], degrees=False)
        
        final_rotation = offset_world_rotation * device_rotation * offset_local_rotation
        quat_final = final_rotation.as_quat()
        
        return {
            "pos x": pos_x, "pos y": pos_y, "pos z": pos_z,
            "rot x": quat_final[0], "rot y": quat_final[1], 
            "rot z": quat_final[2], "rot w": quat_final[3]
        }

    except Exception:
        return {
            "pos x": px, "pos y": py, "pos z": pz,
            "rot x": rx, "rot y": ry, "rot z": rz, "rot w": rw
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

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')

PIPE_HMD_POS = r'\\.\pipe\GlassVR_HMD_Pos'
PIPE_HMD_ROT = r'\\.\pipe\GlassVR_HMD_Rot'

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )

def send_hmd_data():
    while True:
        h_pos = None
        h_rot = None
        try:
            h_pos = create_pipe(PIPE_HMD_POS)
            h_rot = create_pipe(PIPE_HMD_ROT)
            
            win32pipe.ConnectNamedPipe(h_pos, None)
            win32pipe.ConnectNamedPipe(h_rot, None)
            
            while True:
                settings = settings_core.get_settings()
                
                pos_x = pos_y = pos_z = 0.0
                rot_x = rot_y = rot_z = 0.0
                rot_w = 1.0

                #pos///
                try:
                    if settings['hmdpos mode'] not in ["copy", "offsets", "keyboard"]:
                        final_transform = get_new_transform("hmd")
                        pos_x = final_transform['pos x']
                        pos_y = final_transform['pos y']
                        pos_z = final_transform['pos z']
                except: pass

                #rot///
                try:
                    if settings['hmdrot mode'] == "gyro":
                        quat = get_gyro(settings["hmd gyro id"])
                        rot_x, rot_y, rot_z, rot_w = quat["x"], quat["y"], quat["z"], quat["w"]
                    elif settings['hmdrot mode'] not in ["copy", "offsets", "mouse"]:
                        final_transform = get_new_transform("hmd")
                        rot_x = final_transform['rot x']
                        rot_y = final_transform['rot y']
                        rot_z = final_transform['rot z']
                        rot_w = final_transform['rot w']
                except: pass

                buffer_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)
                buffer_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)
                
                try:
                    win32file.WriteFile(h_pos, buffer_pos)
                    win32file.WriteFile(h_rot, buffer_rot)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            pass

        finally:
            for h in [h_pos, h_rot]:
                if h:
                    try:
                        win32pipe.DisconnectNamedPipe(h)
                        win32file.CloseHandle(h)
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
            list(trackers_dict.values())[0]['pos x'],
            list(trackers_dict.values())[0]['pos y'],
            list(trackers_dict.values())[0]['pos z']
        ])
        hmd_rot = R.from_matrix(list(trackers_dict.values())[0]['rotation matrix'])

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

        #hardcoded offsets
        if hand_prefix == "r":
            offset_yaw   = 1.660 + settings.get(f'{device} offset world yaw',   0.0)
            offset_pitch = -0.680 + settings.get(f'{device} offset world pitch', 0.0)
            offset_roll  = 0.670 + settings.get(f'{device} offset world roll',  0.0)
        else:
            offset_yaw   = -1.660 + settings.get(f'{device} offset world yaw',   0.0)
            offset_pitch = 0.680 + settings.get(f'{device} offset world pitch', 0.0)
            offset_roll  = 0.670 + settings.get(f'{device} offset world roll',  0.0)

        # offset_yaw   = settings.get(f'{device} offset world yaw',   0.0)
        # offset_pitch = settings.get(f'{device} offset world pitch', 0.0)
        # offset_roll  = settings.get(f'{device} offset world roll',  0.0)

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

INPUT_PACKER = struct.Struct("<12?8d")
SKELETAL_PACKER = struct.Struct("<25d")

PIPE_BASE = "\\\\.\\pipe\\GlassVR_CONTROLLER_{side}_{type}"

def send_controller_data(is_right):
    device_name = "cr" if is_right else "cl"
    prefix      = device_name
    side        = "RIGHT" if is_right else "LEFT"

    pipe_pos_name      = PIPE_BASE.format(side=side, type="Pos")
    pipe_rot_name      = PIPE_BASE.format(side=side, type="Rot")
    pipe_input_name    = PIPE_BASE.format(side=side, type="Input")
    pipe_skeletal_name = PIPE_BASE.format(side=side, type="Skeletal")

    while True:
        handles = {}
        try:
            handles['pos']      = create_pipe(pipe_pos_name)
            handles['rot']      = create_pipe(pipe_rot_name)
            handles['input']    = create_pipe(pipe_input_name)
            handles['skeletal'] = create_pipe(pipe_skeletal_name)

            for h in handles.values():
                win32pipe.ConnectNamedPipe(h, None)

            while True:
                settings = settings_core.get_settings()

                #pos///
                pos_x = pos_y = pos_z = 0.0
                try:
                    match settings.get(f'{device_name}pos mode', ''):
                        case "copy" | "offsets":
                            pass

                        case "hand tracking":
                            if settings_core.get_settings().get('hand tracking', False):
                                t = get_hand_world_transform(device_name)
                            else:
                                t = get_new_transform(device_name)
                            pos_x, pos_y, pos_z = t['pos x'], t['pos y'], t['pos z']

                        case _:
                            t = get_new_transform(device_name)
                            pos_x, pos_y, pos_z = t['pos x'], t['pos y'], t['pos z']
                except Exception:
                    pass
                
                #rot///
                rot_w, rot_x, rot_y, rot_z = 1.0, 0.0, 0.0, 0.0
                try:
                    match settings.get(f'{device_name}rot mode', ''):
                        case "copy" | "offsets":
                            pass

                        case "hand tracking":
                            if settings_core.get_settings().get('hand tracking', False):
                                t = get_hand_world_transform(device_name)
                            else:
                                t = get_new_transform(device_name)
                            rot_x, rot_y, rot_z, rot_w = t['rot x'], t['rot y'], t['rot z'], t['rot w']

                        case "gyro":
                            q = get_gyro(settings[f'{device_name} gyro id'])
                            rot_x, rot_y, rot_z, rot_w = q['x'], q['y'], q['z'], q['w']

                        case _:
                            t = get_new_transform(device_name)
                            rot_x, rot_y, rot_z, rot_w = t['rot x'], t['rot y'], t['rot z'], t['rot w']
                except Exception:
                    pass

                #input(index)
                trigger     = eval_binding(settings.get(f"{prefix}_trigger", ""))
                a           = eval_binding(settings.get(f"{prefix}_a", "")) > 0.5
                b           = eval_binding(settings.get(f"{prefix}_b", "")) > 0.5
                system      = eval_binding(settings.get(f"{prefix}_menu", "")) > 0.5
                touch_mod   = eval_binding(settings.get(f"{prefix}_touch mod", "")) > 0.5

                joy_x   = eval_binding(settings.get(f"{prefix}_joy right", "")) - eval_binding(settings.get(f"{prefix}_joy left",  ""))
                joy_y   = eval_binding(settings.get(f"{prefix}_joy up", "")) - eval_binding(settings.get(f"{prefix}_joy down",  ""))
                joy_btn = eval_binding(settings.get(f"{prefix}_joy click", "")) > 0.5

                touch_x   = eval_binding(settings.get(f"{prefix}_touch right", "")) - eval_binding(settings.get(f"{prefix}_touch left",  ""))
                touch_y   = eval_binding(settings.get(f"{prefix}_touch up", "")) - eval_binding(settings.get(f"{prefix}_touch down",  ""))

                touch_force = eval_binding(settings.get(f"{prefix}_touch click",  ""))
                
                raw_input = eval_binding(settings.get(f"{prefix}_grip", ""))
                grip_pull = min(1.0, raw_input * 2.0)
                grip_force = max(0.0, (raw_input - 0.5) / 0.5)
                
                if touch_mod:
                    touch_x = joy_x
                    touch_y = joy_y
                    
                    touch_force = max(eval_binding(settings.get(f"{prefix}_touch click",  "")), joy_btn)

                    joy_x = joy_y = 0.0
                    joy_btn = False

                trigger_btn = trigger > 0.99

                #capacitive buttons
                a_cap = a
                b_cap = b
                system_cap = system

                trigger_cap = trigger > 0.01
                grip_cap = grip_pull > 0.01

                joy_cap = joy_btn or abs(joy_x) > 0.1 or abs(joy_y) > 0.1

                touch_cap = (touch_force > 0.01) or abs(touch_x) > 0.1 or abs(touch_y) > 0.1

                #skeletal
                fingers = ["thumb", "index", "middle", "ring", "pinky"]

                if settings.get("curl", True):
                    flexion = list(hand_data["l flexion"] if prefix == "cl" else hand_data["r flexion"])
                    for i, finger in enumerate(fingers):
                        val = eval_binding(settings.get(f"{prefix}_{finger}", ""))
                        if val > 0.01:
                            flexion[i * 4] = val

                    if settings.get("index=trigger", False):
                        if trigger < flexion[4]:
                            trigger = -1 + (flexion[4] * 3)

                    if settings.get("other=grip", False):
                        highest = max(flexion[8], flexion[12], flexion[16])
                        if grip_pull < highest - 0.7:
                            grip_pull = highest - 0.7
                else:
                    flexion = [0.0] * 20
                    for i, finger in enumerate(fingers):
                        val = eval_binding(settings.get(f"{prefix}_{finger}", ""))
                        if val > 0.01:
                            flexion[i * 4] = val

                if settings.get("splay", True):
                    splays_5 = list(hand_data["l splay"] if prefix == "cl" else hand_data["r splay"])
                else:
                    splays_5 = [0.0] * 5

                #buffer
                buf_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)

                buf_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)

                buf_input = INPUT_PACKER.pack(
                    bool(a), bool(b), bool(system),
                    bool(joy_btn), bool(trigger_btn),
                    bool(a_cap), bool(b_cap), bool(system_cap),
                    bool(joy_cap), bool(trigger_cap),
                    bool(touch_cap), bool(grip_cap),
                    float(joy_x), float(joy_y),
                    float(touch_x), float(touch_y),
                    float(trigger),
                    float(touch_force),
                    float(grip_pull),
                    float(grip_force),
                )

                buf_skeletal = SKELETAL_PACKER.pack(
                    *[float(f) for f in flexion],
                    *[float(s) for s in splays_5],
                )

                try:
                    win32file.WriteFile(handles['pos'], buf_pos)
                    win32file.WriteFile(handles['rot'], buf_rot)
                    win32file.WriteFile(handles['input'], buf_input)
                    win32file.WriteFile(handles['skeletal'], buf_skeletal)
                except pywintypes.error as e:
                    if e.winerror in (109, 232):
                        break
                    raise

                time.sleep(0.001)

        except Exception:
            pass
        finally:
            for h in handles.values():
                try:
                    win32pipe.DisconnectNamedPipe(h)
                    win32file.CloseHandle(h)
                except Exception:
                    pass
            time.sleep(1)

def send_tracker_data(tracker_id):
    pipe_pos_name = f"\\\\.\\pipe\\GlassVR_TRACKER_{tracker_id}_Pos"
    pipe_rot_name = f"\\\\.\\pipe\\GlassVR_TRACKER_{tracker_id}_Rot"
    
    while True:
        h_pos = None
        h_rot = None
        try:
            h_pos = create_pipe(pipe_pos_name)
            h_rot = create_pipe(pipe_rot_name)
            
            win32pipe.ConnectNamedPipe(h_pos, None)
            win32pipe.ConnectNamedPipe(h_rot, None)
            
            while True:
                settings = settings_core.get_settings()
                device_key = f'{tracker_id}tracker'

                final_transform = get_new_transform(device_key)
                pos_x, pos_y, pos_z = final_transform['pos x'], final_transform['pos y'], final_transform['pos z']
                rot_x, rot_y, rot_z, rot_w = final_transform['rot x'], final_transform['rot y'], final_transform['rot z'], final_transform['rot w']

                #pos///
                try:
                    pos_mode = settings.get(f"{device_key}pos mode", "copy")
                    if pos_mode == "bad apple":
                        data = BAD_APPLE_STATE.get(device_key, {"pos x": 0, "pos y": 0, "pos z": 0})
                        pos_x, pos_y, pos_z = data["pos x"], data["pos y"], data["pos z"]
                except: pass

                #rot///
                try:
                    rot_mode = settings.get(f"{device_key}rot mode", "copy")
                    if rot_mode == "gyro":
                        quat = get_gyro(settings.get(f'{device_key} gyro id', ""))
                        rot_x, rot_y, rot_z, rot_w = quat["x"], quat["y"], quat["z"], quat["w"]
                    elif rot_mode == "bad apple":
                        data = BAD_APPLE_STATE.get(device_key, {"on": False})
                        rot_x = 1.0 if data["on"] else 0.0
                except: pass

                buffer_pos = POS_PACKER.pack(float(pos_x), float(pos_y), float(pos_z))
                buffer_rot = ROT_PACKER.pack(float(rot_w), float(rot_x), float(rot_y), float(rot_z))
                
                try:
                    win32file.WriteFile(h_pos, buffer_pos)
                    win32file.WriteFile(h_rot, buffer_rot)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            pass 

        finally:
            for h in [h_pos, h_rot]:
                if h:
                    try:
                        win32pipe.DisconnectNamedPipe(h)
                        win32file.CloseHandle(h)
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

    p_w = np.array(P3[0], dtype=float) 
    tips = [
        np.array(P3[4], dtype=float),#thumb
        np.array(P3[8], dtype=float),#index
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
    #todo: improve hand tracking: make side detection less aggressive(if only right is enabled then the hand can only be right)
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
layout_main.addWidget(set_group("Display", [res], text = "set how tall, wide and fast you want the display to be! refrash rate also locks your max fps"))

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

layout_main.addWidget(set_group("Misc", [misc_group1,misc,recommended_label], 
                                text = "if using stereo(SBS), resolution becomes per eye so dont use 3840 and use 1920 instead, also some specific games will not work if ipd is set to 0.0"))

#offsets ui//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
offsets_ui_dict = {}
def create_offset_ui(device, style = None):
    settings = settings_core.get_settings()

    if style == None:
        style = offsets_style

    world = create_group_horizontal([
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world x", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world x", world.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world y", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world y", world.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world z", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world z", world.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world yaw", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world yaw", world.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world pitch", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world pitch", world.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset world roll", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset world roll", world.findChildren(QDoubleSpinBox)[5].value())
        }
    ])

    local = create_group_horizontal([
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local x", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local x", local.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local y", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local y", local.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local z", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local z", local.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local yaw", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local yaw", local.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local pitch", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local pitch", local.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} offset local roll", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} offset local roll", local.findChildren(QDoubleSpinBox)[5].value())
        }
    ])

    playspace_widget = QWidget()
    playspace_layout = QHBoxLayout(playspace_widget)

    reset_method = create_combobox({
        "text" : "Reset Source",
        "default" : settings.get(f"{device} playspace reset method","Headset"),
        "items" : ["Headset", "Fixed Position"],#, "QR"], #add reset by serial and reset by qrcode(ArUco) also add automatic reset after some time or by detecting drift
        "index change" : lambda: settings_core.update_setting(f"{device} playspace reset method", reset_method.findChildren(QComboBox)[0].currentText())
    })
    settings_core.update_setting(f"{device} playspace reset method", reset_method.findChildren(QComboBox)[0].currentText())
    
    playspace = create_group_horizontal([
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} playspace x", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} playspace x", playspace.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} playspace y", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} playspace y", playspace.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} playspace z", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} playspace z", playspace.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f"{device} playspace yaw", 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f"{device} playspace yaw", playspace.findChildren(QDoubleSpinBox)[3].value())
        },
    ])

    playspace_layout.addWidget(BindingGroupWidget(device, "reset playspace"))

    playspace_layout.addWidget(reset_method)
    playspace_layout.addWidget(playspace)

    # resets_widget = QWidget()
    # resets_layout = QHBoxLayout(resets_widget)

    # pos_bindable = BindingGroupWidget(device, "reset position")
    # rot_bindable = BindingGroupWidget(device, "reset rotation")

    # resets_layout.addWidget(pos_bindable)
    # resets_layout.addWidget(rot_bindable)

    hover = ""
    match device:
        case "hmd":
            group_name = "Offsets"
            hover = "Reset Method should be set to 'Fixed Position' here, increment y and click reset until your floor level feels correct"
        case "cr":
            group_name = "Offsets(Right)"
            hover = "Reset Method should be set to 'Headset' here, to reset move your controller(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"
        case "cl":
            group_name = "Offsets(Left)"
            hover = "Reset Method should be set to 'Headset' here, to reset move your controller(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"
        case _:
            group_name = "Offsets"
            hover = "Reset Method should be set to 'Headset' here, to reset move your tracker(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"

    world_group = set_group("World", [world],"h",style, text = "this moves a device world position and rotation")
    local_group = set_group("Local", [local],"h",style, text = "imagin that your source position or rotation is the parent and your emulated device is the child connected to them, if the parent changes its rotation the child will change both its position and rotation")
    playspace_group = set_group("Play Space", [playspace_widget],"h",style, text = hover)
    # resets_group = set_group("Resets", [resets_widget],"h",style, text = hover)

    final_widget = set_group(group_name, [world_group, local_group, playspace_group],"v",style)
    
    offsets_ui_dict.update({device: {"world" : world_group, "local" : local_group, "playspace" : playspace_group}})

    return final_widget

def update_offsets_ui():
    settings = settings_core.get_settings()
    
    for device, ui_groups in offsets_ui_dict.items():
        
        if "world" in ui_groups and ui_groups["world"]:
            world_spinboxes = ui_groups["world"].findChildren(QDoubleSpinBox)
            if len(world_spinboxes) >= 6:
                for sb in world_spinboxes[:6]: sb.blockSignals(True)
                
                world_spinboxes[0].setValue(settings.get(f"{device} offset world x", 0.0))
                world_spinboxes[1].setValue(settings.get(f"{device} offset world y", 0.0))
                world_spinboxes[2].setValue(settings.get(f"{device} offset world z", 0.0))
                world_spinboxes[3].setValue(settings.get(f"{device} offset world yaw", 0.0))
                world_spinboxes[4].setValue(settings.get(f"{device} offset world pitch", 0.0))
                world_spinboxes[5].setValue(settings.get(f"{device} offset world roll", 0.0))
                
                for sb in world_spinboxes[:6]: sb.blockSignals(False)

        if "local" in ui_groups and ui_groups["local"]:
            local_spinboxes = ui_groups["local"].findChildren(QDoubleSpinBox)
            if len(local_spinboxes) >= 6:
                for sb in local_spinboxes[:6]: sb.blockSignals(True)
                
                local_spinboxes[0].setValue(settings.get(f"{device} offset local x", 0.0))
                local_spinboxes[1].setValue(settings.get(f"{device} offset local y", 0.0))
                local_spinboxes[2].setValue(settings.get(f"{device} offset local z", 0.0))
                local_spinboxes[3].setValue(settings.get(f"{device} offset local yaw", 0.0))
                local_spinboxes[4].setValue(settings.get(f"{device} offset local pitch", 0.0))
                local_spinboxes[5].setValue(settings.get(f"{device} offset local roll", 0.0))
                
                for sb in local_spinboxes[:6]: sb.blockSignals(False)

        if "playspace" in ui_groups and ui_groups["playspace"]:
            playspace_spinboxes = ui_groups["playspace"].findChildren(QDoubleSpinBox)
            if len(playspace_spinboxes) >= 4:
                for sb in playspace_spinboxes[:4]: sb.blockSignals(True)
                
                playspace_spinboxes[0].setValue(settings.get(f"{device} playspace x", 0.0))
                playspace_spinboxes[1].setValue(settings.get(f"{device} playspace y", 0.0))
                playspace_spinboxes[2].setValue(settings.get(f"{device} playspace z", 0.0))
                playspace_spinboxes[3].setValue(settings.get(f"{device} playspace yaw", 0.0))
                
                for sb in playspace_spinboxes[:4]: sb.blockSignals(False)

#expand on this!
class UiUpdater(QObject):
    trigger_ui_update = pyqtSignal()
ui_updater = UiUpdater()
ui_updater.trigger_ui_update.connect(update_offsets_ui)
#offsets ui//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#streaming/////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_streaming():
    dynamic_container = QWidget()
    settings = settings_core.get_settings()

    streaming = create_group_horizontal([
        {
            "type" : "checkbox", 
            "text" : "mirror to window", 
            "default": settings.get("mirror window", False),
            "enabled" : True,
            "func"  : lambda: settings_core.update_setting("mirror window", streaming.findChildren(QCheckBox)[0].isChecked())
        },
        {
            "type" : "checkbox", 
            "text" : "mirror to web", 
            "default": settings.get("mirror web", False),
            "enabled" : True,
            "func"  : lambda: settings_core.update_setting("mirror web", streaming.findChildren(QCheckBox)[1].isChecked())
        },

        {
            "type" : "checkbox", 
            "text" : "start mirrored window fullscreen", 
            "default": settings.get("start mirror window fullscreen", False),
            "enabled" : True,
            "func"  : lambda: settings_core.update_setting("start mirror window fullscreen", streaming.findChildren(QCheckBox)[2].isChecked())
        },
        {
            "type"   : "spinbox",
            "text"   : "start mirror window monitor index",
            "min"    : 0,
            "max"    : 999999999,
            "default": settings.get('start mirror window monitor index', 1),
            "steps"  : 1,
            "func"   : lambda: settings_core.update_setting("start mirror window monitor index", streaming.findChildren(QSpinBox)[0].value())
        },
        {
            "type"   : "spinbox",
            "text"   : "web port",
            "min"    : 0,
            "max"    : 999999999,
            "default": settings.get('mirror web port', 9999),
            "steps"  : 1,
            "func"   : lambda: settings_core.update_setting("mirror web port", streaming.findChildren(QSpinBox)[1].value())
        },
        {
            "type"   : "spinbox",
            "text"   : "bitrate",
            "min"    : 1,
            "max"    : 100,
            "default": settings.get('mirror web bitrate', 100),
            "steps"  : 1,
            "func"   : lambda: settings_core.update_setting("mirror web bitrate", streaming.findChildren(QSpinBox)[2].value())
        },
        {
            "type"   : "doublespinbox",
            "text"   : "res scale",
            "min"    : 0.1,
            "max"    : 1.0,
            "default": settings.get('mirror web scale', 1.0),
            "steps"  : 0.1,
            "func"   : lambda: settings_core.update_setting("mirror web scale", streaming.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "button", 
            "text" : "open stream", 
            "enabled" : True,
            "func"  : lambda: webbrowser.open(f"http://127.0.0.1:{settings.get('mirror web port', 9999)}")
        }
    ])

    return streaming

streaming_block = create_streaming()
layout_main.addWidget(set_group("Mirroring", [streaming_block], 
                                text = "(experimental: slow please avoid!!!) mirror to window: pops out the 'headset window' (alt+enter to fullscreen) mirror to url: streams the 'headset window' to a web page(lower bitrate/res = faster streaming), you can also use Sunshine + moonlight-web-stream for faster performance"))
#streaming/////////////////////////////////////////////////////////////////////////////////////////////////////////////\
offsets_hmd = create_offset_ui("hmd")
layout_main.addWidget(offsets_hmd)
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

#HOW DO PEOPLE KEEP INSTALLING STEAMVR ON DISK D????????????????????????????????????????????????????????????????????????
def install_driver():
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    source_folder = os.path.join(script_dir, "assets", "driver to copy")
    destination_folder = settings_core.get_settings()['drivers path']
    
    if not os.path.exists(source_folder):
        update_install_and_config_label("driver folder 'assets/driver to copy' is missing!")
        return

    if not os.path.exists(destination_folder):
        update_install_and_config_label("destination path does not exist! is steamvr on disk c?")
        return

    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        update_install_and_config_label(None)
    except PermissionError:
        update_install_and_config_label("permission denied! close Steam and SteamVR completely!")
    except Exception as e:
        update_install_and_config_label(f"install failed: {str(e)}")

def remove_driver():
    folder_path = settings_core.get_settings()['drivers path'] + '/glassvrdriver'

    if not os.path.exists(folder_path):
        return

    try:
        shutil.rmtree(folder_path)
        update_install_and_config_label(None)
    except PermissionError:
        update_install_and_config_label("permission denied! close Steam and SteamVR completely!")
    except Exception as e:
        update_install_and_config_label(f"uninstall failed: {str(e)}")

tab_driver = QWidget()
layout_driver = QVBoxLayout(tab_driver)
set_style(tab_driver, "{ background: #1F1F1F; border: 0px solid #444; border-radius: 0px; }", "t")

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
vr_config_path = create_lineedit({
    "text" : "steam config folder path",
    "default" : settings_core.get_settings()['vrsettings path'],
    "func" : lambda: config_path_changed()
})

install_label = create_label({
    "text" : "driver is not installed, click to install to install!", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})

config_label = create_label({
    "text" : "config", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})

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

layout_driver.addWidget(set_group("Driver", [driver_path, vr_config_path, install_label, config_label, install_buttons], text = "click reinstall on every new version to update the driver! also if you somehow installed steamvr not on disk c youll need to change the steamvr drivers folder path(normaly steam wont let you do that but some people just dont play by the rules ;P)"))

def update_install_and_config_label(error_message = None):
    install_leb = install_label.findChild(QLabel)
    config_leb = config_label.findChild(QLabel)

    if error_message is not None:
        install_leb.setText(f"ACTION FAILED: {error_message}")
        install_leb.setStyleSheet("color: red;")
        install_buttons.findChildren(QPushButton)[0].setText("install")
        
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            install_leb.setText("driver is installed ;P")
            install_leb.setStyleSheet("color: green")

            install_buttons.findChildren(QPushButton)[0].setText("reinstall")
            install_buttons.findChildren(QPushButton)[1].setEnabled(True)
        else:
            install_leb.setText("driver not found, click to install to install/update!")
            install_leb.setStyleSheet("color: yellow")

            install_buttons.findChildren(QPushButton)[0].setText("install")
            install_buttons.findChildren(QPushButton)[1].setEnabled(False)

    if get_activateMultipleDrivers_true():
        config_leb.setText('steamvr.vrsettings has: ("activateMultipleDrivers" : true) all good ;P')
        config_leb.setStyleSheet("color: green")
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            config_leb.setText('steamvr.vrsettings is missing: ("activateMultipleDrivers" : true) set the correct path and click to reinstall to add it!')
            config_leb.setStyleSheet("color: yellow")
        else:
            config_leb.setText('steamvr.vrsettings is missing: ("activateMultipleDrivers" : true) set the correct path and click to install to add it!')
            config_leb.setStyleSheet("color: yellow")

update_install_and_config_label()

c_button = create_button({
        "text" : "reset config(ui won't update)",
        "enabled" : True,
        "func"  : lambda: settings_core.reset_settings()
    })
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

layout_driver.addWidget(set_group("Config", [c_button, config, config2], text = "if you hate graphical user interfaces(gui's) you can manually change each setting in settings.json file"))

#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////
def get_public_ip():
    #for "network staff" ofcourse ;P
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
            ctypes.windll.user32.MessageBoxW(0, "OUCH!!!!!!!!!!!", ";P", 0)
            ctypes.windll.user32.MessageBoxW(0, "why???????????????", ";P", 0)
        case 1:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "STOP!!!!", ";P", 0)
        case 2:
            ctypes.windll.user32.MessageBoxW(0, "if i'll show you something cool, will you stop clicking?", ";P", 0)
            dialog += 1
            webbrowser.open("https://danixmir.itch.io/hyperlost")
            ctypes.windll.user32.MessageBoxW(0, "its a game i made!", ":>", 0)
        case 3:
            response = ctypes.windll.user32.MessageBoxW(0, "do you like it?", ";P", 4)
            if response == 6:
                dialog += 1
                ctypes.windll.user32.MessageBoxW(0, "thank you!!!", ";P", 0)
            else:
                system = platform.system()
                if system == "Windows":
                    os.system("shutdown /p")#"shutdown /p" #"shutdown /s /t"
                elif system == "Linux" or system == "Darwin":
                    os.system("sudo shutdown -h now")
        case 4:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "AHH!!!!!!!!!!!!!!!!!!!!!!!!", ";P", 0)
        case 5:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you promised you'll stop", ";P", 0)
        case 6:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i feel betrayed", ";P", 0)
        case 7:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ";P", 0)
        case 8:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "go do something else!!!!!!!!", ":)", 0)
        case 9:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "can you stop??????????", ":)", 0)
        case 10:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "plz stop", ";P", 0)
        case 11:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i have nothing more to show you", ";P", 0)
        case 12:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "(ignores)", ";P", 0)
        case 13:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i know where you live", ";P", 0)
        case 14:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "ip: " + get_public_ip() + "\nmac: " + list_mac_addresses(), ":)", 0)
        case 15:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "now will you stop?", ";P", 0)
        case 16:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i don't understand", ";P", 0)
        case 17:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "since when you were the one in control?", ";P", 0)
        case 18:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "hehe, that was a reference", ";P", 0)
        case 19:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "seriously stop", ";P", 0)
        case 20:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you don't know what you're doing", ";P", 0)
        case 21:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "YOU WILL KILL US BOTH", ";P", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "or not", ";P", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "this is the last straw", ";P", 0)
        case 23:
            dialog += 1
            os.startfile("C:\Windows\System32")
            ctypes.windll.user32.MessageBoxW(0, "I'M GONNA DO IT", ";P", 0)
        case 24:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "wow", ";P", 0)
        case 25:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i give up", ";P", 0)
        case 26:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ";P", 0)
        case 27:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ";P", 0)
        case 28:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ";P", 0)
        case 29:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "so.....?", ";P", 0)
        case 30:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "error", "Alert", 0)
        case 31:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "click one more time i dare you", ";P", 0)
        case 32:
            dialog += 1
            for n in range(2147483647):
                time.sleep(0.01)
                webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        case 34:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you know what, you win", ";P", 0)
        case 35:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "the next dialog is the last, check the source code if you don't believe me", ";P", 0)
        case _:
            ctypes.windll.user32.MessageBoxW(0, ";P", ";P", 0)

tab_credits = QWidget()
layout_credits = QVBoxLayout(tab_credits)
layout_credits.setSpacing(0)

def create_credits():
    create_group = QWidget()
    layout_credits1 = QVBoxLayout(create_group)

    label = QLabel("Made by: DaniXmir") # ;P
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)

    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    image_path = os.path.join(script_dir, "assets", "fix anim.gif")

    gif_label = QLabel()
    gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    movie = QMovie(image_path)
    
    gif_label.movie_ref = movie 
    
    def handle_frame_changed(frame_number):
        current_pixmap = movie.currentPixmap()
        scaled_pixmap = current_pixmap.scaled(
            100, 100, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.FastTransformation
        )
        gif_label.setPixmap(scaled_pixmap)

    movie.frameChanged.connect(handle_frame_changed)
    movie.start()

    gif_label.mousePressEvent = lambda event: click()
    gif_label.setCursor(Qt.CursorShape.PointingHandCursor)

    layout_credits1.addWidget(gif_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    group_links = QWidget()
    layout_link = QHBoxLayout(group_links)
    
    link1 = '<a href="https://github.com/DaniXmir/GlassVr" style="color: #4da6ff;">github!</a>'
    label1 = QLabel("open the project on " + link1)
    label1.setTextFormat(Qt.TextFormat.RichText)
    label1.setOpenExternalLinks(True)
    label1.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    link2 = '<a href="https://discord.gg/jyvWdKBpPj" style="color: #4da6ff;">discord server!</a>'
    label2 = QLabel("join the " + link2)
    label2.setTextFormat(Qt.TextFormat.RichText)
    label2.setOpenExternalLinks(True)
    label2.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    link3 = '<a href="https://www.youtube.com/@danixmir106" style="color: #4da6ff;">youtube!</a>'
    label3 = QLabel("subscribe on " + link3)
    label3.setTextFormat(Qt.TextFormat.RichText)
    label3.setOpenExternalLinks(True)
    label3.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    layout_credits1.addWidget(set_group("Links", [label1, label2, label3], "h", text = "you did subscribe right????"))

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

#scroll_controllers.setMinimumWidth(1800)

check_cl = create_checkbox(
    {
        "text" : "enable left controller", 
        "default" : settings_core.get_settings()['enable cl'], 
        "func" : lambda: enable_device("cl")
    })

check_cr = create_checkbox(
    {
        "text" : "enable right controller", 
        "default" : settings_core.get_settings()['enable cr'], 
        "func" : lambda: enable_device("cr")
    })

layout_controllers.addWidget(set_group("Enable", [check_cr, check_cl], text = "enables right and left controller emulation respectively"))

#controllers modes v2////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
cr_shared_layout = None
cl_shared_layout = None

def update_cr_shared():
    settings = settings_core.get_settings()
    p_mode = settings.get('crpos mode', 'copy')
    r_mode = settings.get('crrot mode', 'copy')

    clear_layout(cr_shared_layout)

    #always///
    input_comm = create_combobox({
        "text"   : "input communication method",
        "default": settings.get("crinput mode","app (named pipe)"),
        "items" : ["app (named pipe)", "UDP"],
        "index change" : lambda: settings_core.update_setting("crinput mode", input_comm.findChildren(QComboBox)[0].currentText())
    })
    cr_shared_layout.addWidget(input_comm)

    skeletal_comm = create_combobox({
        "text"   : "skeletal communication method",
        "default": settings.get("crskeletal mode","app (named pipe)"),
        "items" : ["app (named pipe)", "UDP"],
        "index change" : lambda: settings_core.update_setting("crskeletal mode", skeletal_comm.findChildren(QComboBox)[0].currentText())
    })
    cr_shared_layout.addWidget(skeletal_comm)
    #always///

    if p_mode == "UDP" or r_mode == "UDP":
        t = create_group_horizontal([{
                "type"   : "spinbox",
                "text"   : "port",
                "min"    : 0,
                "max"    : 999999999,
                "default": settings.get('cr port', 9001),
                "steps"  : 1,
                "func"   : lambda: settings_core.update_setting("cr port", t.findChildren(QSpinBox)[0].value())
            }])
        cr_shared_layout.addWidget(t)

    if p_mode == "named pipe" or r_mode == "named pipe":
        t = create_label({"text" : "external named pipe require the ui to be closed"})
        cr_shared_layout.addWidget(t)

    if p_mode == "hand tracking xr" or r_mode == "hand tracking xr":
        t = create_label({"text" : "(hand tracking xr coming soon!)"})
        cr_shared_layout.addWidget(t)

def update_cl_shared():
    settings = settings_core.get_settings()
    p_mode = settings.get('clpos mode', 'copy')
    r_mode = settings.get('clrot mode', 'copy')

    clear_layout(cl_shared_layout)

    #always///
    input_comm = create_combobox({
        "text"   : "input communication method",
        "default": settings.get("clinput mode","app (named pipe)"),
        "items" : ["app (named pipe)", "UDP"],
        "index change"   : lambda: settings_core.update_setting("clinput mode", input_comm.findChildren(QComboBox)[0].currentText()),
    })
    cl_shared_layout.addWidget(input_comm)

    skeletal_comm = create_combobox({
        "text"   : "skeletal communication method",
        "default": settings.get("clskeletal mode","app (named pipe)"),
        "items" : ["app (named pipe)", "UDP"],
        "index change"   : lambda: settings_core.update_setting("clskeletal mode", skeletal_comm.findChildren(QComboBox)[0].currentText()),
    })
    cl_shared_layout.addWidget(skeletal_comm)
    #always///

    if p_mode == "UDP" or r_mode == "UDP":
        t = create_group_horizontal([{
                "type"   : "spinbox",
                "text"   : "port",
                "min"    : 0,
                "max"    : 999999999,
                "default": settings.get('cl port', 9002),
                "steps"  : 1,
                "func"   : lambda: settings_core.update_setting("cl port", t.findChildren(QSpinBox)[0].value())
            }])
        cl_shared_layout.addWidget(t)

    if p_mode == "named pipe" or r_mode == "named pipe":
        t = create_label({"text" : "external named pipe require the ui to be closed"})
        cl_shared_layout.addWidget(t)

    if p_mode == "hand tracking xr" or r_mode == "hand tracking xr":
        t = create_label({"text" : "(hand tracking xr coming soon!)"})
        cl_shared_layout.addWidget(t)


def crpos_specific_widget(layout, combo):
    settings_core.update_setting(f'crpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    settings = settings_core.get_settings()

    update_cr_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("crpos copy serial",""),
                    "items": list(set([settings.get("crpos copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("crpos copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("crpos copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)
            
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

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def crrot_specific_widget(layout, combo):
    settings_core.update_setting(f'crrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    settings = settings_core.get_settings()

    update_cr_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("crrot copy serial",""),
                    "items": list(set([settings.get("crrot copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("crrot copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("crrot copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

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

        # case "hand tracking":
            # t = create_group_horizontal([{
            #         "type" : "button",
            #         "enabled" : True,
            #         "text" :"apply recommended offsets (right)", 
            #         "func"  : lambda: apply_hand_offsets("cr")
            #     }])
            # layout.addWidget(t)

        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings.get("cr gyro id", ""),
                    "items": list({str(settings.get("cr gyro id", "")), *controllers_dict}) if settings.get("hmd gyro id") else list(controllers_dict),
                    "index change": lambda: settings_core.update_setting("cr gyro id", combo_extra.findChild(QComboBox).currentText()),
                    "pre show": lambda cb: (
                        saved := str(settings.get("cr gyro id", "")),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *controllers_dict}) if saved else list(controllers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
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

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def clpos_specific_widget(layout, combo):
    settings_core.update_setting(f'clpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    settings = settings_core.get_settings()

    update_cl_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("clpos copy serial",""),
                    "items": list(set([settings.get("clpos copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("clpos copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("clpos copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

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

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def clrot_specific_widget(layout, combo):
    settings_core.update_setting(f'clrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    settings = settings_core.get_settings()

    update_cl_shared()

    match mode:
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get("clrot copy serial",""),
                    "items": list(set([settings.get("clrot copy serial", "")] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting("clrot copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get("clrot copy serial", ""),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

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

        # case "hand tracking":
            # t = create_group_horizontal([{
            #         "type" : "button",
            #         "enabled" : True,
            #         "text" :"apply recommended offsets (left)", 
            #         "func"  : lambda: apply_hand_offsets("cl")
            #     }])
            # layout.addWidget(t)

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
                    "default": settings.get("cl gyro id", ""),
                    "items": list({str(settings.get("cl gyro id", "")), *controllers_dict}) if settings.get("hmd gyro id") else list(controllers_dict),
                    "index change": lambda: settings_core.update_setting("cl gyro id", combo_extra.findChild(QComboBox).currentText()),
                    "pre show": lambda cb: (
                        saved := str(settings.get("cl gyro id", "")),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *controllers_dict}) if saved else list(controllers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

def create_cr_shared():
    global cr_shared_layout
    w = QWidget()
    cr_shared_layout = QVBoxLayout(w)
    return w

def create_cl_shared():
    global cl_shared_layout
    w = QWidget()
    cl_shared_layout = QVBoxLayout(w)
    return w

def create_cr_widget():
    root_widget = QWidget()
    root_layout = QHBoxLayout(root_widget)

    modes_widget = QWidget()
    modes_layout = QVBoxLayout(modes_widget)

    s = create_cr_shared()

    modes_layout.addWidget(create_crpos_widget())
    modes_layout.addWidget(create_crrot_widget())

    root_layout.addWidget(modes_widget)
    root_layout.addWidget(s)

    #style///
    modes_widget.setStyleSheet("QWidget#cr_modes { background: #1F1F1F; border: 1px solid #444; border-radius: 6px; }")
    modes_widget.setObjectName("cr_modes")
    #style///

    return root_widget

def create_cl_widget():
    root_widget = QWidget()
    root_layout = QHBoxLayout(root_widget)

    modes_widget = QWidget()
    modes_layout = QVBoxLayout(modes_widget)

    s = create_cl_shared()

    modes_layout.addWidget(create_clpos_widget())
    modes_layout.addWidget(create_clrot_widget())

    root_layout.addWidget(modes_widget)
    root_layout.addWidget(s)

    #style///
    modes_widget.setStyleSheet("QWidget#cl_modes { background: #1F1F1F; border: 1px solid #444; border-radius: 6px; }")
    modes_widget.setObjectName("cl_modes")
    #style///

    return root_widget

def create_crpos_widget():
    settings = settings_core.get_settings()
    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right position mode",
            "default": settings.get(f'crpos mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "hand tracking", "hand tracking xr"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
    return tab_extra

def create_crrot_widget():
    settings = settings_core.get_settings()
    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right rotation mode",
            "default": settings.get(f'crrot mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "hand tracking", "hand tracking xr", "gyro"],# "hand+gyro", "marker", "marker+gyro",#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
    return tab_extra

def create_clpos_widget():
    settings = settings_core.get_settings()
    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left position mode",
            "default": settings.get(f'clpos mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "hand tracking", "hand tracking xr"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
    return tab_extra

def create_clrot_widget():
    settings = settings_core.get_settings()
    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left rotation mode",
            "default": settings.get(f'clrot mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "hand tracking", "hand tracking xr", "gyro"],# "hand+gyro", "marker", "marker+gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "index change": lambda: clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
    return tab_extra

layout_controllers.addWidget(set_group("Right Modes", [create_cr_widget()], text = "right controller position and rotation modes"))
layout_controllers.addWidget(set_group("Left Modes", [create_cl_widget()], text = "left controller position and rotation modes"))
#controllers modes v2////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# def apply_hand_offsets(device):
#     if device == "cr":
#         spinboxes = offsets_cr.findChildren(QDoubleSpinBox)

#         settings_core.update_setting(f"{device} offset world yaw", 1.660)
#         spinboxes[3].setValue(1.660)

#         settings_core.update_setting(f"{device} offset world pitch", -0.680)
#         spinboxes[4].setValue(-0.680)

#         settings_core.update_setting(f"{device} offset world roll", 0.670)
#         spinboxes[5].setValue(0.670)

#     else:
#         spinboxes = offsets_cl.findChildren(QDoubleSpinBox)

#         settings_core.update_setting(f"{device} offset world yaw", -1.660)
#         spinboxes[3].setValue(1.660)

#         settings_core.update_setting(f"{device} offset world pitch", 0.680)
#         spinboxes[4].setValue(-0.680)

#         settings_core.update_setting(f"{device} offset world roll", 0.670)
#         spinboxes[5].setValue(0.670)

#mapping v2/////////////////////////////////////////////////////////////////////

mapping = ["a", "b", "trigger", "grip", "menu", 
           "joy up", "joy down", "joy left", "joy right", "joy click", 
           "touch up", "touch down", "touch left", "touch right", "touch click", 
           "thumb", "index", "middle", "ring", "pinky", 
           "touch mod"]

def make_mapping_buttons(prefix):
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    for n in mapping:
        group_layout.addWidget(BindingGroupWidget(prefix, n))

    return group_widget

def make_mapping():
    group_widget = QWidget()
    main_layout = QHBoxLayout(group_widget)

    main_layout.addWidget(set_group("Left Mapping", [make_mapping_buttons("cl")]))
    
    main_layout.addWidget(create_image({"path" : "index black", "size x" : 681, "size y" : 418}))

    main_layout.addWidget(set_group("Right Mapping", [make_mapping_buttons("cr")]))

    return group_widget

layout_controllers.addWidget(set_group("Index Controller Mapping", [make_mapping()], text = "you can bind multiple physical controllers/keyboards/mice to one action, option to invert an axis or button state is also available"))

#real controllers settings/////////////////////////////////////////////////////////////////////////////
scroll_content_layout = None

def make_controller_block(ctrl):
    c_id   = ctrl.get("id", "unknown")
    c_name = ctrl.get("type", "Unknown Controller")
    
    settings = settings_core.get_settings()
    c_conf   = settings.get(c_id, {})

    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

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

    final_widget = set_group(f"Name:({c_name}) ID:({c_id})", [group_widget])

    return final_widget

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

    layout_controllers.addWidget(set_group("Detected Real Controllers", [scroll_area]))
    update_controller_ui()

make_base_scroll()
#real controllers settings/////////////////////////////////////////////////////////////////////////////

#//////////////////////////////////////////////////////////
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
        "func" : lambda: settings_core.update_setting("curl",webcam.findChildren(QCheckBox)[1].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "splay",
        "default" : settings_core.get_settings().get("splay", True),
        "func" : lambda: settings_core.update_setting("splay",webcam.findChildren(QCheckBox)[2].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "index curl effects trigger",
        "default" : settings_core.get_settings().get("index=trigger", False),
        "func" : lambda: settings_core.update_setting("index=trigger",webcam.findChildren(QCheckBox)[3].isChecked())
    },
    {
        "type" : "checkbox", 
        "text" : "other curl effects grip",
        "default" : settings_core.get_settings().get("other=grip", False),
        "func" : lambda: settings_core.update_setting("other=grip",webcam.findChildren(QCheckBox)[4].isChecked())
    }
])

webcam1 = create_group_horizontal([
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset x", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset x", webcam1.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset y", webcam1.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox", 
        "text" :"physical camera offset z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("camera offset z", webcam1.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "spinbox", 
        "text" :"camera index", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera index'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("camera index", webcam1.findChildren(QSpinBox)[0].value())
    }
])

layout_controllers.addWidget(set_group("Hand Tracking",[webcam, webcam1], text = "this is inside-out tracking meaning the camera need be on your face, also dont expect anything crazy.. ok"))

def start_hand_tracking():
    enabled = webcam.findChild(QCheckBox).isChecked()
    settings_core.update_setting("hand tracking", enabled)

    if enabled:
        start_camera()
    else:
        pass

#camera (markers)/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
#                 success, rvec, tvec = cv2.solvePnP(
#                     marker_3d_edges, corners[i][0], camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_IPPE_SQUARE
#                 )
                
#                 if success:
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

#playspace/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def start_reset_playspace():
    thread = threading.Thread(target=reset_playspace_on_input, daemon=True)
    thread.start()

def send_reset_to_phone(device):
    try:
        settings = settings_core.get_settings()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        #sock.sendto(b"RESET", ("192.168.50.103", settings.get(f"{device} port", 9001)))
        sock.sendto(b"RESET", ("<broadcast>", settings.get(f"{device} port", 9001)))
        sock.close()

    except Exception as e:
        pass

def reset_playspace_on_input():
    device_states = {}

    while True:
        try:
            settings = settings_core.get_settings()
            
            devices = ["hmd", "cr", "cl"]
            
            for i in range(settings.get("trackers num",2)):
                devices.append(f"{i}tracker")
            
            for n in devices:
                if n not in device_states:
                    device_states[n] = {"packet_triggered": False, "ui_triggered": False}
                
                raw_e_packet = get_latest_packet(n, 'E')
                packet_reset_requested = False
                
                if raw_e_packet is not None:
                    packet_reset_requested = raw_e_packet.get("reset", False)
                    
                packet_fired = False
                if packet_reset_requested:
                    if not device_states[n]["packet_triggered"]:
                        packet_fired = True
                        device_states[n]["packet_triggered"] = True
                else:
                    device_states[n]["packet_triggered"] = False

                setting_key = f"{n}_reset playspace"
                ui_binding_expr = settings.get(setting_key, "")
                
                ui_reset_requested = False
                if ui_binding_expr:
                    ui_reset_requested = bool(eval_binding(ui_binding_expr))
                
                ui_fired = False
                if ui_reset_requested:
                    if not device_states[n]["ui_triggered"]:
                        ui_fired = True
                        device_states[n]["ui_triggered"] = True
                else:
                    device_states[n]["ui_triggered"] = False

                if packet_fired:
                    reset_playspace(n)
                elif ui_fired:
                    send_reset_to_phone(n)
                    reset_playspace(n)

            time.sleep(0.001)

        except Exception as e:
            time.sleep(0.001)

#need more testing (udp flavored)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def reset_playspace(device):
    settings = settings_core.get_settings()
    
    match settings.get(f"{device} playspace reset method", "Headset"):
        case "Headset":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)
    
            hmd_dict = list(trackers_dict.values())[0]
            raw_p_packet = {"x" : ps_x,"y" : 0.0,"z" : ps_z}#get_latest_packet(device, 'P')
            raw_r_packet = {"x" : 0.0,"y" : 0.0,"z" : 0.0,"w":0.0}#get_latest_packet(device, 'R')

            if raw_p_packet is None:
                raw_p_packet = {"x": 0.0, "y": 0.0, "z": 0.0}
            if raw_r_packet is None:
                raw_r_packet = {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

            hmd_x = hmd_dict.get('pos x', 0.0) if hmd_dict else 0.0
            hmd_y = hmd_dict.get('pos y', 0.0) if hmd_dict else 0.0
            hmd_z = hmd_dict.get('pos z', 0.0) if hmd_dict else 0.0

            hmd_yaw = 0.0
            if hmd_dict and 'rotation matrix' in hmd_dict:
                hmd_mat = hmd_dict['rotation matrix']
                hmd_yaw = math.atan2(hmd_mat[0][2], hmd_mat[0][0])
            
            ps_yaw = hmd_yaw

            w = raw_r_packet["w"]
            x = raw_r_packet["x"]
            y = raw_r_packet["y"]
            z = raw_r_packet["z"]
            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            cos_hmd = math.cos(hmd_yaw)
            sin_hmd = math.sin(hmd_yaw)
            unrotated_hmd_x = hmd_x * cos_hmd - hmd_z * sin_hmd
            unrotated_hmd_z = hmd_x * sin_hmd + hmd_z * cos_hmd

            mid_x = unrotated_hmd_x# - ps_x
            mid_z = unrotated_hmd_z# - ps_z
            mid_y = hmd_y + ps_y

            offset_x = mid_x - raw_p_packet["x"]
            offset_y = mid_y - raw_p_packet["y"]
            offset_z = mid_z - raw_p_packet["z"]

            settings_core.update_setting(f"{device} playspace yaw", ps_yaw)
            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)

            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

            ui_updater.trigger_ui_update.emit()

        case "Fixed Position":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)

            raw_p_packet = {"x" : 0.0,"y" : 0.0,"z" : 0.0}#get_latest_packet(device, 'P')
            raw_r_packet = {"x" : 0.0,"y" : 0.0,"z" : 0.0,"w":0.0}#get_latest_packet(device, 'R')

            if raw_p_packet is None:
                raw_p_packet = {"x": 0.0, "y": 0.0, "z": 0.0}
            if raw_r_packet is None:
                raw_r_packet = {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

            w = raw_r_packet["w"]
            x = raw_r_packet["x"]
            y = raw_r_packet["y"]
            z = raw_r_packet["z"]
            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            mid_x = ps_x
            mid_y = ps_y
            mid_z = ps_z

            offset_x = mid_x - raw_p_packet["x"]
            offset_y = mid_y - raw_p_packet["y"]
            offset_z = mid_z - raw_p_packet["z"]

            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)

            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

            ui_updater.trigger_ui_update.emit()

        #(unfinished)///////////////////////
        case "QR":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)

            raw_p_packet = {"x" : 0.0,"y" : 0.0,"z" : 0.0}#get_latest_packet(device, 'P')
            raw_r_packet = {"x" : 0.0,"y" : 0.0,"z" : 0.0,"w":0.0}#get_latest_packet(device, 'R')

            if raw_p_packet is None:
                raw_p_packet = {"x": 0.0, "y": 0.0, "z": 0.0}
            if raw_r_packet is None:
                raw_r_packet = {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

            #rotation it should be at///////////////////////
            w = get_hand_world_transform("cr")["rot w"]
            x = get_hand_world_transform("cr")["rot x"]
            y = get_hand_world_transform("cr")["rot y"]
            z = get_hand_world_transform("cr")["rot z"]

            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            mid_x = ps_x
            mid_y = ps_y
            mid_z = ps_z

            #position it should be at///////////////////////
            offset_x = mid_x - get_hand_world_transform("cr")["pos x"]
            offset_y = mid_y - get_hand_world_transform("cr")["pos y"]
            offset_z = mid_z - get_hand_world_transform("cr")["pos z"]
            
            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)

            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

            ui_updater.trigger_ui_update.emit()

#playspace/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

offsets_cr = create_offset_ui("cr")
offsets_cl = create_offset_ui("cl")
layout_controllers.addWidget(offsets_cr)
layout_controllers.addWidget(offsets_cl)

#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_trackers = QWidget()
layout_trackers = QVBoxLayout(tab_trackers)
set_style(tab_trackers, "{ background: #1F1F1F; border: 0px solid #444; border-radius: 0px; }", "t")

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
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get(f'{index}trackerpos copy serial'),
                    "items": list(set([settings.get(f'{index}trackerpos copy serial')] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting(f'{index}trackerpos copy serial', combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get(f'{index}trackerpos copy serial'),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        case _:
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
        case "copy":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "Copy Serial",
                    "default": settings.get(f'{index}trackerrot copy serial'),
                    "items": list(set([settings.get(f'{index}trackerrot copy serial')] + list(trackers_dict))),
                    "index change": lambda: settings_core.update_setting(f'{index}trackerrot copy serial', combo_extra.findChildren(QComboBox)[0].currentText()),
                    "pre show": lambda cb: (
                        saved := settings.get(f'{index}trackerrot copy serial'),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)), 
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        case "gyro":
            combo_extra = create_combobox({
                    "type" : "combobox",
                    "text": "gyro id",
                    "default": settings.get(f'{index}tracker gyro id', ""),
                    "items": list({str(settings.get(f'{index}tracker gyro id', "")), *controllers_dict}) if settings.get("hmd gyro id") else list(controllers_dict),
                    "index change": lambda: settings_core.update_setting(f'{index}tracker gyro id', combo_extra.findChild(QComboBox).currentText()),
                    "pre show": lambda cb: (
                        saved := str(settings.get(f'{index}tracker gyro id', "")),
                        val := cb.currentText(), 
                        cb.clear(), 
                        cb.addItems(list({saved, *controllers_dict}) if saved else list(controllers_dict)),
                        cb.setCurrentText(val), 
                        None
                    )[-1]
                })
            layout.addWidget(combo_extra)

        case _:
            t = create_group_horizontal([{
                    "type" : "label",
                    "text" : "",
                    "alignment" : Qt.AlignmentFlag.AlignCenter,
                }])
            layout.addWidget(t)

#trackers widget v2//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_tracker_widget(index=0):
    settings = settings_core.get_settings()

    tracker_shared_layout = [None]

    #style///
    hue = (index * 36) % 360
    bg = QColor.fromHsv(hue, 40 + index, 50)
    border = QColor.fromHsv(hue, 120 + index, 180)

    group_style = f"""
        QGroupBox {{
            background-color: {bg.name()};
            border: 1px solid {border.name()};
            border-radius: 8px;
            margin-top: 1.5ex;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            color: {border.name()};
        }}
    """
    #style///

    def update_tracker_shared():
        if tracker_shared_layout[0] is None:
            return
        p_mode = settings_core.get_settings().get(f'{index}trackerpos mode', 'copy')
        r_mode = settings_core.get_settings().get(f'{index}trackerrot mode', 'copy')

        clear_layout(tracker_shared_layout[0])

        if p_mode == "UDP" or r_mode == "UDP":
            t = create_group_horizontal([{
                    "type"   : "spinbox",
                    "text"   : "port",
                    "min"    : 0,
                    "max"    : 999999999,
                    "default": settings_core.get_settings().get(f'{index}tracker port', 9003 + index),
                    "steps"  : 1,
                    "func"   : lambda: settings_core.update_setting(f'{index}tracker port', t.findChildren(QSpinBox)[0].value())
                }])
            settings_core.update_setting(f'{index}tracker port', t.findChildren(QSpinBox)[0].value())
            tracker_shared_layout[0].addWidget(t)

        if p_mode == "named pipe" or r_mode == "named pipe":
            t = create_label({"text" : "external named pipe require the ui to be closed"})
            tracker_shared_layout[0].addWidget(t)

    def _trackerpos_specific(layout, combo):
        settings_core.update_setting(f'{index}trackerpos mode', combo.currentText())

        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        mode = combo.currentText()
        s = settings_core.get_settings()

        update_tracker_shared()

        match mode:
            case "copy":
                combo_extra = create_combobox({
                        "type" : "combobox",
                        "text": "Copy Serial",
                        "default": s.get(f'{index}trackerpos copy serial'),
                        "items": list(set([s.get(f'{index}trackerpos copy serial')] + list(trackers_dict))),
                        "index change": lambda: settings_core.update_setting(f'{index}trackerpos copy serial', combo_extra.findChildren(QComboBox)[0].currentText()),
                        "pre show": lambda cb: (
                            saved := s.get(f'{index}trackerpos copy serial'),
                            val := cb.currentText(),
                            cb.clear(),
                            cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)),
                            cb.setCurrentText(val),
                            None
                        )[-1]
                    })
                layout.addWidget(combo_extra)
            case _:
                layout.addWidget(create_group_horizontal([{"type":"label","text":"","alignment":Qt.AlignmentFlag.AlignCenter}]))

    def _trackerrot_specific(layout, combo):
        settings_core.update_setting(f'{index}trackerrot mode', combo.currentText())

        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        mode = combo.currentText()
        s = settings_core.get_settings()

        update_tracker_shared()

        match mode:
            case "copy":
                combo_extra = create_combobox({
                        "type" : "combobox",
                        "text": "Copy Serial",
                        "default": s.get(f'{index}trackerrot copy serial'),
                        "items": list(set([s.get(f'{index}trackerrot copy serial')] + list(trackers_dict))),
                        "index change": lambda: settings_core.update_setting(f'{index}trackerrot copy serial', combo_extra.findChildren(QComboBox)[0].currentText()),
                        "pre show": lambda cb: (
                            saved := s.get(f'{index}trackerrot copy serial'),
                            val := cb.currentText(),
                            cb.clear(),
                            cb.addItems(list({saved, *trackers_dict}) if saved else list(trackers_dict)),
                            cb.setCurrentText(val),
                            None
                        )[-1]
                    })
                layout.addWidget(combo_extra)
            case "gyro":
                combo_extra = create_combobox({
                        "type" : "combobox",
                        "text": "gyro id",
                        "default": s.get(f'{index}tracker gyro id', ""),
                        "items": list({str(s.get(f'{index}tracker gyro id', "")), *controllers_dict}) if s.get(f'{index}tracker gyro id') else list(controllers_dict),
                        "index change": lambda: settings_core.update_setting(f'{index}tracker gyro id', combo_extra.findChild(QComboBox).currentText()),
                        "pre show": lambda cb: (
                            saved := str(s.get(f'{index}tracker gyro id', "")),
                            val := cb.currentText(),
                            cb.clear(),
                            cb.addItems(list({saved, *controllers_dict}) if saved else list(controllers_dict)),
                            cb.setCurrentText(val),
                            None
                        )[-1]
                    })
                layout.addWidget(combo_extra)
            case _:
                layout.addWidget(create_group_horizontal([{"type":"label","text":"","alignment":Qt.AlignmentFlag.AlignCenter}]))

    outer_widget = QWidget()
    outer_layout = QVBoxLayout(outer_widget)

    root_widget = QWidget()
    root_layout = QHBoxLayout(root_widget)

    modes_widget = QWidget()
    modes_layout = QVBoxLayout(modes_widget)

    shared_widget = QWidget()
    sl = QVBoxLayout(shared_widget)
    tracker_shared_layout[0] = sl

    #pos
    tab_extrapos = QWidget()
    layout_extrapos = QHBoxLayout(tab_extrapos)
    combopos_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} position mode',
            "default": settings.get(f'{index}trackerpos mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe"],
            "index change": lambda: _trackerpos_specific(layout_extrapos, combopos_extra.findChild(QComboBox))
        })
    layout_extrapos.addWidget(combopos_extra)
    _trackerpos_specific(layout_extrapos, combopos_extra.findChild(QComboBox))
    modes_layout.addWidget(tab_extrapos)

    #rot
    tab_extrarot = QWidget()
    layout_extrarot = QHBoxLayout(tab_extrarot)
    comborot_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} rotation mode',
            "default": settings.get(f'{index}trackerrot mode', "copy"),
            "items": ["copy", "offsets", "UDP", "named pipe", "gyro"],
            "index change": lambda: _trackerrot_specific(layout_extrarot, comborot_extra.findChild(QComboBox))
        })
    layout_extrarot.addWidget(comborot_extra)
    _trackerrot_specific(layout_extrarot, comborot_extra.findChild(QComboBox))
    modes_layout.addWidget(tab_extrarot)

    root_layout.addWidget(modes_widget)
    root_layout.addWidget(shared_widget)
    
    offsets_tracker = create_offset_ui(f"{index}tracker", group_style)

    outer_layout.addWidget(set_group("Modes", [root_widget], "v", group_style, text = f"tracker {index} position and rotation modes"))

    outer_layout.addWidget(offsets_tracker)

    modes_widget.setObjectName(f"tracker_root_{index}")
    modes_widget.setStyleSheet(
        f"QWidget#tracker_root_{index} {{"
        f" background: {bg.name()};"
        f" border: 1px solid {border.name()};"
        f" border-radius: 6px; }}"
    )

    final_widget = set_group(f"Tracker {index}", [outer_widget], "v", group_style)
    
    enable_device(f"{index}tracker")
    
    return final_widget
#trackers widget v2//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

tab_devices = QWidget()
layout_devices = QVBoxLayout(tab_devices)

devices_arr = []

def create_trackers_display():
    settings_core.update_setting("trackers num", tracker_num.findChild(QSpinBox).value())
    settings = settings_core.get_settings()
    devices_arr.clear()
    clear_layout(layout_devices)

    if settings['trackers num'] == 64:
        b = create_button({
        "text" : "PLAY BAD APPLE!!!",
        "enabled" : True,
        "func"  : lambda: start_bad_apple()
        })
        layout_devices.addWidget(b)

    if settings['trackers num'] > 0:
        for n in range(settings['trackers num']):
            devices_arr.append(create_tracker_widget(n))

        container = QWidget()
        container_layout = QVBoxLayout(container)
        for widget in devices_arr:
            container_layout.addWidget(widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        layout_devices.addWidget(scroll_area)

tracker_num = create_spinbox({
        "text" : "create trackers",
        "min":0, 
        "max":64, 
        "default":settings_core.get_settings()['trackers num'], 
        "steps" : 1,
        "func"  : lambda: create_trackers_display()
    })
create_trackers_display()

layout_trackers.addWidget(tracker_num)
layout_trackers.addWidget(tab_devices)
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#found trackers display////////////////////////////////////////////////////
first_widget = QWidget()
first_layout = QHBoxLayout(first_widget)

first_label = create_label({
    "text" : "steamvr is not running :(", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})

first_button = create_button({
        "text": "Toggle Found Devices",
        "func": lambda: flip_vis_found()
    })

def flip_vis_found():
    if scroll_detected.isVisible():
        scroll_detected.hide()
    else:
        scroll_detected.show()

    settings_core.update_setting("show detected", scroll_detected.isVisible())

first_layout.addWidget(first_label)
first_layout.addWidget(first_button)

# found_widget = QWidget()
# found_layout = QVBoxLayout(found_widget)

scroll_detected = QScrollArea()
scroll_detected.setWidgetResizable(True)

# scroll_detected.setMinimumHeight(190)
scroll_detected.setMaximumHeight(190)

# scroll_detected.setMinimumWidth(190)
# scroll_detected.setMaximumWidth(190)

detected_widget = QWidget()
detected_layout = QHBoxLayout(detected_widget)

scroll_detected.setWidget(detected_widget)
# found_layout.addWidget(scroll_detected)
# found_layout.addWidget(first_widget)

def boot_change_detected_vis():
    if settings_core.get_settings().get("show detected", True):
        scroll_detected.show()
    else:
        scroll_detected.hide()

boot_change_detected_vis()
#found trackers display////////////////////////////////////////////////////

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

#bad apple/////////////////////////////////////////////////////////////////////////////////////////////////////
BAD_APPLE_STATE = {}

def start_bad_apple():
    for n in range(64):
        settings_core.update_setting(f"{n}trackerpos mode", "bad apple")

        if settings_core.get_settings().get("bad apple ui", True):
            settings_core.update_setting(f"{n}trackerrot mode", "bad apple")
        else:
            settings_core.update_setting(f"{n}trackerrot mode", "good apple")

    thread = threading.Thread(target=bad_apple, daemon=True)
    thread.start()

def bad_apple(): 
    
    speed = settings_core.get_settings().get("bad apple speed", 10.0) #speed(higher == slower)
    # 1 == normal(best but steamvr will crash if rot mode is enabled)
    # 10 == stable(looks ok)
    # 40 == very slow but good for ui(will take like 2 hours if not more)
    
    global BAD_APPLE_STATE
    video_path = os.path.join(os.getcwd(), "assets", "Bad Apple.mp4")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30.0
    
    frame_duration = (1.0 / fps) * speed
    
    grid_w, grid_h = 7, 8
    start_index = 2
    total_trackers = 64
    mod = 0.1 

    try:
        start_time = time.perf_counter()
        frame_count = 0

        while cap.isOpened():
            target_time = start_time + (frame_count * frame_duration)
            
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                start_time = time.perf_counter()
                frame_count = 0
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            next_frame_state = {}
            try:
                hmd_data = list(trackers_dict.values())[0]
                hmd_pos = np.array([hmd_data['pos x'], hmd_data['pos y'], hmd_data['pos z']])
                hmd_rot = R.from_matrix(hmd_data['rotation matrix'])
                world_backward_pos = hmd_pos + hmd_rot.apply(np.array([0, 0, 10]))
            except:
                world_backward_pos = np.array([0, 0, 10])

            for i in range(total_trackers):
                next_frame_state[f"{i}tracker"] = {
                    "on": False,
                    "pos x": float(world_backward_pos[0]), 
                    "pos y": float(world_backward_pos[1]),
                    "pos z": float(world_backward_pos[2])
                }

            h, w = thresh.shape
            cell_h, cell_w = h // grid_h, w // grid_w

            current_tracker = start_index
            for y in range(grid_h):
                for x in range(grid_w):
                    y0, y1 = y * cell_h, (y + 1) * cell_h
                    x0, x1 = x * cell_w, (x + 1) * cell_w
                    
                    cell = thresh[y0:y1, x0:x1]
                    
                    if np.mean(cell) < 127:
                        next_frame_state[f"{current_tracker}tracker"] = {
                            "on": True,
                            "pos x": float(x * mod), 
                            "pos y": float((grid_h - 1 - y) * mod),
                            "pos z": 0.0
                        }
                    current_tracker += 1

            BAD_APPLE_STATE.update(next_frame_state)
            cv2.imshow("Bad Apple!!!", frame)
            cv2.waitKey(1) 

            frame_count += 1
            while time.perf_counter() < target_time:
                remaining = target_time - time.perf_counter()
                if remaining > 0.005:
                    time.sleep(0.001)
                else:
                    pass 

    finally:
        cap.release()
        cv2.destroyAllWindows()
#bad apple/////////////////////////////////////////////////////////////////////////////////////////////////////

#dark mode/////////////////////////////////////////////////////////////////////////////////////////////////////
def is_dark_mode():
    palette = QApplication.instance().palette()
    bg = palette.color(QPalette.ColorRole.Window)
    return bg.lightness() < 128

def start_dark_mode():
    thread = threading.Thread(target=dark_mode, daemon=True)
    thread.start()

def dark_mode():
    try:
        while True:
            if not is_dark_mode():
                WHY_LIGHT_MODE()
            else:
                thank_you()

            time.sleep(5)
    except:
        pass

def WHY_LIGHT_MODE():
    pass
    #print(is_dark_mode())

def thank_you():
    pass
    #print(is_dark_mode())

#dark mode/////////////////////////////////////////////////////////////////////////////////////////////////////

#mirroring//////////////////////////////////////////////////////////////////////////////////////////////////////
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

flask_app = Flask(__name__)

latest_raw_frame     = None
latest_encoded_frame = None
_capture_started     = False

class WindowMirror:

    def __init__(self, window_name):
        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise Exception(f"Could not find '{window_name}'.")

        rect = win32gui.GetWindowRect(self.hwnd)
        self.w = rect[2] - rect[0]
        self.h = rect[3] - rect[1]
        if self.w <= 0 or self.h <= 0:
            self.w, self.h = 1280, 720

    def capture_frame(self):
        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc  = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        rect = win32gui.GetWindowRect(self.hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w > 0 and h > 0:
            self.w, self.h = w, h

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, self.w, self.h)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0, 0), (self.w, self.h), mfc_dc, (0, 0), win32con.SRCCOPY)

        raw = bitmap.GetBitmapBits(True)
        img = np.frombuffer(raw, dtype="uint8").reshape((self.h, self.w, 4))

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def _shared_capture_loop():
    global latest_raw_frame, latest_encoded_frame

    while True:
        mirror = None
        while mirror is None:
            try:
                mirror = WindowMirror("Headset Window")
            except Exception as e:
                time.sleep(2)

        while True:
            try:
                settings = settings_core.get_settings()

                frame = mirror.capture_frame()
                latest_raw_frame = frame

                scale = settings.get("mirror web scale", 100)
                small = cv2.resize(frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                ok, enc = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, settings.get("mirror web bitrate", 100)])
                if ok:
                    latest_encoded_frame = enc.tobytes()
            except Exception as e:
                time.sleep(2)
                break

def _ensure_capture_running():
    global _capture_started
    if not _capture_started:
        _capture_started = True
        threading.Thread(target=_shared_capture_loop, daemon=True).start()

def generate_stream_bytes():
    global latest_encoded_frame
    yield b"--frame\r\n"
    while True:
        if latest_encoded_frame is not None:
            yield b"Content-Type: image/jpeg\r\n\r\n" + latest_encoded_frame + b"\r\n--frame\r\n"
        time.sleep(0.0)

@flask_app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>Headset Window Stream</title><style>
body{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden;user-select:none}
canvas{width:100vw;height:100vh;object-fit:contain;image-rendering:pixelated;cursor:pointer}
</style></head><body>
<canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
function load(){const i=new Image();i.onload=()=>{c.width=i.naturalWidth;c.height=i.naturalHeight;ctx.drawImage(i,0,0);setTimeout(()=>load(),1)};i.onerror=()=>setTimeout(()=>load(),1000);i.src='/frame.jpg?t='+Date.now()}
c.addEventListener('dblclick',()=>{if(!document.fullscreenElement)c.requestFullscreen();else document.exitFullscreen()});
window.onload=load;
</script></body></html>"""

@flask_app.route("/frame.jpg")
def single_frame():
    if latest_encoded_frame is None:
        return "", 204
    return Response(latest_encoded_frame, mimetype="image/jpeg")

@flask_app.route("/stream")
def video_feed():
    return Response(generate_stream_bytes(), mimetype="multipart/x-mixed-replace; boundary=frame")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def start_mirror_window():
    threading.Thread(target=mirror_window, daemon=True).start()

def start_mirror_web():
    threading.Thread(target=mirror_web, daemon=True).start()

import tkinter as tk

def get_monitor_position(index=1):
    root = tk.Tk()
    root.withdraw()
    monitors = []
    for m in root.tk.call('wm', 'maxsize', '.'):
        pass
    root.destroy()
    from screeninfo import get_monitors
    monitors = get_monitors()
    if index < len(monitors):
        return monitors[index].x, monitors[index].y
    return 0, 0

def mirror_window():
    settings = settings_core.get_settings()
    window_open = False
    fullscreen = settings.get("start mirror window fullscreen", False)
    win_name = "Mirror - Headset Window"
    alt_enter_prev = False

    pre_monitor_index = settings.get("start mirror window monitor index", 0)
    while True:
        settings = settings_core.get_settings()
        enabled  = settings.get("mirror window", False)

        if not enabled:
            if window_open:
                cv2.destroyWindow(win_name)
                window_open = False
                fullscreen = False
                alt_enter_prev = False
            time.sleep(0.5)
            continue

        _ensure_capture_running()

        if not window_open:
            cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
            window_open = True
            x, y = get_monitor_position(settings.get("start mirror window monitor index", 0))
            cv2.moveWindow(win_name, x, y)
            if settings.get("start mirror window fullscreen", False):
                cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        if latest_raw_frame is not None:
            cv2.imshow(win_name, latest_raw_frame)
        cv2.waitKey(1)

        alt_held = win32api.GetAsyncKeyState(0x12) & 0x8000
        enter_held = win32api.GetAsyncKeyState(0x0D) & 0x8000
        alt_enter_now = bool(alt_held and enter_held)

        if alt_enter_now and not alt_enter_prev:
            fullscreen = not fullscreen
            if fullscreen:
                cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        alt_enter_prev = alt_enter_now

        current_monitor_index = settings.get("start mirror window monitor index", 0)
        if pre_monitor_index != current_monitor_index:
            x, y = get_monitor_position(settings.get("start mirror window monitor index", 0))
            cv2.moveWindow(win_name, x, y)
            pre_monitor_index = settings.get("start mirror window monitor index", 0)

def mirror_web():
    settings = settings_core.get_settings()
    
    flask_started = False
    PORT = settings.get("mirror web port", 9999)

    while True:
        enabled = settings_core.get_settings().get("mirror web", False)

        if not enabled:
            time.sleep(0.5)
            continue

        _ensure_capture_running()

        if not flask_started:
            flask_started = True
            LOCAL_IP = get_local_ip()
            print("=" * 70)
            print(f"  LOCAL ACCESS URL:   http://localhost:{PORT}/")
            print(f"  NETWORK STREAM URL: http://{LOCAL_IP}:{PORT}/")
            print("=" * 70)

            threading.Thread(
                target=lambda: flask_app.run(host="0.0.0.0", port=PORT, threaded=True,
                                             debug=False, use_reloader=False),
                daemon=True
            ).start()

        time.sleep(1)
#mirroring//////////////////////////////////////////////////////////////////////////////////////////////////////

#resets to 0, maybe add later//////////////////////////////////////////////////////////////////////////////////////////////////////
# def start_resets_pos_rot():
#     thread = threading.Thread(target=resets_pos_rot, daemon=True)
#     thread.start()

#merge this with playspace (method "to zero")
# def resets_pos_rot():
#     while True:
#         try:
#             settings = settings_core.get_settings()

#             if eval_binding(settings.get(f"hmd_reset position")):
#                 hmd_dict = list(trackers_dict.values())[0]

#                 hmd_x = hmd_dict.get('pos x', 0.0)
#                 hmd_y = hmd_dict.get('pos y', 0.0)
#                 hmd_z = hmd_dict.get('pos z', 0.0)

#                 offset_x = -hmd_x
#                 offset_y = -hmd_y
#                 offset_z = -hmd_z

#                 settings_core.update_setting("hmd offset world x", offset_x)
#                 settings_core.update_setting("hmd offset world y", offset_y)
#                 settings_core.update_setting("hmd offset world z", offset_z)

#             if eval_binding(settings.get(f"hmd_reset rotation")):
#                 hmd_yaw = 0.0
#                 if 'rotation matrix' in hmd_dict:
#                     mat = hmd_dict['rotation matrix']
#                     hmd_yaw = math.atan2(mat[0][2], mat[0][0])

#                 world_offset_yaw = -hmd_yaw
#                 world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

#                 settings_core.update_setting("hmd offset world yaw", world_offset_yaw)

#             time.sleep(0.001)
#         except:
#             time.sleep(0.001)
#resets to 0, maybe add later//////////////////////////////////////////////////////////////////////////////////////////////////////

#reset xr//////////////////////////////////////////////////////////////////////////////////////////////////////
def start_reset_xr():
    thread = threading.Thread(target=reset_xr, daemon=True)
    thread.start()

def reset_xr():
    pipe_name = r'\\.\pipe\GlassVR_HMD_Extra'
    pipe_handle = None

    while True:
        try:
            if pipe_handle is None:
                try:
                    pipe_handle = create_pipe(pipe_name)
                    win32pipe.ConnectNamedPipe(pipe_handle, None)
                except Exception :
                    time.sleep(0.5)
                    continue

            settings = settings_core.get_settings()
            is_pressed = bool(eval_binding(settings.get("hmd_reset xr")))
            
            data = struct.pack('?', is_pressed)

            try:
                win32file.WriteFile(pipe_handle, data)
            except pywintypes.error as e:
                if e.winerror in [109, 232]: 
                    win32pipe.DisconnectNamedPipe(pipe_handle)
                    win32file.CloseHandle(pipe_handle)
                    pipe_handle = None

            time.sleep(0.01) 
            
        except Exception as e:
            print(e)
            time.sleep(0.01)
#reset xr//////////////////////////////////////////////////////////////////////////////////////////////////////

if __name__ == '__main__':
    if settings_core.get_settings()['hand tracking']:
        start_camera()
    # if settings_core.get_settings()['markers']:
    #     start_markers()

    start_controller_mapping()

    start_send_data()
    start_update_vrlabel()

    start_reset_gyro()
    # start_resets_pos_rot()
    start_reset_xr()
    start_reset_playspace()

    start_udp_thread()

    start_mirror_window()
    start_mirror_web()

    #start_bad_apple()
    #start_dark_mode()

tabs.addTab(scroll_hmd, "Hmd")
tabs.addTab(scroll_controllers, "Controllers")

tabs.addTab(tab_trackers, "Trackers")
tabs.addTab(tab_driver, "Driver")
tabs.addTab(tab_credits, "Credits")

help_label = create_label({"text" : "hi!!! ;P"})
window_layout.addWidget(help_label)
window_layout.addWidget(tabs)
window_layout.addWidget(scroll_detected)#found_widget)

window.show()
app.exec()

#;P