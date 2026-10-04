#this file sends the data to the driver via named pipes, 
#each module has its own pipe for each devices, so like if pos = wasd and rot = gyro these are 2 pipes for that device
#these pipes can be disabled via (f"{device} disable pipe {slot}", False) and setting mode to "app (named pipe)", this allows the ui to be kept open with external pipes

#controllers also have 2 additional pipes for input and skeletal

import time
import struct
import threading
import copy
import win32pipe
import win32file
import pywintypes

import settings as settings_core
import mode_registry
import mode_manager
import controller_handler as sdl

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')
INPUT_PACKER = struct.Struct('<12?8d')
SKELETAL_PACKER = struct.Struct('<25d')

PIPE_HMD_POS = r'\\.\pipe\GlassVR_HMD_Pos'
PIPE_HMD_ROT = r'\\.\pipe\GlassVR_HMD_Rot'
PIPE_CONTROLLER_BASE = r'\\.\pipe\GlassVR_CONTROLLER_{side}_{type}'

#TODO: update to support oculus and sf
DEFAULT_INPUT = {
    "a": False, "b": False, "system": False,
    "joy_btn": False, "trigger_btn": False,
    "a_cap": False, "b_cap": False, "system_cap": False,
    "joy_cap": False, "trigger_cap": False,
    "touch_cap": False, "grip_cap": False,
    "joy_x": 0.0, "joy_y": 0.0,
    "touch_x": 0.0, "touch_y": 0.0,
    "trigger": 0.0, "touch_force": 0.0,
    "grip_pull": 0.0, "grip_force": 0.0,
}

DEFAULT_SKELETAL = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
}

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_NOWAIT,
        1, 1024, 1024, 0, None
    )

def _find_transform_entry(module, device):
    if module is None or not hasattr(module, "transforms"):
        return None

    transforms = module.transforms
    if isinstance(transforms, dict):
        return transforms.get(device)
    elif isinstance(transforms, list):
        for entry in transforms:
            if isinstance(entry, dict) and entry.get("type") == device:
                return entry
    return None

def _get_slot_module(device, slot):
    se = settings_core.get_settings()
    title = _get_mode_setting(se, device, slot)
    
    if not title:
        return None
        
    return mode_manager.get_active_module(device, slot) or mode_registry.get_mode(title)

def get_transform(device):
    pos_module = _get_slot_module(device, "pos")
    rot_module = _get_slot_module(device, "rot")

    px = py = pz = 0.0
    rx = ry = rz = 0.0
    rw = 1.0

    if pos_module is not None:
        pos_entry = _find_transform_entry(pos_module, device)
        if pos_entry is not None:
            px = pos_entry.get("px", 0.0)
            py = pos_entry.get("py", 0.0)
            pz = pos_entry.get("pz", 0.0)
        else:
            px = getattr(pos_module, "px", 0.0)
            py = getattr(pos_module, "py", 0.0)
            pz = getattr(pos_module, "pz", 0.0)

    if rot_module is not None:
        rot_entry = _find_transform_entry(rot_module, device)
        if rot_entry is not None:
            rx = rot_entry.get("rx", 0.0)
            ry = rot_entry.get("ry", 0.0)
            rz = rot_entry.get("rz", 0.0)
            rw = rot_entry.get("rw", 1.0)
        else:
            rx = getattr(rot_module, "rx", 0.0)
            ry = getattr(rot_module, "ry", 0.0)
            rz = getattr(rot_module, "rz", 0.0)
            rw = getattr(rot_module, "rw", 1.0)

    return (px, py, pz), (rw, rx, ry, rz)

def get_module_input(device):
    module = _get_slot_module(device, "input")
    if module is None:
        return copy.deepcopy(DEFAULT_INPUT)

    entry = _find_transform_entry(module, device)
    if entry is not None and "input" in entry and isinstance(entry["input"], dict):
        res = copy.deepcopy(DEFAULT_INPUT)
        res.update(entry["input"])
        return res

    mod_input = getattr(module, "input", None)
    if isinstance(mod_input, dict):
        res = copy.deepcopy(DEFAULT_INPUT)
        res.update(mod_input)
        return res

    return copy.deepcopy(DEFAULT_INPUT)

def get_module_skeletal(device):
    module = _get_slot_module(device, "skeletal")
    if module is None:
        return copy.deepcopy(DEFAULT_SKELETAL)

    entry = _find_transform_entry(module, device)
    if entry is not None and "skeletal" in entry and isinstance(entry["skeletal"], dict):
        res = copy.deepcopy(DEFAULT_SKELETAL)
        res.update(entry["skeletal"])
        return res

    mod_skeletal = getattr(module, "skeletal", None)
    if isinstance(mod_skeletal, dict):
        res = copy.deepcopy(DEFAULT_SKELETAL)
        res.update(mod_skeletal)
        return res

    return copy.deepcopy(DEFAULT_SKELETAL)

def is_device_enabled(device, se):
    if device == "hmd": return se.get("enable hmd", True)
    if device == "cr": return se.get("enable cr", False)
    if device == "cl": return se.get("enable cl", False)
    tracker_index = _tracker_index(device)
    if tracker_index is not None:
        return tracker_index < int(se.get("trackers num", 0))
    return False

def _tracker_device_key(tracker_id):
    return f"{tracker_id}tracker"

def _tracker_index(device):
    if device.endswith("tracker"):
        prefix = device[:-7]
        if prefix.isdigit():
            return int(prefix)
    if device.startswith("tracker") and device[7:].isdigit():
        return int(device[7:])
    return None

def _get_mode_setting(se, device, slot):
    candidates = (
        f"{device}{slot} mode",
        f"{device} {slot} mode",
        f"{device}_{slot}_mode",
    )
    for key in candidates:
        value = se.get(key)
        if value:
            return value
    return None

def _enabled_devices(se):
    enabled = set()
    if se.get("enable hmd", True):
        enabled.add("hmd")
    if se.get("enable cr", False):
        enabled.add("cr")
    if se.get("enable cl", False):
        enabled.add("cl")

    trackers_num = max(0, int(se.get("trackers num", 0)))
    for i in range(trackers_num):
        enabled.add(_tracker_device_key(i))
    return enabled

def device_scanner():
    spawned_trackers = set()

    while True:
        se = settings_core.get_settings()
        enabled_devices = _enabled_devices(se)

        trackers_num = max(0, int(se.get("trackers num", 0)))
        for i in range(trackers_num):
            if i not in spawned_trackers:
                threading.Thread(
                    target=send_tracker_data,
                    args=(i,),
                    name=f"GlassVR tracker sender {i}",
                    daemon=True,
                ).start()
                spawned_trackers.add(i)

        desired_slots = {}
        desired_modules = {}

        for dev in enabled_devices:
            for slot in ("pos", "rot", "input", "skeletal"):
                title = _get_mode_setting(se, dev, slot)
                if not title:
                    continue
                module = mode_registry.get_mode(title)
                if module is None:
                    continue
                desired_slots[(dev, slot)] = title
                desired_modules[(dev, title)] = module

        mode_manager.reconcile_with_modules(desired_slots, desired_modules)
        time.sleep(0.2)

APP_PIPE_MODE = "app (named pipe)"

def pipe_disabled(device, slot, se):
    if _get_mode_setting(se, device, slot) != APP_PIPE_MODE:
        return False
    return bool(se.get(f"{device} disable pipe {slot}", False))

def pipe_wanted(device, slot, se):
    return is_device_enabled(device, se) and not pipe_disabled(device, slot, se)

class Pipe:
    def __init__(self, name):
        self.name = name
        self.handle = None
        self.connected = False
        self.retry_at = 0.0

    def close(self, retry_delay=0.0):
        h, self.handle = self.handle, None
        self.connected = False
        self.retry_at = time.monotonic() + retry_delay
        if h:
            try:
                win32pipe.DisconnectNamedPipe(h)
            except Exception:
                pass
            try:
                win32file.CloseHandle(h)
            except Exception:
                pass

    def poll(self):
        if self.connected:
            return True
        now = time.monotonic()
        if now < self.retry_at:
            return False
        try:
            if self.handle is None:
                self.handle = create_pipe(self.name)
            try:
                win32pipe.ConnectNamedPipe(self.handle, None)
            except pywintypes.error as e:
                if e.winerror == 536:
                    self.retry_at = now + 0.05
                    return False
                if e.winerror != 535:
                    raise
            win32pipe.SetNamedPipeHandleState(self.handle, win32pipe.PIPE_WAIT, None, None)
            self.connected = True
        except pywintypes.error:
            self.close(1.0)
        return self.connected

    def write(self, buf):
        if not self.poll():
            return
        try:
            win32file.WriteFile(self.handle, buf)
        except pywintypes.error:
            self.close(1.0)

def _run_device(device, pipes, build_buffers):
    while True:
        try:
            se = settings_core.get_settings()

            wanted = set()
            for slot, pipe in pipes.items():
                if pipe_wanted(device, slot, se):
                    wanted.add(slot)
                else:
                    pipe.close()

            if not wanted:
                time.sleep(0.5)
                continue

            buffers = build_buffers(se)
            for slot in wanted:
                pipes[slot].write(buffers[slot])

            time.sleep(0.001)

        except Exception:
            for pipe in pipes.values():
                pipe.close()
            time.sleep(1)

def _pos_rot_builder(device):
    def build(se):
        (pos_x, pos_y, pos_z), (rot_w, rot_x, rot_y, rot_z) = get_transform(device)
        return {
            "pos": POS_PACKER.pack(float(pos_x), float(pos_y), float(pos_z)),
            "rot": ROT_PACKER.pack(float(rot_w), float(rot_x), float(rot_y), float(rot_z)),
        }
    return build

def send_hmd_data():
    pipes = {"pos": Pipe(PIPE_HMD_POS), "rot": Pipe(PIPE_HMD_ROT)}
    _run_device("hmd", pipes, _pos_rot_builder("hmd"))


def _controller_buffers(device_name, se):
    (pos_x, pos_y, pos_z), (rot_w, rot_x, rot_y, rot_z) = get_transform(device_name)

    mod_input = get_module_input(device_name)
    mod_skeletal = get_module_skeletal(device_name)

    prefix = device_name

    sdl_trigger   = sdl.eval_binding(se.get(f"{prefix}_trigger", ""))
    sdl_a         = sdl.eval_binding(se.get(f"{prefix}_a", "")) > 0.5
    sdl_b         = sdl.eval_binding(se.get(f"{prefix}_b", "")) > 0.5
    sdl_system    = sdl.eval_binding(se.get(f"{prefix}_menu", "")) > 0.5
    touch_mod     = sdl.eval_binding(se.get(f"{prefix}_touch mod", "")) > 0.5

    joy_x   = sdl.eval_binding(se.get(f"{prefix}_joy right", "")) - sdl.eval_binding(se.get(f"{prefix}_joy left", ""))
    joy_y   = sdl.eval_binding(se.get(f"{prefix}_joy up", "")) - sdl.eval_binding(se.get(f"{prefix}_joy down", ""))
    joy_btn = sdl.eval_binding(se.get(f"{prefix}_joy click", "")) > 0.5

    touch_x = sdl.eval_binding(se.get(f"{prefix}_touch right", "")) - sdl.eval_binding(se.get(f"{prefix}_touch left", ""))
    touch_y = sdl.eval_binding(se.get(f"{prefix}_touch up", "")) - sdl.eval_binding(se.get(f"{prefix}_touch down", ""))

    touch_force = sdl.eval_binding(se.get(f"{prefix}_touch click", ""))

    raw_input = sdl.eval_binding(se.get(f"{prefix}_grip", ""))
    grip_pull = min(1.0, raw_input * 2.0)
    grip_force = max(0.0, (raw_input - 0.5) / 0.5)

    if touch_mod:
        touch_x = joy_x
        touch_y = joy_y
        touch_force = max(sdl.eval_binding(se.get(f"{prefix}_touch click", "")), joy_btn)
        joy_x = joy_y = 0.0
        joy_btn = False

    a       = bool(mod_input.get("a", False)) or sdl_a
    b       = bool(mod_input.get("b", False)) or sdl_b
    system  = bool(mod_input.get("system", False)) or sdl_system
    joy_btn = bool(mod_input.get("joy_btn", False)) or joy_btn

    trigger     = max(sdl_trigger, float(mod_input.get("trigger", 0.0)))
    grip_pull   = max(grip_pull, float(mod_input.get("grip_pull", 0.0)))
    grip_force  = max(grip_force, float(mod_input.get("grip_force", 0.0)))
    touch_force = max(touch_force, float(mod_input.get("touch_force", 0.0)))

    if abs(mod_input.get("joy_x", 0.0)) > abs(joy_x):
        joy_x = float(mod_input.get("joy_x", 0.0))
    if abs(mod_input.get("joy_y", 0.0)) > abs(joy_y):
        joy_y = float(mod_input.get("joy_y", 0.0))
    if abs(mod_input.get("touch_x", 0.0)) > abs(touch_x):
        touch_x = float(mod_input.get("touch_x", 0.0))
    if abs(mod_input.get("touch_y", 0.0)) > abs(touch_y):
        touch_y = float(mod_input.get("touch_y", 0.0))

    trigger_btn = (trigger > 0.99) or bool(mod_input.get("trigger_btn", False))

    a_cap      = a or bool(mod_input.get("a_cap", False))
    b_cap      = b or bool(mod_input.get("b_cap", False))
    system_cap = system or bool(mod_input.get("system_cap", False))

    trigger_cap = (trigger > 0.01) or bool(mod_input.get("trigger_cap", False))
    grip_cap    = (grip_pull > 0.01) or bool(mod_input.get("grip_cap", False))

    joy_cap   = joy_btn or abs(joy_x) > 0.1 or abs(joy_y) > 0.1 or bool(mod_input.get("joy_cap", False))
    touch_cap = (touch_force > 0.01) or abs(touch_x) > 0.1 or abs(touch_y) > 0.1 or bool(mod_input.get("touch_cap", False))

    fingers = ["thumb", "index", "middle", "ring", "pinky"]
    ov_flexion = mod_skeletal.get("l flexion" if prefix == "cl" else "r flexion", [0.0] * 20)

    if se.get("curl", True):
        flexion = list(ov_flexion)
        for i, finger in enumerate(fingers):
            val = sdl.eval_binding(se.get(f"{prefix}_{finger}", ""))
            flexion[i * 4] = max(flexion[i * 4], val)

        if se.get("index=trigger", False):
            if trigger < flexion[4]:
                trigger = -1 + (flexion[4] * 3)

        if se.get("other=grip", False):
            highest = max(flexion[8], flexion[12], flexion[16])
            if grip_pull < highest - 0.7:
                grip_pull = highest - 0.7
    else:
        flexion = [0.0] * 20
        for i, finger in enumerate(fingers):
            val = sdl.eval_binding(se.get(f"{prefix}_{finger}", ""))
            flexion[i * 4] = max(ov_flexion[i * 4], val)

    if se.get("splay", True):
        splays_5 = list(mod_skeletal.get("l splay" if prefix == "cl" else "r splay", [0.0] * 5))
    else:
        splays_5 = [0.0] * 5

    buf_pos = POS_PACKER.pack(float(pos_x), float(pos_y), float(pos_z))
    buf_rot = ROT_PACKER.pack(float(rot_w), float(rot_x), float(rot_y), float(rot_z))
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

    return {"pos": buf_pos, "rot": buf_rot, "input": buf_input, "skeletal": buf_skeletal}

def send_controller_data(is_right):
    device_name = "cr" if is_right else "cl"
    side = "RIGHT" if is_right else "LEFT"

    pipes = {
        slot: Pipe(PIPE_CONTROLLER_BASE.format(side=side, type=slot.capitalize()))
        for slot in ("pos", "rot", "input", "skeletal")
    }
    _run_device(device_name, pipes, lambda se: _controller_buffers(device_name, se))

def send_tracker_data(tracker_id):
    device_key = _tracker_device_key(tracker_id)
    pipes = {
        "pos": Pipe(rf'\\.\pipe\GlassVR_TRACKER_{tracker_id}_Pos'),
        "rot": Pipe(rf'\\.\pipe\GlassVR_TRACKER_{tracker_id}_Rot'),
    }
    _run_device(device_key, pipes, _pos_rot_builder(device_key))

def start_send_hmd():
    threading.Thread(target=send_hmd_data, daemon=True).start()

def start_send_controllers():
    threading.Thread(target=send_controller_data, args=(True,), daemon=True).start()
    threading.Thread(target=send_controller_data, args=(False,), daemon=True).start()

def start_send_trackers(count=64):
    threading.Thread(target=device_scanner, daemon=True).start()