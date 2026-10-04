#main: creates the window and starts everything

import sys
import os
import importlib.util

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)
from PyQt6.QtCore import Qt

from PyQt6.QtGui import QIcon

import elements as el
import theme_registry
import settings as se
import sender as sd
import globals as gl

from visualizer import Renderer3D
from tracker_display import TrackerDisplay

import ctypes
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GlassVR.App")
except Exception:
    pass
app = QApplication(sys.argv)

window = None

main_vbox = None

nav_bar_container = None
nav_bar_layout = None

middle_container = None
middle_hbox = None

pages_widget = None
renderer = None

scroll_detected = None

loaded_plugin_modules = []

def apply_runtime_visibility():
    global renderer
    global scroll_detected

    if renderer is None or scroll_detected is None:
        return

    settings = se.get_settings()

    enable_visualizer = settings.get("enable visualizer", True)
    separate_window = settings.get("visualizer separate window", False)

    renderer.setVisible(enable_visualizer and not separate_window)

    scroll_detected.setVisible(settings.get("enable tracker display", True))

def get_base_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(
            os.path.abspath(__file__)
        )

    if base not in sys.path:
        sys.path.insert(0, base)

    return base

def generate_tabs():
    global pages_widget
    global nav_bar_layout
    global loaded_plugin_modules

    base_dir = get_base_dir()
    plugins_dir = os.path.join(base_dir,"plugins",)

    loaded_modules = []

    for plugin_folder in gl.get_plugin_folders(
        plugins_dir
    ):
        page_path = os.path.join(plugin_folder,"page.py",)

        if not os.path.isfile(page_path):
            continue

        folder_name = os.path.basename(plugin_folder)

        rel_path = os.path.relpath(plugin_folder,plugins_dir,)

        import_key = (
            rel_path
            .replace(os.sep, ".")
            .replace(" ", "_")
        )

        spec = importlib.util.spec_from_file_location(
            f"plugins.{import_key}.page",
            page_path,
        )

        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)

        sys.modules[spec.name] = module

        #lets the plugin use packages shipped in its own libs folder
        gl.add_plugin_libs(plugin_folder)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            #one broken plugin should not take the whole app down
            gl.log_plugin_error(folder_name, e)
            sys.modules.pop(spec.name, None)
            continue

        if hasattr(module, "page") or hasattr(
            module,
            "tab",
        ):
            priority = getattr(module,"priority",0,)

            loaded_modules.append((priority,folder_name,module,plugin_folder,))

    loaded_modules.sort(
        key=lambda x: (x[0], x[1])
    )

    loaded_plugin_modules = [module for (_priority, _folder_name, module, _plugin_folder) in loaded_modules]

    for (
        priority,
        folder_name,
        module,
        plugin_folder,
    ) in loaded_modules:

        if hasattr(
            module,
            "set_runtime_visibility_callback",
        ):
            module.set_runtime_visibility_callback(apply_runtime_visibility)

        page_widget = (
            module.page()
            if hasattr(module, "page")
            else module.tab()
        )

        title = getattr(module,"title",folder_name.upper())

        page_index = pages_widget.addWidget(page_widget)

        btn_data = {
            "text": title,
            "group": "widget",
            "func": (
                lambda idx=page_index:
                pages_widget.setCurrentIndex(idx)
            ),
        }

        for ext in ("png", "jpg", "jpeg", "gif"):
            icon_path = os.path.join(plugin_folder, f"icon.{ext}")
            if os.path.isfile(icon_path):
                btn_data["icon"] = icon_path
                break

        btn_widget = el.button(btn_data)

        nav_bar_layout.addWidget(btn_widget)

    nav_bar_layout.addStretch()

def build_ui():
    global window
    global main_vbox
    global nav_bar_container
    global nav_bar_layout
    global middle_container
    global middle_hbox
    global pages_widget
    global renderer
    global scroll_detected

    window = QWidget()
    window.setObjectName(theme_registry.MAIN_WINDOW_OBJECT_NAME)
    window.setWindowTitle("GlassVR")
    window.resize(1550,950,)

    main_vbox = QVBoxLayout(window)
    main_vbox.setContentsMargins(10,10,10,10,)
    main_vbox.setSpacing(10)

    nav_bar_container = QWidget()

    nav_bar_layout = QHBoxLayout(nav_bar_container)
    nav_bar_layout.setContentsMargins(0,0,0,0,)
    nav_bar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    middle_container = QWidget()

    middle_hbox = QHBoxLayout(middle_container)
    middle_hbox.setContentsMargins(0,0,0,0,)
    middle_hbox.setSpacing(10)

    pages_widget = QStackedWidget()

    renderer = Renderer3D()

    middle_hbox.addWidget(pages_widget,stretch=3,)
    middle_hbox.addWidget(renderer,stretch=1,)

    scroll_detected = TrackerDisplay()
    scroll_detected.setMinimumHeight(165)

    main_vbox.addWidget(nav_bar_container)
    main_vbox.addWidget(middle_container,stretch=1,)
    main_vbox.addWidget(scroll_detected)

def create_window():
    settings = se.get_settings()
    themes = theme_registry.discover_themes()

    saved_theme = settings.get("theme","default",)

    theme = themes.get(saved_theme)

    if theme is not None:
        theme_registry.apply_theme(theme)

    icon_path = os.path.join(get_base_dir(), "assets", ";Prism.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    build_ui()
    generate_tabs()
    apply_runtime_visibility()

    original_close_event = window.closeEvent

    def _handle_main_window_close(event):
        for module in loaded_plugin_modules:
            if hasattr(module, "on_app_closing"):
                try:
                    module.on_app_closing()
                except Exception:
                    pass
        original_close_event(event)

    window.closeEvent = _handle_main_window_close

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    sd.start_send_hmd()
    sd.start_send_controllers()
    sd.start_send_trackers()

    create_window()

#;P