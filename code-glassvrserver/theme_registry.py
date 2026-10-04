#themes!

import sys
import os
import json
import re
import weakref

from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtGui import QMovie, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QLabel

import globals as gl

MAIN_WINDOW_OBJECT_NAME = "main_window"

_bg_movie = None
_bg_filter = None

_visualizer_listeners = []
_current_visualizer_theme = {}

_theme_listeners = []
_current_theme = {}

def register_theme_listener(callback):
    if callback not in _theme_listeners:
        _theme_listeners.append(callback)

def unregister_theme_listener(callback):
    if callback in _theme_listeners:
        _theme_listeners.remove(callback)

def get_current_theme():
    return dict(_current_theme)

def find_theme_file(theme_data, basename, exts=("png", "jpg", "jpeg", "gif", "webp", "bmp")):
    folder = (theme_data or {}).get("_theme_folder")
    if not folder:
        return None
    for ext in exts:
        candidate = os.path.join(folder, f"{basename}.{ext}")
        if os.path.isfile(candidate):
            return candidate
    return None

def register_visualizer_listener(callback):
    if callback not in _visualizer_listeners:
        _visualizer_listeners.append(callback)

def unregister_visualizer_listener(callback):
    if callback in _visualizer_listeners:
        _visualizer_listeners.remove(callback)

def get_visualizer_theme():
    return dict(_current_visualizer_theme)

def _resolve_background_transform_mode(theme_data):
    filtering = str(theme_data.get("background filtering", "linear")).strip().lower()
    if filtering in ("near", "nearest"):
        return Qt.TransformationMode.FastTransformation
    return Qt.TransformationMode.SmoothTransformation

class BackgroundResizeFilter(QObject):

    def __init__(self, bg_label, movie=None, static_pixmap=None,
                 transform_mode=Qt.TransformationMode.SmoothTransformation, parent=None):
        super().__init__(parent)
        self.bg_label = bg_label
        self.movie = movie
        self.static_pixmap = static_pixmap
        self.transform_mode = transform_mode

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self.bg_label.setGeometry(0, 0, obj.width(), obj.height())
            self.update_frame()
        return super().eventFilter(obj, event)

    def update_frame(self):
        if not self.bg_label:
            return

        source_pixmap = None
        if self.movie and not self.movie.currentPixmap().isNull():
            source_pixmap = self.movie.currentPixmap()
        elif self.static_pixmap and not self.static_pixmap.isNull():
            source_pixmap = self.static_pixmap

        if source_pixmap is None:
            return

        scaled = source_pixmap.scaled(
            self.bg_label.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            self.transform_mode
        )
        self.bg_label.setPixmap(scaled)

def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def discover_themes():
    base_dir = _get_base_dir()
    plugins_dir = os.path.join(base_dir, "plugins")
    discovered = {}

    for plugin_folder in gl.get_plugin_folders(plugins_dir):
        json_path = os.path.join(plugin_folder, "theme.json")
        if not os.path.isfile(json_path):
            continue

        folder_name = os.path.basename(plugin_folder)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                theme_data = json.load(f)

            theme_data["_theme_folder"] = plugin_folder
            theme_title = theme_data.get("title", folder_name)
            discovered[theme_title] = theme_data
        except Exception as e:
            print(f"Failed to load theme from {json_path}: {e}")

    return discovered

def apply_theme(theme_data):
    global _bg_movie, _bg_filter, _current_visualizer_theme, _current_theme

    if not theme_data or not isinstance(theme_data, dict):
        return

    app = QApplication.instance()
    if app is None:
        return

    qss_rules = []

    qss_rules.append("""
        QScrollArea, QScrollArea > QWidget > QWidget {
            background: transparent;
            border: none;
        }
    """)

    if _bg_movie is not None:
        _bg_movie.stop()
        _bg_movie = None

    main_window = None
    for w in app.topLevelWidgets():
        if w.objectName() == MAIN_WINDOW_OBJECT_NAME:
            main_window = w
            break

    if _bg_filter is not None and main_window is not None:
        main_window.removeEventFilter(_bg_filter)
        _bg_filter = None

    bg_label = main_window.findChild(QLabel, "_theme_bg_label") if main_window else None

    theme_folder = theme_data.get("_theme_folder")
    bg_gif_path = os.path.join(theme_folder, "background.gif") if theme_folder else None

    static_bg_path = None
    if theme_folder:
        for ext in ["png", "jpg", "jpeg"]:
            candidate = os.path.join(theme_folder, f"background.{ext}")
            if os.path.isfile(candidate):
                static_bg_path = candidate
                break

    transform_mode = _resolve_background_transform_mode(theme_data)

    if bg_gif_path and os.path.isfile(bg_gif_path) and main_window:
        if not bg_label:
            bg_label = QLabel(main_window)
            bg_label.setObjectName("_theme_bg_label")
            bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            bg_label.lower()

        bg_label.setGeometry(0, 0, main_window.width(), main_window.height())
        bg_label.show()

        movie = QMovie(bg_gif_path)
        _bg_movie = movie

        bg_filter = BackgroundResizeFilter(bg_label, movie=movie, transform_mode=transform_mode, parent=main_window)
        _bg_filter = bg_filter
        main_window.installEventFilter(bg_filter)

        def handle_bg_frame_changed(frame_num):
            bg_filter.update_frame()

        movie.frameChanged.connect(handle_bg_frame_changed)
        movie.start()
    elif static_bg_path and os.path.isfile(static_bg_path) and main_window:
        if not bg_label:
            bg_label = QLabel(main_window)
            bg_label.setObjectName("_theme_bg_label")
            bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            bg_label.lower()

        bg_label.setGeometry(0, 0, main_window.width(), main_window.height())
        bg_label.show()

        static_pixmap = QPixmap(static_bg_path)

        bg_filter = BackgroundResizeFilter(bg_label, static_pixmap=static_pixmap, transform_mode=transform_mode, parent=main_window)
        _bg_filter = bg_filter
        main_window.installEventFilter(bg_filter)
        bg_filter.update_frame()
    else:
        if bg_label:
            bg_label.hide()

    groups = theme_data.get("groups", {})
    for group_key, raw_qss in groups.items():
        if not isinstance(raw_qss, str) or not raw_qss.strip():
            continue

        qss_str = raw_qss.strip()

        if ":" in group_key:
            group_base, pseudo_name = group_key.split(":", 1)
            pseudo_str = f":{pseudo_name}"
        else:
            group_base = group_key
            pseudo_str = ""

        group_name = group_base
        if pseudo_str:
            qss_rules.append(f"""
                QPushButton[group="{group_name}"]{pseudo_str},
                QComboBox[group="{group_name}"]{pseudo_str},
                QCheckBox[group="{group_name}"]{pseudo_str},
                QLineEdit[group="{group_name}"]{pseudo_str},
                QSpinBox[group="{group_name}"]{pseudo_str},
                QDoubleSpinBox[group="{group_name}"]{pseudo_str} {{
                    {qss_str}
                }}
            """)
        else:
            qss_rules.append(f"""
                QGroupBox[group="{group_name}"] {{
                    {qss_str}
                }}
                QGroupBox[group="{group_name}"]::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 3px;
                    background: transparent;
                }}
                QPushButton[group="{group_name}"],
                QComboBox[group="{group_name}"],
                QCheckBox[group="{group_name}"],
                QLineEdit[group="{group_name}"],
                QSpinBox[group="{group_name}"],
                QDoubleSpinBox[group="{group_name}"] {{
                    {qss_str}
                }}
                QLabel[group="{group_name}"] {{
                    {qss_str}
                    background: transparent;
                    border: none;
                }}
                QTabBar::tab[group="{group_name}"] {{
                    {qss_str}
                }}
            """)

    block_props = _parse_qss_props(groups.get("block", ""))
    title_color = None
    bm = _BORDER_RE.match(block_props.get("border", ""))
    if bm and bm.group(2).lower() != "none":
        title_color = bm.group(3)
    title_color = title_color or block_props.get("color")
    if title_color:
        qss_rules.append(f"""
            QGroupBox[group="block"]::title {{
                color: {title_color};
            }}
        """)

    app.setStyleSheet("\n".join(qss_rules))

    _current_visualizer_theme = theme_data.get("visualizer", {}) or {}
    for callback in list(_visualizer_listeners):
        try:
            callback(_current_visualizer_theme)
        except Exception as e:
            print(f"Visualizer theme listener failed: {e}")

    _current_theme = theme_data
    for callback in list(_theme_listeners):
        try:
            callback(theme_data)
        except Exception as e:
            print(f"Theme listener failed: {e}")

RAINBOW_BG_TINT = 0.45
RAINBOW_BORDER_TINT = 0.60

_block_widgets = weakref.WeakKeyDictionary()

_RGBA_RE = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+%?)\s*)?\)", re.I
)
_BORDER_RE = re.compile(r"^\s*(\d+(?:\.\d+)?px)\s+(\w+)\s+(.+?)\s*$")

def _parse_qss_props(qss):
    props = {}
    for chunk in (qss or "").split(";"):
        if ":" not in chunk:
            continue
        key, value = chunk.split(":", 1)
        props[key.strip().lower()] = value.strip()
    return props

def _parse_color(text, fallback=None):
    if not text:
        return fallback
    m = _RGBA_RE.match(text.strip())
    if m:
        r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
        a_raw = m.group(4)
        if a_raw is None:
            alpha = 1.0
        elif a_raw.endswith("%"):
            alpha = float(a_raw[:-1]) / 100.0
        else:
            alpha = float(a_raw)
            if alpha > 1.0:
                alpha /= 255.0
        return QColor(r, g, b), max(0.0, min(1.0, alpha))
    c = QColor(text.strip())
    if c.isValid():
        return QColor(c.red(), c.green(), c.blue()), c.alphaF()
    return fallback

def _mix(a, b, t):
    """t=0 -> a, t=1 -> b"""
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    )

def _rgba(color, alpha):
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.3f})"

def rainbow_blocks_enabled():
    return bool(_current_theme.get("rainbow blocks", False))

def _rainbow_block_qss(index):
    props = _parse_qss_props((_current_theme.get("groups") or {}).get("block", ""))

    hue = (index * 36) % 360
    rainbow_bg = QColor.fromHsv(hue, 40, 50)
    rainbow_border = QColor.fromHsv(hue, 120, 180)

    theme_bg, bg_alpha = _parse_color(props.get("background-color"), (QColor(0, 0, 0), 0.8))
    border_width, border_style, theme_border = "1px", "solid", QColor(255, 255, 255)

    bm = _BORDER_RE.match(props.get("border", ""))
    if bm and bm.group(2).lower() != "none":
        parsed = _parse_color(bm.group(3))
        if parsed:
            border_width, border_style, theme_border = bm.group(1), bm.group(2), parsed[0]

    bg = _mix(theme_bg, rainbow_bg, RAINBOW_BG_TINT)
    border = _mix(theme_border, rainbow_border, RAINBOW_BORDER_TINT)

    return f"""
        QGroupBox[rainbowblock="true"] {{
            background-color: {_rgba(bg, bg_alpha)};
            border: {border_width} {border_style} {border.name()};
        }}
        QGroupBox[rainbowblock="true"]::title {{
            color: {border.name()};
        }}
    """

def _apply_block_style(widget, index):
    try:
        rainbow = rainbow_blocks_enabled()
        widget.setProperty("group", "block")
        widget.setProperty("rainbowblock", "true" if rainbow else "false")
        widget.setStyleSheet(_rainbow_block_qss(index) if rainbow else "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
    except RuntimeError:
        _block_widgets.pop(widget, None)

def style_block(widget, index=0):
    _block_widgets[widget] = index
    _apply_block_style(widget, index)
    return widget

def _restyle_all_blocks(_theme_data=None):
    for widget, index in list(_block_widgets.items()):
        _apply_block_style(widget, index)

register_theme_listener(_restyle_all_blocks)