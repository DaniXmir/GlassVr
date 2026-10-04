#takes gyro data from sdl and sends it

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
import controller_handler as sdl

# pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

# input_devices = ["controller"]
# skeletal_devices = ["controller"]

title = "gyro"

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
    current_device = device
    c = el.combobox({
        "type" : "combobox",
        "text": "gyro id",
        "default": se.get_settings().get("hmd gyro id", ""),
        "items": list({str(se.get_settings().get(f"{current_device} gyro id", "")), *sdl.input_manager.controllers_dict}) if se.get_settings().get(f"{current_device} gyro id") else list(sdl.input_manager.controllers_dict),
        "index change": lambda: se.update_setting(f"{current_device} gyro id", c.findChild(QComboBox).currentText()),
        "pre show": lambda cb: (
            saved := str(se.get_settings().get(f"{current_device} gyro id", "")),
            val := cb.currentText(), 
            cb.clear(), 
            cb.addItems(list({saved, *sdl.input_manager.controllers_dict}) if saved else list(sdl.input_manager.controllers_dict)), 
            cb.setCurrentText(val), 
            None
        )[-1]
    })
    
    return c

def loop(data):
    global px, py, pz, rx, ry, rz, rw, device

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        target_gyro_id = se.get_settings().get(f"{device} gyro id", None)

        if target_gyro_id:
            with sdl.input_manager.controllers_lock:
                controller = next(
                    (ctrl for ctrl in sdl.input_manager.controllers_dict.values() 
                     if isinstance(ctrl, dict) and ctrl.get("id") == target_gyro_id), 
                    None
                )

            if controller and "gyro_quat" in controller:
                quat = controller.get("gyro_quat")
                
                if quat is not None:
                    try:
                        rx, ry, rz, rw = quat.x, quat.y, quat.z, quat.w
                    except AttributeError:
                        if isinstance(quat, (tuple, list)) and len(quat) == 4:
                            rx, ry, rz, rw = quat[0], quat[1], quat[2], quat[3]
                        elif isinstance(quat, dict):
                            rx = quat.get("x", 0.0)
                            ry = quat.get("y", 0.0)
                            rz = quat.get("z", 0.0)
                            rw = quat.get("w", 1.0)
        
        time.sleep(0.01)