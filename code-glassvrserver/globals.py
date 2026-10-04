#misc function helpers

import os
import sys
import time
import traceback

#TODO: update when adding oculus/sf compatibility
_DEVICE_SERIAL_MAP = {
    "hmd": "GlassVRHmd",
    "cr": "GlassVRConRight",
    "cl": "GlassVRConLeft",
}

def device_to_serial(device=""):
    if device in _DEVICE_SERIAL_MAP:
        return _DEVICE_SERIAL_MAP[device]

    if device.endswith("tracker"):
        index_part = device[:-len("tracker")]
        if index_part.isdigit():
            return f"GlassVRTrk{index_part}"

    return ""

_EXCLUDED_PLUGIN_FOLDERS = {"dev"}

def _is_excluded_folder(name):
    return name.lower() in _EXCLUDED_PLUGIN_FOLDERS

def get_plugin_folders(plugins_dir):
    if not os.path.exists(plugins_dir):
        return

    for entry in sorted(os.listdir(plugins_dir)):
        first_level = os.path.join(plugins_dir, entry)
        if (not os.path.isdir(first_level) or entry.startswith("__") or entry.startswith(".")
                or _is_excluded_folder(entry)):
            continue

        if any(os.path.isfile(os.path.join(first_level, f)) for f in ("page.py", "module.py", "theme.json")):
            yield first_level
        else:
            for sub_entry in sorted(os.listdir(first_level)):
                second_level = os.path.join(first_level, sub_entry)
                if (os.path.isdir(second_level) and not sub_entry.startswith("__")
                        and not sub_entry.startswith(".") and not _is_excluded_folder(sub_entry)):
                    yield second_level

def add_plugin_libs(plugin_folder):
    libs = os.path.join(plugin_folder, "libs")
    if os.path.isdir(libs) and libs not in sys.path:
        sys.path.append(libs)
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(libs)
            except OSError:
                pass

def log_plugin_error(plugin_name, error):
    print(f"Skipping plugin '{plugin_name}': {error}")
    try:
        log_dir = os.path.join(os.getenv("APPDATA", "."), "glassvr")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "plugin_errors.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] plugin '{plugin_name}' failed to load\n")
            f.write("".join(traceback.format_exception(type(error), error, error.__traceback__)))
            f.write("\n")
    except Exception:
        pass