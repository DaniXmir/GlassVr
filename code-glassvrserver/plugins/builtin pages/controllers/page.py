# controller page!

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox
import elements as el
import settings as se
import controller_handler as sdl
import threading
import time
import os

title = "Controllers"
priority = 10

GROUP_ORDER = ["main", "face", "joystick", "touchpad", "extra", "skeletal"]

SKELETAL = ["thumb", "index", "middle", "ring", "pinky"]

_INDEX = {
    "main":     ["system", "trigger", "grip"],
    "face":     ["a", "b"],
    "joystick": ["joy_click", "joy_up", "joy_down", "joy_left", "joy_right"],
    "touchpad": ["touch_click", "touch_up", "touch_down", "touch_left", "touch_right"],
    "extra":    ["touchmod"],
}

_VIVE = {
    "main":     ["system", "trigger", "grip_btn"],
    "face":     ["select"],
    "joystick": ["touch_btn", "touch_up", "touch_down", "touch_left", "touch_right"],
}

CONTROLLER_GROUPS_LEFT = {
    "index": _INDEX,
    "vive": _VIVE,
    "frame": {
        "main":     ["system", "trigger", "grip"],
        "face":     ["up", "down", "left", "right"],
        "joystick": ["joy_click", "joy_up", "joy_down", "joy_left", "joy_right"],
        "extra":    ["select", "bumper"],
    },
    "touch": {
        "main":     ["system", "trigger", "grip"],
        "face":     ["x", "y"],
        "joystick": ["joy_click", "joy_up", "joy_down", "joy_left", "joy_right"],
    },
}

CONTROLLER_GROUPS_RIGHT = {
    "index": _INDEX,
    "vive": _VIVE,
    "frame": {
        "main":     ["system", "trigger", "grip"],
        "face":     ["a", "b", "x", "y"],
        "joystick": ["joy_click", "joy_up", "joy_down", "joy_left", "joy_right"],
        "extra":    ["menu", "bumper"],
    },
    "touch": {
        "main":     ["system", "trigger", "grip"],
        "face":     ["a", "b"],
        "joystick": ["joy_click", "joy_up", "joy_down", "joy_left", "joy_right"],
    },
}

CONTROLLER_MAPPINGS_LEFT = CONTROLLER_GROUPS_LEFT
CONTROLLER_MAPPINGS_RIGHT = CONTROLLER_GROUPS_RIGHT

def build_bindings(groups: dict, prefix: str, side: str):
    groups = {**groups, "skeletal": SKELETAL}
    subgroups = [
        el.group({
            "text": name,
            "box": "v",
            "arr": [el.binding_group(groups[name], prefix)]
        })
        for name in GROUP_ORDER if groups.get(name)
    ]
    return el.group({"text": side, "box": "v", "arr": subgroups})


def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    enable_checkbox = el.multitype({"box" : "h", "arr" :[
        {
            "type" : "checkbox",
            "text" : "enable left",
            "default" : se.get_settings()['enable cl'],
            "func" : lambda: se.update_setting(f"enable cl", enable_checkbox.findChildren(QCheckBox)[0].isChecked())
        },
        {
            "type" : "checkbox",
            "text" : "enable right",
            "default" : se.get_settings()['enable cr'],
            "func" : lambda: se.update_setting(f"enable cr", enable_checkbox.findChildren(QCheckBox)[1].isChecked())
        },
    ]})

    enable_g = el.group({
    "text": "enable",
    "box": "h",
    "arr": [
        enable_checkbox
    ],
    "tooltip" : "enables right and left controller emulation respectively"
    })
    layout_main.addWidget(enable_g)

    modes_cr = el.modes("cr")
    modes_cl = el.modes("cl")

    modes_g = el.group({
    "text": "modes",
    "box": "v",
    "arr": [
        modes_cr,
        modes_cl
    ],
    "tooltip" : "position and rotation modes of the simulated left and right controllers"
    })
    layout_main.addWidget(modes_g)

    input_g = el.group({
    "text": "input communication",
    "box": "h",
    "arr": [
        el.comm("cl"),
        el.comm("cr")
    ],
    "tooltip" : "if using hand tracking select it here"
    })
    layout_main.addWidget(input_g)

    mappings_container = QWidget()
    mappings_layout = QHBoxLayout(mappings_container)
    mappings_layout.setContentsMargins(0, 0, 0, 0)

    def refresh_mappings(con_type):
        el.clear_layout(mappings_layout)

        groups_left = CONTROLLER_GROUPS_LEFT.get(con_type, CONTROLLER_GROUPS_LEFT["touch"])
        groups_right = CONTROLLER_GROUPS_RIGHT.get(con_type, CONTROLLER_GROUPS_RIGHT["touch"])

        gl = build_bindings(groups_left, f"cl_{con_type}", "cl")
        gr = build_bindings(groups_right, f"cr_{con_type}", "cr")

        # use the shared resolver (checks APP_ROOT, exe dir, cwd) instead of
        # only APP_ROOT, so this also works in a built exe
        img_path = f"assets/{con_type}.png"

        if not el.resolve_asset_path(img_path):
            img_path = "assets/index.png"

        mappings_layout.addWidget(gl)
        mappings_layout.addWidget(el.image({"path": img_path}))
        mappings_layout.addWidget(gr)

    current_con_type = se.get_settings().get("con type", "touch")
    if current_con_type not in CONTROLLER_MAPPINGS_LEFT:
        current_con_type = "touch"

    contype_combo = el.combobox({
        "text": "controller type",
        "default": current_con_type,
        "items": list(CONTROLLER_MAPPINGS_LEFT.keys()),
        "index change": lambda: (
            new_type := contype_combo.findChildren(QComboBox)[0].currentText(),
            se.update_setting("con type", new_type),
            refresh_mappings(new_type)
        ),
        "tooltip": "the controller type steamvr sees, can be changed at run time (with most games)" \
                    "\n\nvive: not 1:1 emulation since i also added a skeletal component, only use for super old vr games from 2016" \
                    "\n\ntouch: classic oculus rift cv1 controllers! with all their surprisingly modern input scheme and 2 additional ones for middle and pinky fingers! recommended!" \
                    "\n\nindex: outdated abomination, touchpad is almost never used but for games that do use it i included a touch mod button that redirect inputs from the joystick to it" \
                    "\n\nframe: modern with lots of inputs! use if you have enough inputs, if not use touch"
    })

    contype_g = el.group({
    "text": f"compatibility mode",
    "box": "h",
    "arr": [
        contype_combo
    ]
    })
    layout_main.addWidget(contype_g)

    mappings_g = el.group({
    "text": "mappings",
    "box": "h",
    "arr": [
        mappings_container
    ],
    "tooltip" : "you can bind multiple physical controllers/keyboards/mice to one action, you can also invert axis and button states!"
    })
    layout_main.addWidget(mappings_g)

    refresh_mappings(current_con_type)

    layout_main.addWidget(el.offsets("cr"))
    layout_main.addWidget(el.offsets("cl"))

    return el.scroll({"widget": tab_main})