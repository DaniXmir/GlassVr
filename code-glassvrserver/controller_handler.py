#input handler for sdl controller/keyboard/mouse
#while it be better to make an equivalent file for the driver, this one has a better integration with the ui

#TODO: improve gyro handling

#usage:
#import controller_handler as sdl

#get value from a button
#sdl.eval_binding(se.get(f"{prefix}_trigger", ""))

#bindable() in elements can also take a callback as "func"
#this will run every time the button is pressed
#{"func" : lambda: print("hellow ;P")}

#poll right trigger in a thread:
# def input_test():
#     while True:
#         settings = se.get_settings()
#         print(sdl.eval_binding(settings["cr_trigger"]))
#         time.sleep(0.01)

# def start_input_test():
#     thread = threading.Thread(target=input_test, daemon=True)
#     thread.start()

#see example plugin

import ctypes
import math
import threading
import time
from typing import Dict, Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

import sdl3 as SDL
from sdl3 import *

import settings as se

USER32 = getattr(ctypes, 'windll', None).user32 if hasattr(ctypes, 'windll') else None

def is_key_pressed_globally(vk_code: int) -> bool:
    if USER32:
        return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)
    return False

def get_vk_code(bind_str: str) -> Optional[int]:
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
                scan = ctypes.windll.user32.MapVirtualKeyA(vk, 0)
                if scan == 0:
                    continue
                lparam = scan << 16
                if vk in (0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                          0x2D, 0x2E, 0x5B, 0x5C, 0x5D, 0x2C, 0x13):
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

_last_mouse_pos    = None
mouse_captured     = False
_capture_lock_pos  = None
_capture_thread    = None
_capture_stop_flag = None
_accum_lock        = threading.Lock()
_accum_dx          = 0.0
_accum_dy          = 0.0

_CAPTURE_POLL_HZ = 250

_MONITOR_DEFAULTTONEAREST = 2


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _RECT),
                ("rcWork", _RECT), ("dwFlags", ctypes.c_ulong)]

if hasattr(ctypes, 'windll'):
    ctypes.windll.user32.MonitorFromPoint.restype = ctypes.c_void_p
    ctypes.windll.user32.MonitorFromPoint.argtypes = [_POINT, ctypes.c_ulong]
    ctypes.windll.user32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MONITORINFO)]


def _get_cursor_pos():
    pt = _POINT()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
        return None
    return (pt.x, pt.y)


def _get_monitor_center(point):
    if point is not None:
        hmonitor = ctypes.windll.user32.MonitorFromPoint(
            _POINT(point[0], point[1]), _MONITOR_DEFAULTTONEAREST
        )
        if hmonitor:
            info = _MONITORINFO()
            info.cbSize = ctypes.sizeof(_MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                r = info.rcMonitor
                return ((r.left + r.right) // 2, (r.top + r.bottom) // 2)

    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    return (screen_w // 2, screen_h // 2)


def _capture_loop(lock_pos, stop_flag):
    global _accum_dx, _accum_dy

    last_pos = lock_pos
    interval = 1.0 / _CAPTURE_POLL_HZ

    while not stop_flag.is_set():
        pos = _get_cursor_pos()
        if pos is not None and pos != lock_pos:
            dx = float(pos[0] - last_pos[0])
            dy = float(pos[1] - last_pos[1])
            with _accum_lock:
                _accum_dx += dx
                _accum_dy += dy
            ctypes.windll.user32.SetCursorPos(*lock_pos)
        last_pos = lock_pos
        time.sleep(interval)


def set_mouse_capture(enabled):
    global mouse_captured, _capture_lock_pos, _last_mouse_pos
    global _capture_thread, _capture_stop_flag, _accum_dx, _accum_dy

    enabled = bool(enabled)
    if enabled == mouse_captured:
        return

    mouse_captured = enabled

    if enabled:
        click_pos = _get_cursor_pos()
        center = _get_monitor_center(click_pos)

        ctypes.windll.user32.SetCursorPos(*center)
        _capture_lock_pos = center
        _last_mouse_pos   = center
        with _accum_lock:
            _accum_dx = 0.0
            _accum_dy = 0.0

        ctypes.windll.user32.ShowCursor(False)

        _capture_stop_flag = threading.Event()
        _capture_thread = threading.Thread(
            target=_capture_loop, args=(center, _capture_stop_flag), daemon=True
        )
        _capture_thread.start()
    else:
        if _capture_stop_flag is not None:
            _capture_stop_flag.set()
        if _capture_thread is not None:
            _capture_thread.join(timeout=1.0)
        _capture_thread = None
        _capture_stop_flag = None

        ctypes.windll.user32.ShowCursor(True)
        _capture_lock_pos = None


def get_mouse_delta():
    global _last_mouse_pos, _accum_dx, _accum_dy

    if mouse_captured:
        with _accum_lock:
            dx, dy = _accum_dx, _accum_dy
            _accum_dx = 0.0
            _accum_dy = 0.0
        return dx, dy

    current_pos = _get_cursor_pos()
    if current_pos is None:
        return 0.0, 0.0

    if _last_mouse_pos is None:
        _last_mouse_pos = current_pos
        return 0.0, 0.0

    dx = float(current_pos[0] - _last_mouse_pos[0])
    dy = float(current_pos[1] - _last_mouse_pos[1])
    _last_mouse_pos = current_pos

    return dx, dy

current_binding_btn = None

class _Signals(QObject):
    controller_connected = pyqtSignal()
    binding_captured     = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.binding_captured.connect(self._on_binding_captured)

    def _on_binding_captured(self, input_name):
        if current_binding_btn is not None:
            current_binding_btn.finish_binding(input_name)


signals = _Signals()

class ControllerManager:
    CALIBRATION_SAMPLES = 200
    DEFAULT_THRESHOLD = 0.02
    DEADZONE = 0.1

    IDLE_TIMEOUT = 10.0
    IDLE_MOVEMENT_ABORT_MULTIPLIER = 3.0
    STICK_ACTIVITY_EPSILON = 1e-4

    # se.get_settings() hits disk (open + json.load) on every call. The
    # hardware poller runs at ~1kHz and the gyro handler fires at the
    # sensor's native rate, so calling it unthrottled from either was
    # adding real input latency. Settings (deadzone, sensitivity,
    # calibration, etc.) don't need sub-100ms freshness, so both read
    # through this cache instead of hitting disk every tick.
    SETTINGS_CACHE_TTL = 0.1

    def __init__(self):
        self.controllers_dict: Dict[str, Dict[str, Any]] = {}
        self.controllers_lock = threading.Lock()
        self.sdl_id_map: Dict[int, str] = {}

        self.running = False
        self._event_thread = None
        self._poller_thread = None

        self._settings_cache = None
        self._settings_cache_ts = 0.0

    def _get_cached_settings(self):
        now = time.time()
        if self._settings_cache is None or (now - self._settings_cache_ts) >= self.SETTINGS_CACHE_TTL:
            self._settings_cache = se.get_settings()
            self._settings_cache_ts = now
        return self._settings_cache

    def get_default_state(self, device_type="unknown", handle=None, unique_id="") -> Dict[str, Any]:
        return {
            "id": unique_id,
            "type": device_type,
            "handle": handle,
            "joystick_handle": None,
            "gamepad_handle": None,
            "active": True,
            "gyro_quat": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            "last_good_quat": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            "last_ts": 0,
            "last_activity_ts": time.time(),
            "gyro_bias": {
                "wx": 0.0, "wy": 0.0, "wz": 0.0,
                "ax": 0.0, "ay": 0.0, "az": 0.0,
                "tx": self.DEFAULT_THRESHOLD, "ty": self.DEFAULT_THRESHOLD, "tz": self.DEFAULT_THRESHOLD,
                "samples": 0,
                "loaded": False,
                "calibrating": False
            }
        }

    def get_controller(self, c_id):
        with self.controllers_lock:
            return self.controllers_dict.get(c_id, self.get_default_state())

    def get_gyro(self, c_id):
        with self.controllers_lock:
            ctrl = self.controllers_dict.get(c_id)
            if ctrl is None:
                return {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            return ctrl["gyro_quat"].copy()

    def get_all_controllers(self):
        with self.controllers_lock:
            return list(self.controllers_dict.values())

    def reset_gyro(self, target_id=None):
        target_quat = {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
        with self.controllers_lock:
            for c_id, ctrl in self.controllers_dict.items():
                if target_id is None or c_id == target_id:
                    if "gyro_quat" in ctrl:
                        ctrl["gyro_quat"] = target_quat.copy()
                        ctrl["last_good_quat"] = target_quat.copy()

    def get_deadzone(self, c_id, ctrl=None, axis="x"):
        """Per-axis, per-controller deadzone ('x' or 'y'), looked up the same
        way as gyro config (hardware unique id first, falling back to c_id),
        with a global 'default deadzone x'/'default deadzone y' setting as
        fallback, then the class constant."""
        if ctrl is None:
            with self.controllers_lock:
                ctrl = self.controllers_dict.get(c_id, {})

        unique_id = ctrl.get("id", c_id)
        settings_dict = self._get_cached_settings()
        c_conf = settings_dict.get(unique_id, settings_dict.get(c_id, {}))

        default_dz = settings_dict.get(f"default deadzone {axis}", self.DEADZONE)
        return float(c_conf.get(f"deadzone_{axis}", default_dz))

    @staticmethod
    def apply_deadzone(value: float, deadzone: float) -> float:
        deadzone = max(0.0, min(0.95, deadzone))
        if abs(value) < deadzone:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - deadzone) / (1.0 - deadzone)

    def start_calibration(self, target_id=None):
        with self.controllers_lock:
            for c_id, ctrl in self.controllers_dict.items():
                if target_id is None or c_id == target_id:
                    if "gyro_bias" in ctrl:
                        ctrl["gyro_bias"] = {
                            "wx": 0.0, "wy": 0.0, "wz": 0.0,
                            "ax": 0.0, "ay": 0.0, "az": 0.0,
                            "tx": self.DEFAULT_THRESHOLD, "ty": self.DEFAULT_THRESHOLD, "tz": self.DEFAULT_THRESHOLD,
                            "samples": 0,
                            "loaded": False,
                            "calibrating": True,
                        }

    def _discard_calibration(self, c_id: str, target: dict, c_conf: dict):
        bias = target["gyro_bias"]
        saved = c_conf.get("calibration")

        bias["calibrating"] = False
        bias["samples"] = 0
        bias["wx"] = saved.get("wx", 0.0) if saved else 0.0
        bias["wy"] = saved.get("wy", 0.0) if saved else 0.0
        bias["wz"] = saved.get("wz", 0.0) if saved else 0.0
        bias["loaded"] = True

    def _maybe_start_idle_calibration(self, c_id: str, ctrl: dict, now: float):
        bias = ctrl.get("gyro_bias")
        if not bias or bias.get("calibrating"):
            return

        if not ctrl.get("gamepad_handle"):
            return

        last_activity = ctrl.get("last_activity_ts", now)
        if now - last_activity >= self.IDLE_TIMEOUT:
            self.start_calibration(c_id)

    def start(self):
        if self.running:
            return

        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_WII", b"1")
        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_COMBINE_JOY_CONS", b"0")
        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4", b"1")
        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS5", b"1")
        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4_RUMBLE", b"1")
        SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_XBOX_ELITE", b"1")
        SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")

        SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMEPAD)

        self.running = True
        self._event_thread = threading.Thread(target=self._run_sdl_event_loop, daemon=True, name="SDL_Event_Thread")
        self._poller_thread = threading.Thread(target=self._run_hardware_poller, daemon=True, name="SDL_Hardware_Poller")

        self._event_thread.start()
        self._poller_thread.start()

    def stop(self):
        self.running = False
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=1.0)
        if self._poller_thread and self._poller_thread.is_alive():
            self._poller_thread.join(timeout=1.0)

    def process_sdl_gyro(self, c_id: str, raw_data: list, timestamp_ns: int):
        with self.controllers_lock:
            target = self.controllers_dict.get(c_id)
            if not target:
                return

        unique_id = target.get("id", c_id)
        settings_dict = self._get_cached_settings()

        c_conf = settings_dict.get(unique_id, settings_dict.get(c_id, {}))

        idx_x = int(c_conf.get("index_x", 0))
        idx_y = int(c_conf.get("index_y", 1))
        idx_z = int(c_conf.get("index_z", 2))
        sens = float(c_conf.get("sensitivity", 1.0))

        rx = raw_data[idx_x] * (-1.0 if c_conf.get("invert_x") else 1.0)
        ry = raw_data[idx_y] * (-1.0 if c_conf.get("invert_y") else 1.0)
        rz = raw_data[idx_z] * (-1.0 if c_conf.get("invert_z") else 1.0)

        bias = target["gyro_bias"]

        if not bias.get("loaded") and not bias.get("calibrating"):
            saved = c_conf.get("calibration")
            if saved:
                bias["wx"] = saved.get("wx", 0.0)
                bias["wy"] = saved.get("wy", 0.0)
                bias["wz"] = saved.get("wz", 0.0)
            bias["loaded"] = True

        if bias.get("calibrating"):
            n = bias["samples"]

            if n > 0:
                dev_x = rx - bias["wx"]
                dev_y = ry - bias["wy"]
                dev_z = rz - bias["wz"]
                abort_tx = bias["tx"] * self.IDLE_MOVEMENT_ABORT_MULTIPLIER
                abort_ty = bias["ty"] * self.IDLE_MOVEMENT_ABORT_MULTIPLIER
                abort_tz = bias["tz"] * self.IDLE_MOVEMENT_ABORT_MULTIPLIER
                if abs(dev_x) > abort_tx or abs(dev_y) > abort_ty or abs(dev_z) > abort_tz:
                    self._discard_calibration(c_id, target, c_conf)
                    target["last_activity_ts"] = time.time()
                    return

            bias["wx"] = (bias["wx"] * n + rx) / (n + 1)
            bias["wy"] = (bias["wy"] * n + ry) / (n + 1)
            bias["wz"] = (bias["wz"] * n + rz) / (n + 1)
            bias["samples"] += 1

            if bias["samples"] >= self.CALIBRATION_SAMPLES:
                bias["calibrating"] = False
                bias["loaded"] = True
                se.update_nested(c_id, {
                    "calibration": {"wx": bias["wx"], "wy": bias["wy"], "wz": bias["wz"]}
                })
                target["last_activity_ts"] = time.time()
            return

        dev_x = rx - bias["wx"]
        dev_y = ry - bias["wy"]
        dev_z = rz - bias["wz"]

        if abs(dev_x) > bias["tx"] or abs(dev_y) > bias["ty"] or abs(dev_z) > bias["tz"]:
            target["last_activity_ts"] = time.time()

        vx = dev_x * sens
        vy = dev_y * sens
        vz = dev_z * sens

        if target.get("last_ts", 0) == 0:
            target["last_ts"] = timestamp_ns
            return

        dt = (timestamp_ns - target["last_ts"]) / 1_000_000_000.0
        target["last_ts"] = timestamp_ns

        q = target["gyro_quat"]
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

    def _run_sdl_event_loop(self):
        while self.running:
            event = SDL.SDL_Event()
            while SDL.SDL_PollEvent(ctypes.byref(event)):

                # Controller Connection
                if event.type == SDL_EVENT_JOYSTICK_ADDED:
                    device_index = event.jdevice.which
                    joy_handle = SDL.SDL_OpenJoystick(device_index)

                    if joy_handle:
                        instance_id = SDL.SDL_GetJoystickID(joy_handle)
                        name = SDL.SDL_GetJoystickName(joy_handle).decode("utf-8", "replace")
                        guid = SDL.SDL_GetJoystickGUID(joy_handle)
                        guid_str = "".join([f"{guid.data[i]:02x}" for i in range(16)])
                        serial = SDL.SDL_GetJoystickSerial(joy_handle)
                        unique_id = serial.decode("utf-8") if serial else guid_str

                        gamepad_handle = SDL.SDL_OpenGamepad(device_index)
                        gamepad_instance_id = None
                        if gamepad_handle:
                            SDL.SDL_SetGamepadSensorEnabled(gamepad_handle, SDL.SDL_SENSOR_GYRO, True)
                            SDL.SDL_SetGamepadSensorEnabled(gamepad_handle, SDL.SDL_SENSOR_ACCEL, True)
                            gamepad_instance_id = SDL.SDL_GetGamepadID(gamepad_handle)

                        with self.controllers_lock:
                            if unique_id in self.controllers_dict:
                                self.controllers_dict[unique_id]["joystick_handle"] = joy_handle
                                self.controllers_dict[unique_id]["gamepad_handle"] = gamepad_handle
                                self.controllers_dict[unique_id]["active"] = True
                                self.controllers_dict[unique_id]["last_ts"] = 0
                            else:
                                state = self.get_default_state(name, joy_handle, unique_id)
                                state["joystick_handle"] = joy_handle
                                state["gamepad_handle"] = gamepad_handle
                                self.controllers_dict[unique_id] = state

                        self.sdl_id_map[instance_id] = unique_id
                        if gamepad_instance_id is not None:
                            self.sdl_id_map[gamepad_instance_id] = unique_id

                        signals.controller_connected.emit()

                # Gyro Sensor Updates
                elif event.type == SDL_EVENT_GAMEPAD_SENSOR_UPDATE:
                    c_id = self.sdl_id_map.get(event.gsensor.which)
                    if c_id and event.gsensor.sensor == SDL.SDL_SENSOR_GYRO:
                        self.process_sdl_gyro(c_id, list(event.gsensor.data), event.gsensor.sensor_timestamp)

                # Controller Disconnection
                elif event.type == SDL_EVENT_JOYSTICK_REMOVED:
                    instance_id = event.jdevice.which
                    c_id = self.sdl_id_map.get(instance_id)
                    if c_id:
                        with self.controllers_lock:
                            ctrl = self.controllers_dict.get(c_id, {})
                            if ctrl.get("gamepad_handle"):
                                SDL.SDL_CloseGamepad(ctrl["gamepad_handle"])
                            ctrl["joystick_handle"] = None
                            ctrl["gamepad_handle"] = None
                            ctrl["active"] = False

                        keys_to_remove = [k for k, v in self.sdl_id_map.items() if v == c_id]
                        for k in keys_to_remove:
                            del self.sdl_id_map[k]

                # Button Motion
                elif event.type in [SDL_EVENT_JOYSTICK_BUTTON_DOWN, SDL_EVENT_JOYSTICK_BUTTON_UP]:
                    c_id = self.sdl_id_map.get(event.jbutton.which)
                    if c_id:
                        key = f"btn_{event.jbutton.button}"
                        is_down = bool(event.jbutton.down)
                        with self.controllers_lock:
                            ctrl = self.controllers_dict.setdefault(c_id, {})
                            old_state = ctrl.copy()
                            ctrl[key] = is_down
                            if is_down:
                                ctrl["last_activity_ts"] = time.time()
                        self.detect_input_change(c_id, {key: is_down}, old_state)

                # Axis Motion
                elif event.type == SDL_EVENT_JOYSTICK_AXIS_MOTION:
                    c_id = self.sdl_id_map.get(event.jaxis.which)
                    if c_id:
                        key = f"axis_{event.jaxis.axis}"
                        raw_val = event.jaxis.value / 32767.0
                        # SDL's raw joystick axis order is conventionally
                        # X, Y, X2, Y2, ... - even indices are X-like, odd are Y-like.
                        axis_kind = "y" if (event.jaxis.axis % 2) else "x"
                        with self.controllers_lock:
                            ctrl = self.controllers_dict.setdefault(c_id, {})
                            old_val = ctrl.get(key, 0.0)
                            deadzone = self.get_deadzone(c_id, ctrl, axis=axis_kind)
                            val = self.apply_deadzone(raw_val, deadzone)
                            ctrl[key] = val
                            if abs(val) > self.STICK_ACTIVITY_EPSILON:
                                ctrl["last_activity_ts"] = time.time()
                        self.detect_input_change(c_id, {key: val}, {key: old_val})

                # Hat Motion
                elif event.type == SDL_EVENT_JOYSTICK_HAT_MOTION:
                    c_id = self.sdl_id_map.get(event.jhat.which)
                    if c_id:
                        key = f"hat_{event.jhat.hat}"
                        val = event.jhat.value
                        with self.controllers_lock:
                            ctrl = self.controllers_dict.setdefault(c_id, {})
                            old_val = ctrl.get(key, 0)
                            ctrl[key] = val
                            if val != 0:
                                ctrl["last_activity_ts"] = time.time()
                        self.detect_input_change(c_id, {key: val}, {key: old_val})

            time.sleep(0.001)

    def _run_hardware_poller(self):
        while self.running:
            try:
                with self.controllers_lock:
                    items = list(self.controllers_dict.items())

                now = time.time()

                for c_id, ctrl in items:
                    gamepad = ctrl.get("gamepad_handle")
                    if gamepad:
                        deadzone_x = self.get_deadzone(c_id, ctrl, axis="x")
                        deadzone_y = self.get_deadzone(c_id, ctrl, axis="y")
                        new_data = self._poll_gamepad(gamepad, deadzone_x, deadzone_y)

                        moved = any(v is True for v in new_data.values()) or any(
                            isinstance(v, float) and abs(v) > self.STICK_ACTIVITY_EPSILON
                            for v in new_data.values()
                        )

                        self.detect_input_change(c_id, new_data, ctrl)
                        with self.controllers_lock:
                            ctrl.update(new_data)
                            if moved:
                                ctrl["last_activity_ts"] = now

                        self._maybe_start_idle_calibration(c_id, ctrl, now)
            except Exception:
                pass
            time.sleep(0.001)

    def _poll_gamepad(self, gamepad_handle, deadzone_x: Optional[float] = None,
                       deadzone_y: Optional[float] = None) -> Dict[str, float]:
        if deadzone_x is None:
            deadzone_x = self.DEADZONE
        if deadzone_y is None:
            deadzone_y = self.DEADZONE

        def axis(a, deadzone):
            v = SDL.SDL_GetGamepadAxis(gamepad_handle, a) / 32767.0
            return self.apply_deadzone(v, deadzone)

        def btn(b):
            return bool(SDL.SDL_GetGamepadButton(gamepad_handle, b))

        return {
            "a": btn(SDL.SDL_GAMEPAD_BUTTON_SOUTH),
            "b": btn(SDL.SDL_GAMEPAD_BUTTON_EAST),
            "x": btn(SDL.SDL_GAMEPAD_BUTTON_WEST),
            "y": btn(SDL.SDL_GAMEPAD_BUTTON_NORTH),
            "back": btn(SDL.SDL_GAMEPAD_BUTTON_BACK),
            "start": btn(SDL.SDL_GAMEPAD_BUTTON_START),
            "guide": btn(SDL.SDL_GAMEPAD_BUTTON_GUIDE),
            "dpup": btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_UP),
            "dpdown": btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_DOWN),
            "dpleft": btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_LEFT),
            "dpright": btn(SDL.SDL_GAMEPAD_BUTTON_DPAD_RIGHT),
            "leftshoulder": btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_SHOULDER),
            "rightshoulder": btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER),
            "leftstick": btn(SDL.SDL_GAMEPAD_BUTTON_LEFT_STICK),
            "rightstick": btn(SDL.SDL_GAMEPAD_BUTTON_RIGHT_STICK),
            "leftx": axis(SDL.SDL_GAMEPAD_AXIS_LEFTX, deadzone_x),
            "lefty": axis(SDL.SDL_GAMEPAD_AXIS_LEFTY, deadzone_y),
            "rightx": axis(SDL.SDL_GAMEPAD_AXIS_RIGHTX, deadzone_x),
            "righty": axis(SDL.SDL_GAMEPAD_AXIS_RIGHTY, deadzone_y),
            "lefttrigger": axis(SDL.SDL_GAMEPAD_AXIS_LEFT_TRIGGER, deadzone_x),
            "righttrigger": axis(SDL.SDL_GAMEPAD_AXIS_RIGHT_TRIGGER, deadzone_x),
        }

    def detect_input_change(self, c_id: str, new_data: dict, old_state: dict):
        if current_binding_btn is None:
            return

        for key, value in new_data.items():
            if key.startswith("btn_") and value is True:
                signals.binding_captured.emit(f"SDL_{c_id}_{key}")
                return
            if key.startswith("hat_") and value != 0:
                signals.binding_captured.emit(f"SDL_{c_id}_{key}_{value}")
                return
            if key.startswith("axis_") and abs(value) > 0.7:
                direction = "1.0" if value > 0 else "-1.0"
                signals.binding_captured.emit(f"SDL_{c_id}_{key}_{direction}")
                return

    def eval_binding(self, bind_data: Any) -> float:
        if isinstance(bind_data, dict):
            buttons = bind_data.get("buttons", [])
            invert = bind_data.get("invert", False)

            max_val = 0.0
            for btn_string in buttons:
                val = self.eval_binding(btn_string)
                if val > max_val:
                    max_val = val

            return 1.0 - max_val if invert else max_val

        if not bind_data or bind_data == "[Unbound]":
            return 0.0

        if bind_data.startswith("Key_") or bind_data.startswith("Mouse_"):
            vk = get_vk_code(bind_data)
            return 1.0 if (vk and is_key_pressed_globally(vk)) else 0.0

        parts = bind_data.split("_", 2)
        if parts[0] == "SDL" and len(parts) == 3:
            try:
                c_id = parts[1]
                remainder = parts[2]

                with self.controllers_lock:
                    c_dict = self.controllers_dict.get(c_id)

                if c_dict is None:
                    return 0.0

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
                return 1.0 if (val is True or val > 0.5) else 0.0
            except Exception:
                return 0.0

        return 0.0

input_manager = ControllerManager()
input_manager.start()

def eval_binding(bind_data):
    return input_manager.eval_binding(bind_data)

def get_controller(c_id):
    return input_manager.get_controller(c_id)

def get_gyro(c_id):
    return input_manager.get_gyro(c_id)

def get_all_controllers():
    return input_manager.get_all_controllers()

def get_deadzone_x(c_id):
    return input_manager.get_deadzone(c_id, axis="x")

def get_deadzone_y(c_id):
    return input_manager.get_deadzone(c_id, axis="y")

def reset_gyro(target_id=None):
    return input_manager.reset_gyro(target_id)

def start_calibration(target_id=None):
    return input_manager.start_calibration(target_id)