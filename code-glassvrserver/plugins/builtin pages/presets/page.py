#presets page!
#saves/loads copies of AppData\Roaming\glassvr\settings.json
#presets located in <root>\assets\presets\<name>.json

import sys
import os
import json
import shutil
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit

import elements as el
import settings as se

title = "presets"
priority = 996

INVALID_CHARS = '<>:"/\\|?*'

def get_root_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(el.__file__))

def get_presets_dir() -> str:
    path = os.path.join(get_root_dir(), "assets", "presets")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path

def preset_path(name: str) -> str:
    return os.path.join(get_presets_dir(), name + ".json")

def validate_name(name: str):
    name = name.strip()
    if not name:
        return "name is empty"
    if any(c in name for c in INVALID_CHARS):
        return f"name can't contain any of these: {INVALID_CHARS}"
    if name.endswith(".") or name.endswith(" "):
        return "name can't end with a dot or space"

    try:
        existing = {os.path.splitext(f)[0].lower() for f in os.listdir(get_presets_dir()) if f.lower().endswith(".json")}
    except OSError:
        existing = set()
    if name.lower() in existing:
        return "a preset with this name already exists!"
    return None

def list_presets() -> list:
    out = []
    try:
        files = sorted(os.listdir(get_presets_dir()), key=str.lower)
    except OSError:
        return out

    for f in files:
        if not f.lower().endswith(".json"):
            continue
        path = os.path.join(get_presets_dir(), f)
        desc = ""
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            desc = str(data.get("description", ""))
        except Exception:
            desc = "(couldn't read this file)"
        out.append((os.path.splitext(f)[0], desc, path))
    return out

def restart_app():
    if getattr(sys, 'frozen', False):
        cmd = [sys.executable] + sys.argv[1:]
    else:
        cmd = [sys.executable, os.path.abspath(sys.argv[0])] + sys.argv[1:]
    try:
        subprocess.Popen(cmd, cwd=os.getcwd())
    except Exception:
        return
    app = QApplication.instance()
    if app:
        app.quit()
    else:
        sys.exit(0)

def reset_config_and_restart():
    se.reset_settings()
    restart_app()

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    #add preset//////////////////////////////////////
    name_widget = el.lineedit({
        "text": "name",
        "default": "",
        "placeholder": "preset name?",
        "func": lambda: on_name_changed()
    })

    desc_widget = el.lineedit({
        "text": "desc",
        "default": "",
        "placeholder": "preset description?"
    })

    add_widget = el.button({
        "text": "add",
        "enabled": False,
        "func": lambda: add_preset()
    })

    def get_name() -> str:
        le = name_widget.findChild(QLineEdit)
        return le.text().strip() if le else ""

    def get_desc() -> str:
        le = desc_widget.findChild(QLineEdit)
        return le.text().strip() if le else ""

    def get_add_btn() -> QPushButton:
        return add_widget.findChild(QPushButton)

    def on_name_changed():
        name = get_name()
        btn = get_add_btn()

        if btn:
            btn.setEnabled(bool(name) and validate_name(name) is None)

    def add_preset():
        name = get_name()
        if validate_name(name) is not None:
            return

        try:
            se.get_settings()

            dst = preset_path(name)
            shutil.copyfile(se.get_path(), dst)

            with open(dst, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["description"] = get_desc()
            with open(dst, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception:
            return

        name_le = name_widget.findChild(QLineEdit)
        desc_le = desc_widget.findChild(QLineEdit)
        if name_le:
            name_le.setText("")
        if desc_le:
            desc_le.setText("")

        refresh_list()

    add_group = el.group({
        "text": "add preset",
        "box": "v",
        "arr": [
            name_widget,
            desc_widget,
            add_widget
        ],
        "tooltip": "saves a copy of your current settings as a preset"
    })

    #preset list//////////////////////////////////////
    list_container = QWidget()
    list_layout = QVBoxLayout(list_container)

    def use_preset(path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)  #refuse to apply a broken file
            shutil.copyfile(path, se.get_path())
        except Exception:
            return
        restart_app()

    def delete_preset(path: str):
        try:
            os.remove(path)
        except Exception:
            return

        refresh_list()
        on_name_changed()  #the name might be free again

    def refresh_list():
        el.clear_layout(list_layout)

        presets = list_presets()
        if not presets:
            list_layout.addWidget(el.label({"text": "no presets yet"}))

        for name, desc, path in presets:
            list_layout.addWidget(el.group({
                "text": "",
                "box": "h",
                "arr": [
                    el.label({"text": name}),
                    el.label({"text": desc}),
                    el.button({
                        "text": "use",
                        "enabled": True,
                        "func": lambda p=path: use_preset(p)
                    }),
                    el.button({
                        "text": "delete",
                        "enabled": True,
                        "func": lambda p=path: delete_preset(p)
                    })
                ]
            }))

        list_layout.addStretch(1)

    presets_scroll = el.scroll({"widget": list_container})
    presets_scroll.setMinimumHeight(300)

    list_group = el.group({
        "text": "saved presets",
        "box": "v",
        "arr": [presets_scroll]
    })

    #reset//////////////////////////////////////
    reset_cfg_btn = el.button({
        "text": "reset config",
        "enabled": True,
        "func": lambda: reset_config_and_restart()
    })

    config_group = el.group({
        "text": "Config",
        "box": "v",
        "arr": [reset_cfg_btn],
        "tooltip": "restarts the app and revert to default settings"
    })

    layout_main.addWidget(add_group)
    layout_main.addWidget(list_group)
    layout_main.addWidget(config_group)

    refresh_list()

    return el.scroll({"widget": tab_main})