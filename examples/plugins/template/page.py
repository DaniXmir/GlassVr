from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton
import math

import steamvr as svr
import elements as el
import settings as se
import controller_handler as sdl

title = "template"
priority = 100

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    return el.scroll({"widget": tab_main})