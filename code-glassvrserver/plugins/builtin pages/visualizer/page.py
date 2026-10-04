#creates a page for visualizer settings!

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
)

import elements as el
import settings as se
from visualizer import Renderer3D

title = "Visualizer"
priority = 70

renderer_popout_window = None

def _ensure_popout_window():
    global renderer_popout_window

    if renderer_popout_window is not None:
        return renderer_popout_window

    renderer_popout_window = QWidget()
    renderer_popout_window.setWindowTitle("GlassVR - Visualizer")
    renderer_popout_window.resize(1000, 700)

    layout = QVBoxLayout(renderer_popout_window)
    layout.addWidget(Renderer3D(), stretch=1)

    return renderer_popout_window

def on_app_closing():
    if renderer_popout_window is not None:
        renderer_popout_window.close()

def sync_popout_window():
    settings = se.get_settings()

    want_open = (
        settings.get("enable visualizer", True)
        and settings.get("visualizer separate window", False)
    )

    win = _ensure_popout_window()

    if want_open:
        win.show()
        win.raise_()
        win.activateWindow()
    else:
        win.hide()


# ============================================================
# Runtime visibility callback
# ============================================================

_runtime_visibility_callback = None


def set_runtime_visibility_callback(callback):
    """
    Called by main.py when the plugin is loaded.

    This gives the plugin a callback into the REAL running
    main module without doing:

        import main

    which would create a second copy of main.py when the
    application was launched as __main__.
    """

    global _runtime_visibility_callback

    _runtime_visibility_callback = callback


def apply_runtime_visibility():
    """
    Tell main.py to update the UI immediately.
    """

    if _runtime_visibility_callback is not None:
        _runtime_visibility_callback()


# ============================================================
# Tab
# ============================================================

# Set inside tab() once the "visualizer separate window" checkbox is
# built, so _refresh_control_state() can update its enabled/checked
# state whenever "enable visualizer" changes elsewhere.
_separate_window_widget = None


def _refresh_control_state():
    """Keeps the 'visualizer separate window' checkbox in sync with
    'enable visualizer' -- disabled (and irrelevant) whenever the
    visualizer itself is off."""
    if _separate_window_widget is None:
        return

    cb = _separate_window_widget.findChild(QCheckBox)
    if cb is None:
        return

    settings = se.get_settings()
    enable_visualizer = settings.get("enable visualizer", True)

    cb.blockSignals(True)
    cb.setEnabled(enable_visualizer)
    cb.setChecked(settings.get("visualizer separate window", False))
    cb.blockSignals(False)


def tab() -> QWidget:
    global _separate_window_widget

    tab_main = QWidget()

    layout_main = QVBoxLayout(
        tab_main
    )

    # ========================================================
    # Visibility settings
    # ========================================================

    def toggle_visibility(
        key,
        check_widget,
    ):
        # Save the new setting.
        se.update_setting(
            key,
            check_widget.isChecked(),
        )

        if key == "enable visualizer":
            # Turning the visualizer off/on changes whether the
            # separate-window checkbox is even usable, and whether the
            # pop-out window should currently be open.
            _refresh_control_state()
            sync_popout_window()

        # Immediately update the REAL UI.
        apply_runtime_visibility()

    control = el.multitype(
        {
            "arr": [
                {
                    "type": "checkbox",
                    "text": "enable visualizer",
                    "default": se.get_settings()[
                        "enable visualizer"
                    ],
                    "func": (
                        lambda:
                        toggle_visibility(
                            "enable visualizer",
                            control.findChildren(
                                QCheckBox
                            )[0],
                        )
                    ),
                },
                {
                    "type": "checkbox",
                    "text": "enable tracker display",
                    "default": se.get_settings()[
                        "enable tracker display"
                    ],
                    "func": (
                        lambda:
                        toggle_visibility(
                            "enable tracker display",
                            control.findChildren(
                                QCheckBox
                            )[1],
                        )
                    ),
                },
            ]
        }
    )

    control_g = el.group(
        {
            "text": "control",
            "box": "h",
            "arr": [control],
        }
    )

    layout_main.addWidget(
        control_g
    )

    # ========================================================
    # Camera settings
    # ========================================================

    def toggle_camera():
        checkbox = camera.findChildren(
            QCheckBox
        )[0]

        se.update_setting(
            "attach cam",
            checkbox.isChecked(),
        )

    camera = el.multitype(
        {
            "arr": [
                {
                    "type": "checkbox",
                    "text": "attach camera to hmd",
                    "default": se.get_settings()[
                        "attach cam"
                    ],
                    "func": toggle_camera,
                }
            ]
        }
    )

    camera_g = el.group(
        {
            "text": "camera",
            "box": "h",
            "arr": [camera],
        }
    )

    layout_main.addWidget(
        camera_g
    )

    # ========================================================
    # Pop-out window toggle
    # ========================================================

    def toggle_separate_window():
        cb = _separate_window_widget.findChild(QCheckBox)
        if cb is None:
            return

        se.update_setting("visualizer separate window", cb.isChecked())

        sync_popout_window()
        apply_runtime_visibility()

    _separate_window_widget = el.checkbox({
        "text": "open in separate window",
        "default": se.get_settings().get("visualizer separate window", False),
        "enabled": se.get_settings().get("enable visualizer", True),
        "func": toggle_separate_window,
    })

    g_misc = el.group(
        {
            "text": "misc",
            "box": "h",
            "arr": [_separate_window_widget],
        }
    )

    layout_main.addWidget(g_misc)

    # Boot-time restore: main.py's generate_tabs() calls tab() for every
    # plugin up front (not lazily on first click), so this runs once at
    # startup and reopens the pop-out window if it was left open.
    sync_popout_window()

    # ========================================================
    # Return page
    # ========================================================

    return el.scroll(
        {
            "widget": tab_main
        }
    )