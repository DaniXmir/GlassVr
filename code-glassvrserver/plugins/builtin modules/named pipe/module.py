#ghost module, doesnt send data
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea,
    QGroupBox, QFrame
)

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

def _disable_pipe_checkbox(slot):
    d = device
    m = mode
    key = f"{d} disable pipe {slot}"
    c = el.checkbox({
        "type" : "checkbox",
        "text" : f"disable internal pipe",
        "default" : se.get_settings().get(key, False),
        "func" : lambda: se.update_setting(key, c.findChildren(QCheckBox)[0].isChecked())
    })
    return c

def pos_mode():
    return _disable_pipe_checkbox("pos")

def rot_mode():
    return _disable_pipe_checkbox("rot")

def both_mode():
    return el.label({"text": " "})

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        time.sleep(0.01)