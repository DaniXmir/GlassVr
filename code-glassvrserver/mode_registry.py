#slop

import sys
import os
import re
import importlib.util

import globals as gl

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_cache = None #{title: module}

def discover_modes(force_reload=False):
    global _cache

    if _cache is not None and not force_reload:
        return _cache

    base_dir = _get_base_dir()
    plugins_dir = os.path.join(base_dir, "plugins")
    discovered = {}

    for plugin_folder in gl.get_plugin_folders(plugins_dir):
        module_path = os.path.join(plugin_folder, "module.py")
        if not os.path.isfile(module_path):
            continue

        folder_name = os.path.basename(plugin_folder)
        rel_path = os.path.relpath(plugin_folder, plugins_dir)
        import_key = rel_path.replace(os.sep, ".").replace(" ", "_")

        spec = importlib.util.spec_from_file_location(f"plugins.{import_key}.module", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module

            gl.add_plugin_libs(plugin_folder)

            try:
                spec.loader.exec_module(module)
            except Exception as e:
                gl.log_plugin_error(folder_name, e)
                sys.modules.pop(spec.name, None)
                continue

            mode_title = getattr(module, "title", folder_name)
            discovered[mode_title] = module

    _cache = discovered
    return _cache

_GENERIC_FIXED = {
    "controller": ("cr", "cl"),
    "controllers": ("cr", "cl"),
}

_TRACKER_PATTERN = re.compile(r"^(?:\d+tracker|tracker\d+)$")

def device_matches(device, allowed_devices):
    if device in allowed_devices:
        return True

    for generic, specifics in _GENERIC_FIXED.items():
        if generic in allowed_devices and device in specifics:
            return True

    if _TRACKER_PATTERN.match(device) and ("tracker" in allowed_devices or "trackers" in allowed_devices):
        return True

    return False

def get_mode(title):
    return discover_modes().get(title)