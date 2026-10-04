#creates a page for wasd module

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox
import math
import elements as el
import settings as se

title = "wasd"
priority = 80

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    #idk
    c_group = QWidget()
    c_layout = QHBoxLayout(c_group)
    c_layout.addWidget(el.label({"text" : "                                                                                 "}))
    c_layout.addWidget(el.capture_button())
    c_layout.addWidget(el.label({"text" : "                                                                                 "}))

    l_g = el.group({
    "text": "wasd",
    "box": "v",
    "arr": [
        el.label({"text" : "click capture to lock your input to this page, also plz avoid binding/pressing 'tab' it can sometime escape,\nidk, you have a better idea?\n(recommend to put the ui in your second monitor if you can!)"}),
        
    ]
    })
    layout_main.addWidget(l_g)

    enable_g = el.group({
    "text": "wasd",
    "box": "v",
    "arr": [
        c_group
        
    ]
    })
    layout_main.addWidget(enable_g,stretch=10)

    return el.scroll({"widget": tab_main})