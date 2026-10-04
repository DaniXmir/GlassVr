#themes page!

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea, QGroupBox,QFrame
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QColor, QPalette, QMovie

import elements as el

title = "Themes"
priority = 998

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    info_g = el.theme_info()
    layout_main.addWidget(info_g)

    s = el.theme_selector()

    selector_g = el.group({
    "text": "selector",
    "box": "v",
    "arr": [
        s
    ]
    })
    layout_main.addWidget(selector_g)

    return tab_main