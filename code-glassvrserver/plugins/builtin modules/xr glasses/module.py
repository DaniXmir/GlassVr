#zombie module! unlike ghost module that dont do anything,
#this one doesnt send data but can send a recenter command to the driver via \\.\pipe\GlassVR_HMD_Extra
#for now the extra pipe only does recenters for xr glasses and udp, will be change later

import struct
import threading
import time
import webbrowser
from PyQt6.QtWidgets import QCheckBox, QVBoxLayout, QWidget
import pywintypes
import win32file
import win32pipe

import elements as el
import settings as se
import controller_handler as sdl

pos_devices = ["hmd"]
rot_devices = ["hmd"]

title = "xr glasses"

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
    return el.label({"text": " "})

def rot_mode():
    c = el.checkbox({
        "text": "3dof only",
        "default": se.get_settings().get("xr 3dof", True),
        "func": lambda: se.update_setting(
            "xr 3dof", c.findChildren(QCheckBox)[0].isChecked()
        ),
    })
    return c

def both_mode():
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    s = el.bindable({
        "prefix": "hmd",
        "mapping": "reset xr",
    })
    group_layout.addWidget(s)

    b = el.button({
        "type": "button",
        "enabled": True,
        "text": "(only viture xr glasses are supported) calibrate on viture site",
        "func": lambda: webbrowser.open("https://www.viture.com/firmware/calibration"),
    })
    group_layout.addWidget(b)

    return group_widget

def _create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None,
    )

def pipe_reset_loop(stop_event):
    pipe_name = r"\\.\pipe\GlassVR_HMD_Extra"
    pipe_handle = None

    while not stop_event.is_set():
        try:
            if pipe_handle is None:
                try:
                    pipe_handle = _create_pipe(pipe_name)
                    win32pipe.ConnectNamedPipe(pipe_handle, None)
                except Exception:
                    time.sleep(0.5)
                    continue

            settings = se.get_settings()
            is_pressed = bool(sdl.eval_binding(settings.get("hmd_reset xr")))

            data = struct.pack("?", is_pressed)

            try:
                win32file.WriteFile(pipe_handle, data)
            except pywintypes.error as e:
                if e.winerror in (109, 232):
                    win32pipe.DisconnectNamedPipe(pipe_handle)
                    win32file.CloseHandle(pipe_handle)
                    pipe_handle = None

            time.sleep(0.01)

        except Exception:
            time.sleep(0.01)

    if pipe_handle is not None:
        try:
            win32pipe.DisconnectNamedPipe(pipe_handle)
        except Exception:
            pass
        try:
            win32file.CloseHandle(pipe_handle)
        except Exception:
            pass

def loop(data):
    global px, py, pz, rx, ry, rz, rw

    device = data.get("device")
    mode = data.get("mode")
    stop_event = data.get("stop_event")

    if device is None:
        return

    pipe_thread = threading.Thread(
        target=pipe_reset_loop, args=(stop_event,), daemon=True
    )
    pipe_thread.start()

    while not stop_event.is_set():
        time.sleep(0.01)