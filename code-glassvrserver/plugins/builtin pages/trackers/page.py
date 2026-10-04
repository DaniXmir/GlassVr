from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSpinBox

import elements as el
import settings as se
import theme_registry as tr

title = "Trackers"
priority = 20

MAX_TRACKERS = 64

_trackers_container_widget = None
_tracker_widgets = {}


def _tracker_device_key(n):
    return f"{n}tracker"


def _build_tracker_widget(n):
    device = _tracker_device_key(n)

    modes_widget = el.modes(device)
    offsets_widget = el.offsets(device)

    group = el.group({
        "text": f"Tracker {n}",
        "box": "v",
        "group": "block",
        "arr": [modes_widget, offsets_widget],
    })
    tr.style_block(group, n)

    return group


def _sync_trackers():
    count = se.get_settings().get("trackers num", 0)

    order = []
    for n in range(count):
        widget = _tracker_widgets.get(n)
        if widget is None:
            widget = _build_tracker_widget(n)
            _tracker_widgets[n] = widget
        order.append(widget)

    stale_indices = [n for n in _tracker_widgets if n >= count]
    for n in stale_indices:
        widget = _tracker_widgets.pop(n)
        widget.setParent(None)
        widget.deleteLater()

    el.reorder_group({
        "widget": _trackers_container_widget,
        "order": order,
    })


def tab() -> QWidget:
    global _trackers_container_widget

    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    count_spinbox = el.spinbox({
        "text": "create trackers",
        "min": 0,
        "max": MAX_TRACKERS,
        "default": se.get_settings().get("trackers num", 0),
        "steps": 1,
        "func": lambda: (
            se.update_setting("trackers num", count_spinbox.findChildren(QSpinBox)[0].value()),
            _sync_trackers(),
        ),
    })

    count_g = el.group({
        "text": "trackers",
        "box": "v",
        "arr": [count_spinbox],
        "tooltip" : "select how many trackers you want to emulate!"
    })
    layout_main.addWidget(count_g,stretch=1)

    _trackers_container_widget = QWidget()
    QVBoxLayout(_trackers_container_widget)
    layout_main.addWidget(_trackers_container_widget)

    _sync_trackers()

    return el.scroll({"widget": tab_main})