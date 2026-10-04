#creates a page for hand tracking settings
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QSpinBox, QDoubleSpinBox

import elements as el
import settings as se
from . import hand_tracking as ht #<- this is how to import outside of root!

title = "hand tracking"
priority = 90

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    l = el.label({"text" : "plz set input/skeletal communication to 'hand tracking' in the controller tab!"})

    l_g = el.group({
        "text": "warning",
        "box": "v",
        "arr": [l]
    })

    layout_main.addWidget(l_g, stretch=1)

    def toggle_hand_tracking():
        enabled = webcam_controls.findChildren(QCheckBox)[0].isChecked()
        se.update_setting("hand tracking", enabled)

        if enabled:
            ht.start_camera()
        else:
            ht.stop_camera()

    webcam_controls = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "checkbox",
                "text": "enable hand tracking",
                "default": se.get_settings().get("hand tracking", False),
                "func": toggle_hand_tracking,
            },
            {
                "type": "checkbox",
                "text": "curl",
                "default": se.get_settings().get("curl", True),
                "func": lambda: se.update_setting(
                    "curl", webcam_controls.findChildren(QCheckBox)[1].isChecked()
                ),
            },
            {
                "type": "checkbox",
                "text": "splay",
                "default": se.get_settings().get("splay", True),
                "func": lambda: se.update_setting(
                    "splay", webcam_controls.findChildren(QCheckBox)[2].isChecked()
                ),
            },
            {
                "type": "checkbox",
                "text": "index curl effects trigger",
                "default": se.get_settings().get("index=trigger", False),
                "func": lambda: se.update_setting(
                    "index=trigger", webcam_controls.findChildren(QCheckBox)[3].isChecked()
                ),
            },
            {
                "type": "checkbox",
                "text": "other curl effects grip",
                "default": se.get_settings().get("other=grip", False),
                "func": lambda: se.update_setting(
                    "other=grip", webcam_controls.findChildren(QCheckBox)[4].isChecked()
                ),
            },
        ],
    })

    camera_settings = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "physical camera offset x",
                "min": -999999999, "max": 999999999,
                "default": se.get_settings().get("camera offset x", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "camera offset x", camera_settings.findChildren(QDoubleSpinBox)[0].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "physical camera offset y",
                "min": -999999999, "max": 999999999,
                "default": se.get_settings().get("camera offset y", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "camera offset y", camera_settings.findChildren(QDoubleSpinBox)[1].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "physical camera offset z",
                "min": -999999999, "max": 999999999,
                "default": se.get_settings().get("camera offset z", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "camera offset z", camera_settings.findChildren(QDoubleSpinBox)[2].value()
                ),
            },
            {
                "type": "spinbox",
                "text": "camera index",
                "min": 0, "max": 999999999,
                "default": se.get_settings().get("camera index", 0),
                "steps": 1,
                "func": lambda: se.update_setting(
                    "camera index", camera_settings.findChildren(QSpinBox)[0].value()
                ),
            },
        ],
    })

    hand_tracking_group = el.group({
        "text": "Hand Tracking",
        "box": "v",
        "arr": [webcam_controls, camera_settings],
        "tooltip": "this is inside-out tracking meaning the camera needs "
                   "to be on your face, also don't expect anything crazy.. ok",
    })

    layout_main.addWidget(hand_tracking_group, stretch=3)

    if se.get_settings().get("hand tracking", False):
        ht.start_camera()

    return el.scroll({"widget": tab_main})