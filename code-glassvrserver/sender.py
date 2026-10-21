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

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')
INDEX_INPUT_PACKER = struct.Struct('<12?8d')
FRAME_INPUT_PACKER = struct.Struct('<20?4d')
VIVE_INPUT_PACKER = struct.Struct('<6?3d')
TOUCH_INPUT_PACKER = struct.Struct('<8?4d')
SKELETAL_PACKER = struct.Struct('<25d')
EXTRA_PACKER = struct.Struct('<?')

PIPE_HMD_BASE = r'\\.\pipe\GlassVR_HMD_{tag}'
PIPE_TRACKER_BASE = r'\\.\pipe\GlassVR_TRACKER_{tracker_id}_{tag}'
PIPE_CONTROLLER_BASE = r'\\.\pipe\GlassVR_CONTROLLER_{side}_{tag}'

DEFAULT_MOD_INPUT = {
    "index": {
        "a": False, "b": False, "system": False,
        "joy_btn": False, "trigger_btn": False,
        "a_cap": False, "b_cap": False, "system_cap": False,
        "joy_cap": False, "trigger_cap": False,
        "touch_cap": False, "grip_cap": False,
        "joy_x": 0.0, "joy_y": 0.0,
        "touch_x": 0.0, "touch_y": 0.0,
        "trigger": 0.0, "touch_force": 0.0,
        "grip_pull": 0.0, "grip_force": 0.0,
    },
    "frame": {
        "y_up": False, "y_up_cap": False,
        "a_down": False, "a_down_cap": False,
        "x_left": False, "x_left_cap": False,
        "b_right": False, "b_right_cap": False,
        "select": False, "select_cap": False,
        "bumper": False, "bumper_cap": False,
        "system": False, "system_cap": False,
        "trigger_btn": False, "trigger_cap": False,
        "grip_btn": False, "grip_cap": False,
        "joy_btn": False, "joy_cap": False,
        "trigger": 0.0, "grip": 0.0,
        "joy_x": 0.0, "joy_y": 0.0,
    },
    "vive": {
        "system": False,
        "grip_btn": False,
        "select": False,
        "trigger_btn": False,
        "touch_btn": False,
        "touch_cap": False,
        "trigger": 0.0,
        "touch_x": 0.0,
        "touch_y": 0.0,
    },
    "touch": {
        "system": False,
        "a_x": False, "a_x_cap": False,
        "b_y": False, "b_y_cap": False,
        "trigger_cap": False,
        "joy_btn": False, "joy_cap": False,
        "trigger": 0.0,
        "grip": 0.0,
        "joy_x": 0.0,
        "joy_y": 0.0,
    }
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
        return copy.deepcopy(DEFAULT_MOD_INPUT)

    entry = _find_transform_entry(module, device)
    if entry is not None and "input" in entry and isinstance(entry["input"], dict):
        res = copy.deepcopy(DEFAULT_MOD_INPUT)
        res.update(entry["input"])
        return res

    mod_input = getattr(module, "input", None)
    if isinstance(mod_input, dict):
        res = copy.deepcopy(DEFAULT_MOD_INPUT)
        res.update(mod_input)
        return res

    return copy.deepcopy(DEFAULT_MOD_INPUT)

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

HOOK_FINGERS = ("thumb", "index", "middle", "ring", "pinky")

def _hook_hand_slots(se):
    need = {}
    entries = se.get("hook overrides", [])
    if not isinstance(entries, list):
        return need

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        skeletal = entry.get("skeletal override", "")
        if skeletal in ("cl", "cr") and any(
                entry.get(f"{f} curl override") or entry.get(f"{f} splay override") for f in HOOK_FINGERS):
            need.setdefault(skeletal, set()).add("skeletal")

        source = entry.get("input override", "")
        if source in ("cl", "cr") and any(
                v is True for k, v in entry.items() if k.startswith("input ") and k.endswith(" override")):
            need.setdefault(source, set()).add("input")
    return need

def _hook_slots(device, se):
    return tuple(sorted(_hook_hand_slots(se).get(device, ())))

def _desired_device_slots(se):
    desired = {dev: ("pos", "rot", "input", "skeletal") for dev in _enabled_devices(se)}
    for hand, slots in _hook_hand_slots(se).items():
        desired.setdefault(hand, tuple(sorted(slots)))
    return desired

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

        for dev, slots in _desired_device_slots(se).items():
            for slot in slots:
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

TAG_TO_SLOT = {
    "pos": "pos",
    "rot": "rot",
    "idx": "input", "ifm": "input", "ive": "input", "itc": "input",
    "skl": "skeletal",
}

def pipe_wanted(device, tag, se):
    slot = TAG_TO_SLOT.get(tag, tag)
    if not is_device_enabled(device, se) and slot not in _hook_slots(device, se):
        return False
    return not pipe_disabled(device, slot, se)

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
            for tag, pipe in pipes.items():
                if pipe_wanted(device, tag, se):
                    wanted.add(tag)
                else:
                    pipe.close()

            if not wanted:
                time.sleep(0.5)
                continue

            buffers = build_buffers(se)
            for tag in wanted:
                if tag in buffers and buffers[tag]:
                    pipes[tag].write(buffers[tag])

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
            "ext": EXTRA_PACKER.pack(False),
        }
    return build

def send_hmd_data():
    pipes = {
        "pos": Pipe(PIPE_HMD_BASE.format(tag="pos")),
        "rot": Pipe(PIPE_HMD_BASE.format(tag="rot")),
        "ext": Pipe(PIPE_HMD_BASE.format(tag="ext")),
    }
    _run_device("hmd", pipes, _pos_rot_builder("hmd"))

def _controller_buffers(device_name, se):
    (pos_x, pos_y, pos_z), (rot_w, rot_x, rot_y, rot_z) = get_transform(device_name)

    mod_input = get_module_input(device_name)
    mod_skeletal = get_module_skeletal(device_name)
    prefix = device_name
    con_type = se.get("con type", "touch")

    idx_data = mod_input.get("index", {})
    frm_data = mod_input.get("frame", {})
    viv_data = mod_input.get("vive", {})
    tch_data = mod_input.get("touch", {})

    ov_flexion = mod_skeletal.get("l flexion" if prefix == "cl" else "r flexion", [0.0] * 20)
    flexion = list(ov_flexion)
    splays_5 = list(mod_skeletal.get("l splay" if prefix == "cl" else "r splay", [0.0] * 5))

    buf_pos = POS_PACKER.pack(float(pos_x), float(pos_y), float(pos_z))
    buf_rot = ROT_PACKER.pack(float(rot_w), float(rot_x), float(rot_y), float(rot_z))

    # Match PacketInputIndex exactly: 12 bools, 8 doubles
    buf_idx = INDEX_INPUT_PACKER.pack(
        bool(idx_data.get("a", False)), 
        bool(idx_data.get("b", False)), 
        bool(idx_data.get("system", False)),
        bool(idx_data.get("joy_btn", False)), 
        bool(idx_data.get("trigger_btn", False)),
        bool(idx_data.get("a_cap", False)), 
        bool(idx_data.get("b_cap", False)), 
        bool(idx_data.get("system_cap", False)),
        bool(idx_data.get("joy_cap", False)), 
        bool(idx_data.get("trigger_cap", False)),
        bool(idx_data.get("touch_cap", False)), 
        bool(idx_data.get("grip_cap", False)),
        float(idx_data.get("joy_x", 0.0)), 
        float(idx_data.get("joy_y", 0.0)),
        float(idx_data.get("touch_x", 0.0)), 
        float(idx_data.get("touch_y", 0.0)),
        float(idx_data.get("trigger", 0.0)),
        float(idx_data.get("touch_force", 0.0)),
        float(idx_data.get("grip_pull", 0.0)),
        float(idx_data.get("grip_force", 0.0)),
    ) if con_type == "index" else b''

    # Match PacketInputFrame exactly: 20 bools, 4 doubles
    buf_ifm = FRAME_INPUT_PACKER.pack(
        bool(frm_data.get("y_up", False)), bool(frm_data.get("y_up_cap", False)),
        bool(frm_data.get("a_down", False)), bool(frm_data.get("a_down_cap", False)),
        bool(frm_data.get("x_left", False)), bool(frm_data.get("x_left_cap", False)),
        bool(frm_data.get("b_right", False)), bool(frm_data.get("b_right_cap", False)),
        bool(frm_data.get("select", False)), bool(frm_data.get("select_cap", False)),
        bool(frm_data.get("bumper", False)), bool(frm_data.get("bumper_cap", False)),
        bool(frm_data.get("system", False)), bool(frm_data.get("system_cap", False)),
        bool(frm_data.get("trigger_btn", False)), bool(frm_data.get("trigger_cap", False)),
        bool(frm_data.get("grip_btn", False)), bool(frm_data.get("grip_cap", False)),
        bool(frm_data.get("joy_btn", False)), bool(frm_data.get("joy_cap", False)),
        float(frm_data.get("trigger", 0.0)), float(frm_data.get("grip", 0.0)),
        float(frm_data.get("joy_x", 0.0)), float(frm_data.get("joy_y", 0.0))
    ) if con_type == "frame" else b''

    # Match PacketInputVive exactly: 6 bools, 3 doubles
    buf_ive = VIVE_INPUT_PACKER.pack(
        bool(viv_data.get("system", False)), 
        bool(viv_data.get("grip_btn", False)),
        bool(viv_data.get("select", False)), 
        bool(viv_data.get("trigger_btn", False)),
        bool(viv_data.get("touch_btn", False)), 
        bool(viv_data.get("touch_cap", False)),
        float(viv_data.get("trigger", 0.0)), 
        float(viv_data.get("touch_x", 0.0)), 
        float(viv_data.get("touch_y", 0.0))
    ) if con_type == "vive" else b''

    # Match PacketInputTouch exactly: 8 bools, 4 doubles
    buf_itc = TOUCH_INPUT_PACKER.pack(
        bool(tch_data.get("system", False)), 
        bool(tch_data.get("a_x", False)), 
        bool(tch_data.get("a_x_cap", False)),
        bool(tch_data.get("b_y", False)), 
        bool(tch_data.get("b_y_cap", False)), 
        bool(tch_data.get("trigger_cap", False)),
        bool(tch_data.get("joy_btn", False)), 
        bool(tch_data.get("joy_cap", False)),
        float(tch_data.get("trigger", 0.0)), 
        float(tch_data.get("grip", 0.0)),
        float(tch_data.get("joy_x", 0.0)), 
        float(tch_data.get("joy_y", 0.0))
    ) if con_type == "touch" else b''

    buf_skl = SKELETAL_PACKER.pack(
        *[float(f) for f in flexion],
        *[float(s) for s in splays_5],
    )

    buf_ext = EXTRA_PACKER.pack(False)

    return {
        "pos": buf_pos,
        "rot": buf_rot,
        "idx": buf_idx,
        "ifm": buf_ifm,
        "ive": buf_ive,
        "itc": buf_itc,
        "skl": buf_skl,
        "ext": buf_ext,
    }

def send_controller_data(is_right):
    device_name = "cr" if is_right else "cl"
    side = "RIGHT" if is_right else "LEFT"

    pipes = {
        tag: Pipe(PIPE_CONTROLLER_BASE.format(side=side, tag=tag))
        for tag in ("pos", "rot", "idx", "ifm", "ive", "itc", "skl", "ext")
    }
    _run_device(device_name, pipes, lambda se: _controller_buffers(device_name, se))

def send_tracker_data(tracker_id):
    device_key = _tracker_device_key(tracker_id)
    pipes = {
        "pos": Pipe(PIPE_TRACKER_BASE.format(tracker_id=tracker_id, tag="pos")),
        "rot": Pipe(PIPE_TRACKER_BASE.format(tracker_id=tracker_id, tag="rot")),
    }
    _run_device(device_key, pipes, _pos_rot_builder(device_key))

def start_send_hmd():
    threading.Thread(target=send_hmd_data, daemon=True).start()

def start_send_controllers():
    threading.Thread(target=send_controller_data, args=(True,), daemon=True).start()
    threading.Thread(target=send_controller_data, args=(False,), daemon=True).start()

def start_send_trackers(count=64):
    threading.Thread(target=device_scanner, daemon=True).start()