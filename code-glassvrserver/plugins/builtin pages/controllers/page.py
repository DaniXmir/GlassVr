#controller page!

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox
import elements as el
import settings as se
import controller_handler as sdl
import threading
import time

title = "Controllers"
priority = 10

#TODO: update to support vive/oculus/sf
mapping = ["a", "b", "trigger", "grip", "menu", 
           "joy up", "joy down", "joy left", "joy right", "joy click", 
           "touch up", "touch down", "touch left", "touch right", "touch click", 
           "thumb", "index", "middle", "ring", "pinky", 
           "touch mod"]

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    settings = se.get_settings()

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

    gl = el.group({
    "text": f"cl",
    "box": "h",
    "arr": [
        el.binding_group(mapping, "cl")
    ]
    })

    gr = el.group({
    "text": f"cr",
    "box": "h",
    "arr": [
        el.binding_group(mapping, "cr")
    ]
    })

    mappings_g = el.group({
    "text": "mappings",
    "box": "h",
    "arr": [
        gl,
        el.image({"path" : "assets/index black.png"}),
        gr
    ],
    "tooltip" : "you can bind multiple physical controllers/keyboards/mice to one action, you can also invert axis and button states!"
    })
    layout_main.addWidget(mappings_g)

    layout_main.addWidget(el.offsets("cr"))
    layout_main.addWidget(el.offsets("cl"))

    return el.scroll({"widget": tab_main})