#ghost module
from PyQt6.QtWidgets import QWidget, QComboBox
import time

import elements as el
import controller_handler as sdl
import settings as se
import steamvr as svr

pos_devices = ["hmd", "controller", "tracker"]
rot_devices = ["hmd", "controller", "tracker"]

title = "copy"

device = None
mode = None

px = 0.0
py = 0.0
pz = 0.0

rx = 0.0
ry = 0.0
rz = 0.0
rw = 0.0

#this combo box "pre show" populates with every devies's serial steamvr finds when clicked
def pos_mode():
    combo_extra = el.combobox({
        "text": "Copy Serial",
        "default": se.get_settings().get(f"{device}pos copy serial", ""),
        "items": list(set([se.get_settings().get(f"{device}pos copy serial", "")] + list(svr.get_trackers_dict()))),
        "index change": lambda: se.update_setting(f"{device}pos copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
        "pre show": lambda cb: (
            saved := se.get_settings().get(f"{device}pos copy serial", ""),
            val := cb.currentText(), 
            cb.clear(), 
            cb.addItems(list({saved, *svr.get_trackers_dict()}) if saved else list(svr.get_trackers_dict())), 
            cb.setCurrentText(val), 
            None
        )[-1]
    })
    
    return combo_extra

#same
def rot_mode():
    combo_extra = el.combobox({
        "text": "Copy Serial",
        "default": se.get_settings().get(f"{device}rot copy serial", ""),
        "items": list(set([se.get_settings().get(f"{device}rot copy serial", "")] + list(svr.get_trackers_dict()))),
        "index change": lambda: se.update_setting(f"{device}rot copy serial", combo_extra.findChildren(QComboBox)[0].currentText()),
        "pre show": lambda cb: (
            saved := se.get_settings().get(f"{device}rot copy serial", ""),
            val := cb.currentText(), 
            cb.clear(), 
            cb.addItems(list({saved, *svr.get_trackers_dict()}) if saved else list(svr.get_trackers_dict())), 
            cb.setCurrentText(val), 
            None
        )[-1]
    })
    
    return combo_extra

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    while not stop_event.is_set():
        time.sleep(0.01)