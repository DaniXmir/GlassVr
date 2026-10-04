#driver page!
#will give you lots of errors if you somehow installed steam on disk-d!

import sys
import os
import json
import shutil
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
import subprocess

import elements as el
import settings as se

title = "Driver"
priority = 40

def get_steam_path() -> str:
    return str(se.get_settings().get('steam path', r'C:\Program Files (x86)\Steam')).strip().strip('"').strip()

def get_steamvr_path() -> str:
    return str(se.get_settings().get('steamvr path', r'C:\Program Files (x86)\Steam\steamapps\common\SteamVR')).strip().strip('"').strip()

def get_config_dir() -> str:
    return os.path.join(get_steam_path(), "config")

def get_drivers_dir() -> str:
    return os.path.join(get_steamvr_path(), "drivers")

def get_vrsettings_file() -> str:
    return os.path.join(get_config_dir(), "steamvr.vrsettings")

def get_log_file(suffix = "vrserver.txt") -> str:
    return os.path.join(get_steam_path(), "logs", suffix)

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

def is_steamvr_valid() -> bool:
    vr_p = get_steamvr_path()
    try:
        return (
            os.path.isdir(vr_p)
            and len(os.listdir(vr_p)) > 0
            and os.path.isdir(get_drivers_dir())
        )
    except OSError:
        return False

def set_activateMultipleDrivers_true():
    file_path = get_vrsettings_file()
    try:
        if not os.path.exists(file_path):
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "steamvr" not in data:
            data["steamvr"] = {}

        if data["steamvr"].get("activateMultipleDrivers") is True:
            return

        data["steamvr"]["activateMultipleDrivers"] = True

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    except Exception:
        pass

def get_activateMultipleDrivers_true() -> bool:
    file_path = get_vrsettings_file()
    try:
        if not os.path.exists(file_path):
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "steamvr" not in data:
            return False

        return data["steamvr"].get("activateMultipleDrivers") is True
    except Exception:
        return False

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    def folder_exist(path: str) -> bool:
        return os.path.isdir(path)

    steam_path_widget = el.lineedit({
        "text": "steam path",
        "default": get_steam_path(),
        "func": lambda: on_path_changed()
    })

    steamvr_path_widget = el.lineedit({
        "text": "steamvr path",
        "default": get_steamvr_path(),
        "func": lambda: on_path_changed()
    })

    steam_check_widget = el.label({
        "text": "steam status",
        "alignment": Qt.AlignmentFlag.AlignCenter
    })

    vr_check_widget = el.label({
        "text": "steamvr status",
        "alignment": Qt.AlignmentFlag.AlignCenter
    })

    install_label_widget = el.label({
        "text": "driver status",
        "alignment": Qt.AlignmentFlag.AlignCenter
    })

    config_label_widget = el.label({
        "text": "config status",
        "alignment": Qt.AlignmentFlag.AlignCenter
    })

    install_buttons_widget = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "button",
                "text": "install",
                "enabled": is_steamvr_valid(),
                "func": lambda: install_driver()
            },
            {
                "type": "button",
                "text": "uninstall",
                "enabled": True,
                "func": lambda: remove_driver()
            }
        ]
    })

    def set_label_status(widget: QWidget, text: str, color: str):
        lbl = widget.findChild(QLabel)
        if lbl:
            lbl.setText(text)
            lbl.setStyleSheet(f"color: {color};")

    def get_install_btn() -> QPushButton:
        btns = install_buttons_widget.findChildren(QPushButton)
        return btns[0] if btns else None

    def get_uninstall_btn() -> QPushButton:
        btns = install_buttons_widget.findChildren(QPushButton)
        return btns[1] if len(btns) > 1 else None

    def open_config_folder():
        try:
            os.startfile(se.get_path())
        except Exception:
            pass

    def open_steamvr_settings():
        try:
            os.startfile(get_vrsettings_file())
        except Exception:
            pass

    def open_log(filename="vrserver.txt"):
        try:
            os.startfile(get_log_file(filename))
        except Exception:
            pass

    config_row1 = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "button",
                "text": "open config",
                "enabled": True,
                "func": open_config_folder
            },
            {
                "type": "label",
                "text": se.get_path().removesuffix("\\settings.json"),
                "alignment": Qt.AlignmentFlag.AlignCenter
            }
        ]
    })

    config_row2 = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "button",
                "text": "open steamvr.vrsettings",
                "enabled": True,
                "func": open_steamvr_settings
            },
            {
                "type": "label",
                "text": get_config_dir(),
                "alignment": Qt.AlignmentFlag.AlignCenter
            }
        ]
    })

    log_row = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "button",
                "text": "open vrserver.txt",
                "enabled": True,
                "func": lambda: open_log("vrserver.txt")
            },
            {
                "type": "label",
                "text": get_log_file("vrserver.txt"),
                "alignment": Qt.AlignmentFlag.AlignCenter
            }
        ]
    })
    
    log2_row = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "button",
                "text": "open vrcompositor.txt",
                "enabled": True,
                "func": lambda: open_log("vrcompositor.txt")
            },
            {
                "type": "label",
                "text": get_log_file("vrcompositor.txt"),
                "alignment": Qt.AlignmentFlag.AlignCenter
            }
        ]
    })

    def update_all_labels(error_message=None):
        steam_p = get_steam_path()
        drivers_p = get_drivers_dir()
        glassvr_dir = os.path.join(drivers_p, "glassvrdriver")

        steam_exe = os.path.join(steam_p, "steam.exe")
        if os.path.exists(steam_exe):
            set_label_status(steam_check_widget, "Steam found ;P", "green")
        else:
            set_label_status(steam_check_widget, "steam.exe was not found, IS STEAM ON DISK-D???", "red")

        vr_valid = is_steamvr_valid()
        if vr_valid:
            set_label_status(vr_check_widget, "SteamVR found ;P", "green")
        else:
            set_label_status(vr_check_widget, "SteamVR folder was not found or empty!", "red")

        btn_inst = get_install_btn()
        btn_uninst = get_uninstall_btn()

        if error_message is not None:
            set_label_status(install_label_widget, f"ACTION FAILED: {error_message}", "red")
            if btn_inst:
                btn_inst.setText("install")
        else:
            if folder_exist(glassvr_dir):
                set_label_status(install_label_widget, "driver installed ;P", "green")
                if btn_inst:
                    btn_inst.setText("reinstall")
                if btn_uninst:
                    btn_uninst.setEnabled(True)
            else:
                set_label_status(install_label_widget, "driver not found, click install to install/update!", "yellow")
                if btn_inst:
                    btn_inst.setText("install")
                if btn_uninst:
                    btn_uninst.setEnabled(False)

        if btn_inst:
            btn_inst.setEnabled(vr_valid)

        if get_activateMultipleDrivers_true():
            set_label_status(config_label_widget, 'steamvr.vrsettings has: ("activateMultipleDrivers" : true) all good ;P', "green")
        else:
            if folder_exist(glassvr_dir):
                set_label_status(config_label_widget, 'steamvr.vrsettings is missing: ("activateMultipleDrivers" : true) set the correct path and click reinstall to add it!', "yellow")
            else:
                set_label_status(config_label_widget, 'steamvr.vrsettings is missing: ("activateMultipleDrivers" : true) set the correct path and click install to add it!', "yellow")

        cfg_lbls = config_row2.findChildren(QLabel)
        if cfg_lbls:
            cfg_lbls[0].setText(get_config_dir())

        log_lbls = log_row.findChildren(QLabel)
        if log_lbls:
            log_lbls[0].setText(get_log_file("vrserver.txt"))

        log2_lbls = log2_row.findChildren(QLabel)
        if log2_lbls:
            log2_lbls[0].setText(get_log_file("vrcompositor.txt"))

    def on_path_changed():
        sp_le = steam_path_widget.findChild(QLineEdit)
        vr_le = steamvr_path_widget.findChild(QLineEdit)

        if sp_le:
            se.update_setting('steam path', sp_le.text())
        if vr_le:
            se.update_setting('steamvr path', vr_le.text())

        set_activateMultipleDrivers_true()
        update_all_labels()

    def install_driver():
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(el.__file__))

        source_folder = os.path.join(script_dir, "assets", "driver to copy")
        destination_folder = get_drivers_dir()

        if not os.path.exists(source_folder):
            update_all_labels("driver folder 'assets/driver to copy' is missing!")
            return

        if not is_steamvr_valid():
            update_all_labels("SteamVR was not found in the given path (drivers folder missing)!")
            return

        try:
            shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
            set_activateMultipleDrivers_true()
            update_all_labels(None)
        except PermissionError:
            update_all_labels("permission denied! close Steam and SteamVR completely!")
        except Exception as e:
            update_all_labels(f"install failed: {str(e)}")

    def remove_driver():
        folder_path = os.path.join(get_drivers_dir(), 'glassvrdriver')

        if not os.path.exists(folder_path):
            return

        try:
            shutil.rmtree(folder_path)
            update_all_labels(None)
        except PermissionError:
            update_all_labels("permission denied! close Steam and SteamVR completely!")
        except Exception as e:
            update_all_labels(f"uninstall failed: {str(e)}")

    driver_group = el.group({
        "text": "Driver",
        "box": "v",
        "arr": [
            steam_path_widget,
            steamvr_path_widget,
            steam_check_widget,
            vr_check_widget,
            install_label_widget,
            config_label_widget,
            install_buttons_widget
        ],
        "tooltip" : "if you get any errors plz read them carefully!"
    })

    reset_cfg_btn = el.button({
        "text": "reset config",
        "enabled": True,
        "func": lambda: reset_config_and_restart()
    })

    config_group = el.group({
        "text": "Config",
        "box": "v",
        "arr": [
            reset_cfg_btn,
            config_row1,
            config_row2
        ],
        "tooltip" : "if you like editing staff the old fashioned way!"
    })

    log_group = el.group({
        "text": "Log",
        "box": "v",
        "arr": [
            log_row,
            log2_row
        ],
        "tooltip" : "the driver/app itself doesnt really have any logging :("
    })

    layout_main.addWidget(driver_group)
    layout_main.addWidget(config_group)
    layout_main.addWidget(log_group)

    update_all_labels()

    return el.scroll({"widget": tab_main})