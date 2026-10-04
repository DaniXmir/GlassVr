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

title = "UDP"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 0.0

def pos_mode():
    return el.label({"text": f" "})

def rot_mode():
    return el.label({"text": f" "})

def both_mode():
    current_device = device #sometimes buggy, plz save device as local var
 
    settings = se.get_settings()
    s = el.spinbox({
        "text"   : "port",
        "min"    : 0,
        "max"    : 999999999,
        "default": settings.get(f"{current_device} port", 9000),
        "steps"  : 1,
        "func"   : lambda: se.update_setting(f"{current_device} port", s.findChildren(QSpinBox)[0].value())
    })
    return s

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        time.sleep(0.01)