#polls sdl values to move the selected device

#movement doesnt calculates offsets keep them 0!
#TODO: add controller support for camera

import time
import math
import numpy as np
from scipy.spatial.transform import Rotation as R

import elements as el
import controller_handler as sdl
import settings as se
import steamvr as svr

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QTimer, QEvent, QPoint, QRect
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QColor, QPalette, QMovie

import globals as gl

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

title = "wasd"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 1.0

_current_yaw = 0.0
_current_pitch = 0.0

def pos_mode():
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    speed = el.doublespinbox({
    "text" : "speed", 
    "min":-999999999, 
    "max":999999999, 
    "default":se.get_settings().get("wasd speed", 0.05), 
    "steps" : 0.01,
    "func" : lambda: se.update_setting("wasd speed", speed.findChildren(QDoubleSpinBox)[0].value())
    })
    w = el.bindable({"prefix" : device, "mapping" : "forward"})
    a = el.bindable({"prefix" : device, "mapping" : "left"})
    s = el.bindable({"prefix" : device, "mapping" : "backward"})
    d = el.bindable({"prefix" : device, "mapping" : "right"})

    up = el.bindable({"prefix" : device, "mapping" : "up"})
    down = el.bindable({"prefix" : device, "mapping" : "down"})

    group_layout.addWidget(speed)

    group_layout.addWidget(w)
    group_layout.addWidget(a)
    group_layout.addWidget(s)
    group_layout.addWidget(d)

    group_layout.addWidget(up)
    group_layout.addWidget(down)

    return group_widget

def rot_mode():
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    sensitivity_setting = f"{device}rot mouse sensitivity"
    invert_x_setting = f"{device}rot invert x"
    invert_y_setting = f"{device}rot invert y"
    use_mouse_setting = f"{device}rot use mouse"

    settings = se.get_settings()

    use_mouse_box = el.checkbox({
        "text": "Use Mouse",
        "default": settings.get(use_mouse_setting, True),
        "func": lambda: se.update_setting(use_mouse_setting, not se.get_settings().get(use_mouse_setting, True))
    })

    sensitivity_setting = f"{device}rot mouse sensitivity"
    invert_x_setting = f"{device}rot invert x"
    invert_y_setting = f"{device}rot invert y"

    settings = se.get_settings()

    sens_box = el.doublespinbox({
        "text": "Mouse Sensitivity",
        "default": settings.get(sensitivity_setting, 0.050),
        "min": 0.001,
        "max": 10.0,
        "step": 0.005,
        "func": lambda: se.update_setting(sensitivity_setting, sens_box.findChildren(QDoubleSpinBox)[0].value())
    })

    invert_x_box = el.checkbox({
        "text": "Invert Mouse X",
        "default": settings.get(invert_x_setting, False),
        "func": lambda: se.update_setting(invert_x_setting, not se.get_settings().get(invert_x_setting, False))
    })

    invert_y_box = el.checkbox({
        "text": "Invert Mouse Y",
        "default": settings.get(invert_y_setting, False),
        "func": lambda: se.update_setting(invert_y_setting, not se.get_settings().get(invert_y_setting, False))
    })

    cam_up = el.bindable({"prefix": device, "mapping": "cam_up"})
    cam_down = el.bindable({"prefix": device, "mapping": "cam_down"})
    cam_left = el.bindable({"prefix": device, "mapping": "cam_left"})
    cam_right = el.bindable({"prefix": device, "mapping": "cam_right"})

    group_layout.addWidget(use_mouse_box)
    group_layout.addWidget(sens_box)
    group_layout.addWidget(invert_x_box)
    group_layout.addWidget(invert_y_box)

    group_layout.addWidget(cam_up)
    group_layout.addWidget(cam_down)
    group_layout.addWidget(cam_left)
    group_layout.addWidget(cam_right)

    return group_widget


def loop(data):
    global px, py, pz, rx, ry, rz, rw, device, _current_yaw, _current_pitch

    stop_event = data.get("stop_event")

    while not stop_event.is_set():
        if device is None:
            time.sleep(0.01)
            continue

        settings = se.get_settings()
        rot_mode_setting = settings.get(f"{device}rot mode", "wasd")

        if rot_mode_setting == "wasd":
            mouse_dx, mouse_dy = sdl.get_mouse_delta() if hasattr(sdl, "get_mouse_delta") else (0.0, 0.0)

            if settings.get(f"{device}rot use mouse", True):
                dx, dy = mouse_dx, mouse_dy
            else:
                dx, dy = 0.0, 0.0   # still polled above so the delta doesn't pile up

            sensitivity = settings.get(f"{device}rot mouse sensitivity", 0.050)

            dx += (sdl.eval_binding(settings.get(f"{device}_cam_right", ""))
                   - sdl.eval_binding(settings.get(f"{device}_cam_left", ""))) * (sensitivity*1000)
            dy += (sdl.eval_binding(settings.get(f"{device}_cam_down", ""))
                   - sdl.eval_binding(settings.get(f"{device}_cam_up", ""))) * (sensitivity*1000)
            
            invert_x = 1.0 if settings.get(f"{device}rot invert x", False) else -1.0
            invert_y = 1.0 if settings.get(f"{device}rot invert y", False) else -1.0

            _current_yaw += dx * sensitivity * invert_x
            _current_pitch += dy * sensitivity * invert_y
            _current_pitch = max(-89.0, min(89.0, _current_pitch))

            rot_yaw = R.from_euler('Y', _current_yaw, degrees=True)
            rot_pitch = R.from_euler('X', _current_pitch, degrees=True)
            quat = (rot_yaw * rot_pitch).as_quat()

            rx, ry, rz, rw = float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3])
            
            yaw_rad = math.radians(_current_yaw)
            fwd_x, fwd_z = -math.sin(yaw_rad), -math.cos(yaw_rad)
            right_x, right_z = math.cos(yaw_rad), -math.sin(yaw_rad)

        else:
            trackers_dict = svr.get_trackers_dict()
            copy_serial = gl.device_to_serial(device)
            tracker_data = trackers_dict.get(copy_serial, {})

            rot_matrix = tracker_data.get("rotation matrix", None)

            if rot_matrix is not None:
                yaw, pitch, roll = R.from_matrix(rot_matrix).as_euler('yxz', degrees=True)
                _current_yaw = float(yaw)

                yaw_rad = math.radians(_current_yaw)
                fwd_x, fwd_z = -math.sin(yaw_rad), -math.cos(yaw_rad)
                right_x, right_z = math.cos(yaw_rad), -math.sin(yaw_rad)

                quat = R.from_matrix(rot_matrix).as_quat()
                rx, ry, rz, rw = float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3])
            else:
                yaw_rad = math.radians(_current_yaw)
                fwd_x, fwd_z = -math.sin(yaw_rad), -math.cos(yaw_rad)
                right_x, right_z = math.cos(yaw_rad), -math.sin(yaw_rad)

        pos_mode_setting = settings.get(f"{device}pos mode", "wasd")
        
        if pos_mode_setting == "wasd":
            fwd_input = sdl.eval_binding(settings.get(f"{device}_forward", "")) - sdl.eval_binding(settings.get(f"{device}_backward", ""))
            side_input = sdl.eval_binding(settings.get(f"{device}_right", "")) - sdl.eval_binding(settings.get(f"{device}_left", ""))

            px += (fwd_x * fwd_input + right_x * side_input) * se.get_settings().get("wasd speed", 0.05)
            pz += (fwd_z * fwd_input + right_z * side_input) * se.get_settings().get("wasd speed", 0.05)

            py += sdl.eval_binding(settings.get(f"{device}_up", "")) * se.get_settings().get("wasd speed", 0.05)
            py -= sdl.eval_binding(settings.get(f"{device}_down", "")) * se.get_settings().get("wasd speed", 0.05)
        else:
            trackers_dict = svr.get_trackers_dict()
            copy_serial = settings.get(f"{device}pos copy serial", "")
            tracker_data = trackers_dict.get(copy_serial, {})
            
            px = tracker_data.get("pos x", px)
            py = tracker_data.get("pos y", py)
            pz = tracker_data.get("pos z", pz)

        time.sleep(0.01)