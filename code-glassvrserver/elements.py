#custom ui elements compatible with themes and other staff,
#avoid creating primative PyQt6 elements if possible for consistency, or rewrite the whole front end idc

#elements expect "data" arg like this

#usage:
#l = el.labe({"text":"hellow! ;P"})
#layout.AddWidget(l)

#plz see example plugin

import sys
import os
import re
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QTabWidget, QGridLayout, QCheckBox, QComboBox, QScrollArea,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QTimer, QEvent, QPoint, QRect
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QColor, QPalette, QMovie, QImageReader

import settings as se
import mode_registry
import mode_manager
import theme_registry
import controller_handler as ch
import steamvr as svr

import playspace as ps

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

IMAGE_EXT_PRIORITY = ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "tif", "ico"]

_supported_exts_cache = None
_missing_warned = set()

def _supported_image_exts():
    global _supported_exts_cache
    if _supported_exts_cache is None:
        _supported_exts_cache = {bytes(f).decode().lower() for f in QImageReader.supportedImageFormats()}
        _supported_exts_cache.update(IMAGE_EXT_PRIORITY)
    return _supported_exts_cache

def _ext_of(path):
    return os.path.splitext(path)[1].lower().lstrip(".")

def _find_by_stem(base):
    folder, stem = os.path.split(base)
    try:
        names = os.listdir(folder or ".")
    except OSError:
        return None

    exts = _supported_image_exts()
    best = None
    for n in names:
        s, e = os.path.splitext(n)
        e = e.lower().lstrip(".")
        if not stem or s.lower() != stem.lower() or e not in exts:
            continue
        full = os.path.join(folder, n)
        if not os.path.isfile(full):
            continue
        rank = IMAGE_EXT_PRIORITY.index(e) if e in IMAGE_EXT_PRIORITY else len(IMAGE_EXT_PRIORITY)
        key = (rank, n.lower())
        if best is None or key < best[0]:
            best = (key, full)
    return best[1] if best else None

def resolve_asset_path(path):
    if not path or not isinstance(path, str):
        return None
    path = path.strip()
    if not path:
        return None

    if os.path.isabs(path):
        bases = [path]
    else:
        bases = [os.path.join(APP_ROOT, path), os.path.abspath(path)]

    for base in bases:
        if os.path.isfile(base):
            return base
        if _ext_of(base) not in _supported_image_exts():
            found = _find_by_stem(base)
            if found:
                return found
    return None

def parse_filtering(value):
    v = str(value or "").strip().lower()
    if v in ("near", "nearest", "nearest neighbor", "nearest-neighbor", "nearest_neighbor", "neighbor", "point", "pixel"):
        return "nearest"
    return "linear"

def parse_tooltip_data(spec):
    if not spec:
        return "", [], "v"

    # String format: "tooltip": "text"
    if isinstance(spec, str):
        return spec, [], "v"

    # Dict format: "tooltip": {"text": "hi!", "image": "path", "box": "v"}
    if isinstance(spec, dict):
        text = spec.get("text")
        text_str = "" if text is None else str(text)

        box = spec.get("box", spec.get("tooltip box", "v"))

        img_spec = spec.get("image", spec.get("images", spec.get("path", spec.get("tooltip image"))))
        images = parse_tooltip_images(img_spec, {"filtering": spec.get("filtering")})

        return text_str, images, box

    # List format: "tooltip": ["text", {"image": "path"}] or [{}, {}]
    if isinstance(spec, (list, tuple)):
        combined_text = []
        combined_images = []
        box = "v"

        for item in spec:
            t, imgs, b = parse_tooltip_data(item)
            if t:
                combined_text.append(t)
            combined_images.extend(imgs)
            if b == "h":
                box = "h"

        return "\n".join(combined_text), combined_images, box

    return str(spec), [], "v"

def parse_tooltip_images(value, defaults=None):
    defaults = defaults or {}

    if not value:
        return []

    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            out.extend(parse_tooltip_images(v, defaults))
        return out

    if isinstance(value, dict):
        path = value.get("path") or value.get("file") or value.get("image") or value.get("source") or ""
        text = value.get("text")
        text = "" if text is None else str(text)

        by = value.get("by") or value.get("author") or value.get("credit") or ""
        by = "" if by is None else str(by)

        size = value.get("size")
        if not size and "width" in value and "height" in value:
            size = (value.get("width"), value.get("height"))

        filtering = parse_filtering(value.get("filtering", defaults.get("filtering")))

        nested_images = value.get("images")
        if nested_images:
            return parse_tooltip_images(nested_images, {"filtering": filtering})

        if not path and not text and not by:
            return []
        return [{"path": path, "text": text, "by": by, "size": size, "filtering": filtering}]

    if isinstance(value, str):
        if not value.strip():
            return []
        return [{"path": value, "text": "", "by": "", "size": None, "filtering": parse_filtering(defaults.get("filtering"))}]

    return []

class HoverTooltip(QLabel):
    #"v" (default)          "h"
    #[main text]            [main text] [text ][text ]
    #[text ]                            [image][image]
    #[image]                            [by   ][by   ]
    #[by   ]
    MAX_WIDTH = 320
    IMAGE_SCALE = 2.0
    IMAGE_MAX_WIDTH = 560
    IMAGE_MAX_HEIGHT = 480

    def __init__(self, tooltip_spec, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setProperty("group", "tooltip")

        self._inner_style = "background: transparent; border: none; padding: 0px; margin: 0px;"
        self._align = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft

        self._layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self._text_label = QLabel()
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(self._inner_style)
        self._text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._layout.addWidget(self._text_label, 0, self._align)

        self._cells = []
        self._movies = []
        self._tooltip_spec = None
        self._box = "v"

        self.set_spec(tooltip_spec)
        self.hide()

    def text(self):
        return self._text_label.text()

    def setText(self, text):
        self.set_spec(text)

    def set_spec(self, tooltip_spec):
        self._tooltip_spec = tooltip_spec
        text, images, box = parse_tooltip_data(tooltip_spec)

        self._text_label.setText(text)
        self._text_label.setVisible(bool(text))

        self._box = "h" if str(box).strip().lower().startswith("h") else "v"
        if self._box == "h":
            self._layout.setDirection(QBoxLayout.Direction.LeftToRight)
        else:
            self._layout.setDirection(QBoxLayout.Direction.TopToBottom)

        self._rebuild_images(images)

    def _rebuild_images(self, entries):
        for movie in self._movies:
            movie.stop()
        self._movies = []

        for cell, _size, _caption, _by in self._cells:
            self._layout.removeWidget(cell)
            cell.setParent(None)
            cell.deleteLater()
        self._cells = []

        for entry in entries:
            made = self._make_cell(entry)
            if made is None:
                continue
            self._layout.addWidget(made[0], 0, self._align)
            self._cells.append(made)

    def _display_size(self, native, target_size=None):
        if target_size and isinstance(target_size, (list, tuple)) and len(target_size) == 2:
            limit = QSize(target_size[0], target_size[1])
            size = native.scaled(limit, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            size = QSize(round(native.width() * self.IMAGE_SCALE), round(native.height() * self.IMAGE_SCALE))
            limit = QSize(self.IMAGE_MAX_WIDTH, self.IMAGE_MAX_HEIGHT)
            if size.width() > limit.width() or size.height() > limit.height():
                size = size.scaled(limit, Qt.AspectRatioMode.KeepAspectRatio)
        return QSize(max(size.width(), 1), max(size.height(), 1))

    def _make_image_label(self, resolved, target_size=None, filtering="linear"):
        nearest = (filtering == "nearest")
        reader = QImageReader(resolved)
        reader.setAutoTransform(True)
        native = reader.size()

        movie = None
        if reader.supportsAnimation():
            candidate = QMovie(resolved)
            if candidate.isValid() and candidate.frameCount() != 1:
                movie = candidate

        pixmap = None
        if not (native.isValid() and native.width() > 0 and native.height() > 0):
            if movie is not None:
                movie.jumpToFrame(0)
                native = movie.currentPixmap().size()
            else:
                pixmap = QPixmap(resolved)
                native = pixmap.size()
        if native.width() <= 0 or native.height() <= 0:
            return None, None

        size = self._display_size(native, target_size=target_size)

        label = QLabel()
        label.setStyleSheet(self._inner_style)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setAlignment(self._align)
        label.setFixedSize(size)

        if movie is not None and not nearest:
            movie.setParent(label)
            movie.setScaledSize(size)
            label.setMovie(movie)
            self._movies.append(movie)
        elif movie is not None:
            movie.setParent(label)
            frame_cache = {}

            def show_frame(frame_number, movie=movie, label=label, size=size, cache=frame_cache):
                frame = cache.get(frame_number)
                if frame is None:
                    frame = movie.currentPixmap().scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
                    cache[frame_number] = frame
                label.setPixmap(frame)

            movie.frameChanged.connect(show_frame)
            movie.jumpToFrame(0)
            show_frame(0)
            self._movies.append(movie)
        else:
            if pixmap is None:
                pixmap = QPixmap(resolved)
            if pixmap.isNull():
                return None, None
            mode = Qt.TransformationMode.FastTransformation if nearest else Qt.TransformationMode.SmoothTransformation
            label.setPixmap(pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, mode))

        return label, size

    def _make_cell(self, entry):
        path = entry.get("path") or ""
        caption = entry.get("text") or ""
        by_text = entry.get("by") or ""
        size_spec = entry.get("size")

        resolved = resolve_asset_path(path) if path else None
        if path and resolved is None and path not in _missing_warned:
            _missing_warned.add(path)
            print(f"[elements] tooltip image not found: {path}")

        image_label, size = (None, None)
        if resolved is not None:
            image_label, size = self._make_image_label(resolved, target_size=size_spec, filtering=entry.get("filtering", "linear"))

        if image_label is None and not caption and not by_text:
            return None

        cell = QWidget()
        cell.setStyleSheet(self._inner_style)
        cell.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(4)

        caption_label = None
        if caption:
            caption_label = QLabel(caption)
            caption_label.setWordWrap(True)
            caption_label.setStyleSheet(self._inner_style)
            caption_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            cell_layout.addWidget(caption_label, 0, self._align)

        if image_label is not None:
            cell_layout.addWidget(image_label, 0, self._align)

        by_label = None
        if by_text:
            by_label = QLabel(f"{by_text}" if not by_text.lower().startswith("by") else by_text)
            by_label.setWordWrap(True)
            by_label.setStyleSheet(self._inner_style)
            by_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            cell_layout.addWidget(by_label, 0, self._align)

        return cell, size, caption_label, by_label

    def _natural_width(self, label):
        label.ensurePolished()
        fm = label.fontMetrics()
        plain = label.text()
        if label.textFormat() != Qt.TextFormat.PlainText:
            plain = re.sub(r"<[^>]*>", "", plain.replace("<br>", "\n").replace("<br/>", "\n"))
        return max((fm.horizontalAdvance(line) for line in plain.split("\n")), default=0) + 2

    def _fit_width(self):
        self.ensurePolished()
        margins = self.contentsMargins()
        max_text = max(60, self.MAX_WIDTH - margins.left() - margins.right())

        widest_cell = 0
        for _cell, size, caption, by in self._cells:
            image_w = size.width() if size is not None else 0
            caption_w = min(self._natural_width(caption), max_text) if caption is not None else 0
            by_w = min(self._natural_width(by), max_text) if by is not None else 0

            cell_w = max(image_w, caption_w, by_w, 1)
            if caption is not None:
                caption.setFixedWidth(cell_w)
            if by is not None:
                by.setFixedWidth(cell_w)

            widest_cell = max(widest_cell, cell_w)

        if self._text_label.isVisibleTo(self):
            text_w = min(self._natural_width(self._text_label), max_text)
            if self._box == "v":
                text_w = max(text_w, widest_cell)
            self._text_label.setFixedWidth(max(text_w, 1))

    def show_for_widget(self, widget):
        for movie in self._movies:
            movie.start()

        self._fit_width()
        self._layout.activate()
        self.adjustSize()
        tip_size = self.size()

        widget_top_left = widget.mapToGlobal(QPoint(0, 0))
        widget_rect_global = QRect(widget_top_left, widget.size())

        screen = widget.screen() if hasattr(widget, "screen") else None
        if screen is not None:
            screen_geo = screen.availableGeometry()
        else:
            screen_geo = QApplication.primaryScreen().availableGeometry()

        gap = 6

        below_y = widget_rect_global.bottom() + gap
        above_y = widget_rect_global.top() - tip_size.height() - gap

        if below_y + tip_size.height() <= screen_geo.bottom():
            y = below_y
        elif above_y >= screen_geo.top():
            y = above_y
        else:
            y = below_y if (screen_geo.bottom() - below_y) >= (above_y - screen_geo.top()) else above_y

        x = widget_rect_global.left()
        if x + tip_size.width() > screen_geo.right():
            x = screen_geo.right() - tip_size.width()
        if x < screen_geo.left():
            x = screen_geo.left()

        self.move(x, y)
        self.show()
        self.raise_()

    def hideEvent(self, event):
        for movie in self._movies:
            movie.stop()
        super().hideEvent(event)

def attach_tooltip(widget, tooltip_spec):
    existing_tip = getattr(widget, "_hover_tip", None)
    if existing_tip is not None:
        existing_tip.set_spec(tooltip_spec)
        return

    tip = HoverTooltip(tooltip_spec, parent=widget)
    widget._hover_tip = tip

    widget.destroyed.connect(tip.close)

    original_enter = widget.enterEvent
    original_leave = widget.leaveEvent

    def enterEvent(event):
        tip.show_for_widget(widget)
        if original_enter:
            original_enter(event)

    def leaveEvent(event):
        tip.hide()
        if original_leave:
            original_leave(event)

    widget.enterEvent = enterEvent
    widget.leaveEvent = leaveEvent

def has_tooltip(data):
    return "tooltip" in data or "tooltip image" in data or "tooltip box" in data

def without_tooltip(data):
    return {k: v for k, v in data.items() if k not in ("tooltip", "tooltip image", "tooltip box")}

def attach_data_tooltip(data, *widgets):
    if not isinstance(data, dict) or not has_tooltip(data):
        return

    spec = data.get("tooltip")
    if spec is None:
        spec = {
            "image": data.get("tooltip image"),
            "box": data.get("tooltip box", "v")
        }

    for w in widgets:
        w.setToolTip("")
        attach_tooltip(w, spec)


def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


def reorder_group(data=None):
    if data is None:
        return

    widget = data.get("widget")
    order = data.get("order", [])
    last = data.get("last")

    if widget is None:
        return

    layout = widget.layout()
    if layout is None:
        return

    full_order = list(order)
    if last is not None:
        full_order.append(last)

    for w in full_order:
        layout.removeWidget(w)
        layout.addWidget(w)


def group(data=None):
    if data is None:
        data = {"text": "Group", "arr": [], "box": "v", "group": "group", "alignment" : Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter}

    cg = data.get("group", "group")
    title_text = data.get("text", data.get("name", ""))
    box_type = data.get("box", "v")
    items = data.get("arr", [])
    alignment_data = data.get("alignment", None)

    group_widget = QGroupBox(title_text)

    if box_type == "h":
        layout = QHBoxLayout(group_widget)
    else:
        layout = QVBoxLayout(group_widget)

    type_map = {
        "label": label,
        "button": button,
        "checkbox": checkbox,
        "spinbox": spinbox,
        "doublespinbox": doublespinbox,
        "image": image,
        "combobox": combobox,
        "lineedit": lineedit,
        "multitype": multitype,
        "hook": hook,
    }

    for item in items:
        if isinstance(item, QWidget):
            if alignment_data != None:
                layout.addWidget(item, alignment = alignment_data)
            else:
                layout.addWidget(item)
        elif isinstance(item, dict):
            if "group" not in item:
                item["group"] = "widget"
            item_type = item.get("type", "").lower()
            if item_type in type_map:
                if alignment_data != None:
                    layout.addWidget(type_map[item_type](item), alignment = alignment_data)
                else:
                    layout.addWidget(type_map[item_type](item))

    attach_data_tooltip(data, group_widget)

    group_widget.setProperty("group", cg)
    return group_widget

def scroll(data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(data.get("resizable", True))

    if "widget" in data:
        scroll_area.setWidget(data["widget"])

    scroll_area.setProperty("group", cg)
    return scroll_area


def tab(data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    tabs_widget = QTabWidget()
    if data.get("movable", True):
        tabs_widget.setMovable(True)

    tabs_widget.setProperty("group", cg)
    return tabs_widget

def image(data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)
    group_layout.setContentsMargins(0, 0, 0, 0)

    img_label = QLabel()
    img_label.setAlignment(data.get("alignment", Qt.AlignmentFlag.AlignCenter))
    img_label.setProperty("group", cg)

    path = data.get("path") or data.get("file") or data.get("image") or data.get("source") or ""
    size = data.get("size")
    width = data.get("width")
    height = data.get("height")

    target_w, target_h = None, None
    if size and isinstance(size, (list, tuple)) and len(size) == 2:
        target_w, target_h = size[0], size[1]
    elif width is not None and height is not None:
        target_w, target_h = width, height

    aspect_mode = data.get("aspect_ratio", Qt.AspectRatioMode.KeepAspectRatio)

    filter_type = data.get("filtering", "linear")
    if filter_type == "nearest" or filter_type == "near":
        transform_mode = Qt.TransformationMode.FastTransformation
    else:
        transform_mode = data.get("transform_mode", Qt.TransformationMode.SmoothTransformation)

    resolved_path = resolve_asset_path(path) if path else None

    if resolved_path and os.path.isfile(resolved_path):
        if resolved_path.lower().endswith(".gif"):
            movie = QMovie(resolved_path)
            movie.setParent(img_label)
            img_label.movie_ref = movie
            if target_w and target_h:
                def handle_frame_changed(frame_number):
                    try:
                        current_pixmap = movie.currentPixmap()
                        if not current_pixmap.isNull():
                            img_label.setPixmap(current_pixmap.scaled(target_w, target_h, aspect_mode, transform_mode))
                    except RuntimeError:
                        movie.stop()
                movie.frameChanged.connect(handle_frame_changed)
            else:
                img_label.setMovie(movie)
            movie.start()
        else:
            pixmap = QPixmap(resolved_path)
            if target_w and target_h and not pixmap.isNull():
                pixmap = pixmap.scaled(target_w, target_h, aspect_mode, transform_mode)
            img_label.setPixmap(pixmap)

    attach_data_tooltip(data, img_label)

    group_layout.addWidget(img_label)
    return group_widget

def button(data=None):
    if data is None:
        data = {"text": "button", "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)
    group_layout.setContentsMargins(0, 0, 0, 0)

    btn = QPushButton(data.get("text", ""))
    btn.setProperty("group", cg)

    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    filter_type = data.get("filtering", "linear")
    transform_mode = (
        Qt.TransformationMode.FastTransformation
        if filter_type == "nearest"
        else Qt.TransformationMode.SmoothTransformation
    )

    icon_size = None
    if "icon_size" in data and data["icon_size"]:
        size = data["icon_size"]
        if isinstance(size, (tuple, list)) and len(size) == 2:
            icon_size = QSize(size[0], size[1])
        elif isinstance(size, QSize):
            icon_size = size
        btn.setIconSize(icon_size)

    if "icon" in data and data["icon"]:
        icon_val = data["icon"]
        resolved_icon = resolve_asset_path(icon_val) if isinstance(icon_val, str) else None
        
        if resolved_icon and os.path.isfile(resolved_icon):
            if resolved_icon.lower().endswith(".gif"):
                movie = QMovie(resolved_icon)
                btn.movie_ref = movie
                
                def update_icon(frame_number):
                    current_pixmap = movie.currentPixmap()
                    if not current_pixmap.isNull():
                        if icon_size:
                            scaled = current_pixmap.scaled(
                                icon_size,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                transform_mode
                            )
                            btn.setIcon(QIcon(scaled))
                        else:
                            btn.setIcon(QIcon(current_pixmap))

                movie.frameChanged.connect(update_icon)
                movie.start()
            else:
                pixmap = QPixmap(resolved_icon)
                if icon_size and not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        icon_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        transform_mode
                    )
                btn.setIcon(QIcon(pixmap))
        elif isinstance(icon_val, QIcon):
            btn.setIcon(icon_val)

    if "func" in data and callable(data["func"]):
        btn.clicked.connect(lambda checked=False: data["func"]())

    btn.setEnabled(data.get("enabled", True))

    attach_data_tooltip(data, btn)

    group_layout.addWidget(btn)
    return group_widget

VK_ESCAPE = 0x1B

def capture_button(data=None):
    if data is None:
        data = {"text": "Capture Mouse", "group": "widget"}

    cg = data.get("group", "widget")
    base_text = data.get("text", "Capture Mouse")
    captured_text = data.get("captured_text", "Press ESC to release")

    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)
    group_layout.setContentsMargins(0, 0, 0, 0)

    btn = QPushButton(base_text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setProperty("group", cg)
    btn.setEnabled(data.get("enabled", True))

    state = {"captured": False, "esc_was_down": False}

    esc_timer = QTimer(btn)
    esc_timer.setInterval(30)

    def poll_escape():
        down = ch.is_key_pressed_globally(VK_ESCAPE)
        if down and not state["esc_was_down"]:
            exit_capture()
        state["esc_was_down"] = down

    esc_timer.timeout.connect(poll_escape)

    def enter_capture():
        if state["captured"]:
            return
        state["captured"] = True
        ch.set_mouse_capture(True)
        btn.setText(captured_text)
        state["esc_was_down"] = ch.is_key_pressed_globally(VK_ESCAPE)
        esc_timer.start()
        if "func" in data and callable(data["func"]):
            data["func"](True)

    def exit_capture():
        if not state["captured"]:
            return
        state["captured"] = False
        esc_timer.stop()
        ch.set_mouse_capture(False)
        btn.setText(base_text)
        if "func" in data and callable(data["func"]):
            data["func"](False)

    def on_clicked():
        if not state["captured"]:
            enter_capture()

    btn.clicked.connect(on_clicked)

    btn.destroyed.connect(lambda: exit_capture() if state["captured"] else None)

    attach_data_tooltip(data, btn)

    group_layout.addWidget(btn)
    return group_widget

def label(data=None):
    #custom labe:
    #text/alignment/tooltip

    if data is None:
        data = {"text": "label", "group": "label"}

    #"group" is for themes and visuals, for consistency avoid changing, only if doing something special
    cg = data.get("group", "label")
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    lbl = QLabel(data.get("text", ""))
    lbl.setAlignment(data.get("alignment", Qt.AlignmentFlag.AlignCenter))
    lbl.setProperty("group", cg)

    lbl.setOpenExternalLinks(True)
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

    palette = lbl.palette()
    palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    lbl.setPalette(palette)

    attach_data_tooltip(data, lbl)

    group_layout.addWidget(lbl)
    return group_widget

def spinbox(data=None):
    #custom spinbox:
    #text/default/min/max/steps/enabled/func: lambda value: /tooltip

    if data is None:
        data = {"text": "spinbox", "min": 0, "max": 100, "default": 0, "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    label_data = {**without_tooltip(data), "group": "label"}
    lbl = label(label_data)
    group_layout.addWidget(lbl)

    sb = QSpinBox()
    sb.setRange(data.get("min", 0), data.get("max", 100))
    sb.setValue(data.get("default", data.get("value", 0)))
    sb.setSingleStep(data.get("steps", data.get("step", 1)))
    sb.setEnabled(data.get("enabled", True))
    sb.setProperty("group", cg)

    if "func" in data and callable(data["func"]):
        callback = data["func"]
        sig = inspect.signature(callback)
        params = sig.parameters

        if len(params) == 0:
            sb.valueChanged.connect(lambda val: callback())
        else:
            sb.valueChanged.connect(lambda val: callback(val))

    attach_data_tooltip(data, group_widget)

    group_layout.addWidget(sb)
    return group_widget


def doublespinbox(data=None):
    #custom doublespinbox same as spinbox for supports floats:
    #text/default/min/max/steps/enabled/decimals/func: lambda value: /tooltip
    if data is None:
        data = {"text": "doublespinbox", "min": 0.0, "max": 100.0, "default": 0.0, "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    label_data = {**without_tooltip(data), "group": "label"}
    lbl = label(label_data)
    group_layout.addWidget(lbl)

    sb = QDoubleSpinBox()
    sb.setRange(data.get("min", 0.0), data.get("max", 100.0))
    sb.setValue(data.get("default", data.get("value", 0.0)))
    sb.setSingleStep(data.get("steps", data.get("step", 1.0)))
    sb.setDecimals(data.get("decimals", 3))
    sb.setEnabled(data.get("enabled", True))
    sb.setProperty("group", cg)

    if "func" in data and callable(data["func"]):
        callback = data["func"]
        sig = inspect.signature(callback)
        params = sig.parameters

        if len(params) == 0:
            sb.valueChanged.connect(lambda val: callback())
        else:
            sb.valueChanged.connect(lambda val: callback(val))

    attach_data_tooltip(data, group_widget)

    group_layout.addWidget(sb)
    return group_widget

def checkbox(data=None):
    #custom checkbox:
    #text/enabled/default/func: lambda value: /tooltip
    if data is None:
        data = {"text": "checkbox", "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    label_data = {**without_tooltip(data), "group": "label"}
    lbl = label(label_data)
    group_layout.addWidget(lbl)

    cb = QCheckBox()
    cb.setChecked(data.get("default", data.get("checked", False)))
    cb.setEnabled(data.get("enabled", True))
    cb.setProperty("group", cg)

    if "func" in data and callable(data["func"]):
        callback = data["func"]
        sig = inspect.signature(callback)
        params = sig.parameters

        if len(params) == 0:
            cb.toggled.connect(lambda state: callback())
        else:
            cb.toggled.connect(lambda state: callback(state))

    attach_data_tooltip(data, group_widget)

    group_layout.addWidget(cb)
    return group_widget

def lineedit(data=None):
    #custom lineedit:
    #text/enabled/default/placeholder/func: lambda value: /tooltip
    if data is None:
        data = {"text": "lineedit", "default": "", "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    label_data = {**without_tooltip(data), "group": "label"}
    lbl = label(label_data)
    group_layout.addWidget(lbl)

    le = QLineEdit()
    le.setText(data.get("default", ""))
    le.setEnabled(data.get("enabled", True))
    le.setProperty("group", cg)

    if "placeholder" in data:
        le.setPlaceholderText(data["placeholder"])

    if "func" in data and callable(data["func"]):
        callback = data["func"]
        
        sig = inspect.signature(callback)
        params = sig.parameters
        
        if len(params) == 0:
            le.textChanged.connect(lambda value: callback())
        else:
            le.textChanged.connect(lambda value: callback(value))

    attach_data_tooltip(data, group_widget)

    group_layout.addWidget(le)
    return group_widget


def combobox(data=None):
    if data is None:
        data = {"text": "combobox", "group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    label_data = {**without_tooltip(data), "group": "label"}
    lbl = label(label_data)
    group_layout.addWidget(lbl)

    combo = QComboBox()
    combo.addItems(data.get("items", []))
    combo.setCurrentText(data.get("default", ""))
    combo.setProperty("group", cg)

    #runs on selected
    if "index change" in data:
        combo.currentIndexChanged.connect(lambda: data["index change"]())

    #runs when opened
    if "pre show" in data:
        def wrapped_popup():
            data["pre show"](combo)
            QComboBox.showPopup(combo)
        combo.showPopup = wrapped_popup

    attach_data_tooltip(data, group_widget)

    group_layout.addWidget(combo)
    return group_widget


def modes(device="hmd", data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")

    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    stack_widget = QWidget()
    stack_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    stack_layout = QVBoxLayout(stack_widget)
    stack_layout.setContentsMargins(0, 0, 0, 0)

    both_container = QWidget()
    both_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    both_layout = QVBoxLayout(both_container)
    both_layout.setContentsMargins(0, 0, 0, 0)

    active_module_by_slot = {"pos": None, "rot": None}

    def refresh_both():
        clear_layout(both_layout)

        seen_ids = set()
        for module in active_module_by_slot.values():
            if module is None or not hasattr(module, "both_mode"):
                continue
            if id(module) in seen_ids:
                continue
            seen_ids.add(id(module))
            both_layout.addWidget(module.both_mode())

    def on_pos_module_change(module):
        active_module_by_slot["pos"] = module
        refresh_both()

    def on_rot_module_change(module):
        active_module_by_slot["rot"] = module
        refresh_both()

    stack_layout.addWidget(modes_sub(device, "pos", data, on_module_change=on_pos_module_change))
    stack_layout.addWidget(modes_sub(device, "rot", data, on_module_change=on_rot_module_change))

    group_layout.addWidget(stack_widget)
    group_layout.addWidget(both_container)

    return group_widget


def modes_sub(device, type_name, data=None, on_module_change=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    settings = se.get_settings()
    all_modules_by_title = mode_registry.discover_modes()

    modules_by_title = {
        title: module
        for title, module in all_modules_by_title.items()
        if mode_registry.device_matches(device, getattr(module, f"{type_name}_devices", []))
    }
    mode_titles = list(modules_by_title.keys())

    current_value = settings.get(f"{device}{type_name} mode", "")
    if current_value not in modules_by_title and mode_titles:
        current_value = mode_titles[0]

    content_area = QWidget()
    content_layout = QVBoxLayout(content_area)
    active_module = {"current": None}

    def refresh_content(selected_title):
        clear_layout(content_layout)
        module = modules_by_title.get(selected_title)

        if active_module["current"] is not module:
            mode_manager.release(active_module["current"], device, type_name)
            mode_manager.acquire(module, device, type_name)
            active_module["current"] = module

        if callable(on_module_change):
            on_module_change(module)

        if module is None:
            return

        module.device = device
        module.mode = type_name

        if type_name == "pos" and hasattr(module, "pos_mode"):
            content_layout.addWidget(module.pos_mode())
        elif type_name == "rot" and hasattr(module, "rot_mode"):
            content_layout.addWidget(module.rot_mode())

    def on_index_change():
        selected = combo.findChildren(QComboBox)[0].currentText()
        se.update_setting(f"{device}{type_name} mode", selected)
        refresh_content(selected)

    combo = combobox({
        "text": f"{device} {'position' if type_name == 'pos' else 'rotation'} module",
        "default": current_value,
        "items": mode_titles,
        "index change": on_index_change,
        "group": cg,
    })

    group_layout.addWidget(combo)
    group_layout.addWidget(content_area)

    refresh_content(current_value)
    return group_widget


def theme_selector(data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QHBoxLayout(group_widget)

    settings = se.get_settings()
    themes_by_title = theme_registry.discover_themes()
    theme_titles = list(themes_by_title.keys())

    current_value = settings.get("theme", "default")
    if current_value not in themes_by_title and theme_titles:
        current_value = theme_titles[0]

    def on_index_change():
        selected = combo.findChildren(QComboBox)[0].currentText()
        se.update_setting("theme", selected)
        theme_registry.apply_theme(themes_by_title.get(selected))

    combo = combobox({
        "text": "theme",
        "default": current_value,
        "items": theme_titles,
        "index change": on_index_change,
        "group": cg,
    })

    group_layout.addWidget(combo)

    theme_registry.apply_theme(themes_by_title.get(current_value))
    return group_widget


def theme_info(data=None):
    if data is None:
        data = {}

    cg = data.get("group", "group")
    icon_size = data.get("icon_size", (128, 128))
    spacing = data.get("spacing", 16)

    def make_label():
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        lbl.setProperty("group", "label")
        return lbl

    title_lbl = make_label()
    author_lbl = make_label()
    desc_lbl = make_label()

    text_widget = QWidget()
    text_layout = QVBoxLayout(text_widget)
    text_layout.setContentsMargins(0, 0, 0, 0)
    text_layout.setSpacing(spacing)
    text_layout.addStretch(1)
    text_layout.addWidget(title_lbl)
    text_layout.addWidget(author_lbl)
    text_layout.addWidget(desc_lbl)
    text_layout.addStretch(1)

    icon_holder = QWidget()
    icon_layout = QHBoxLayout(icon_holder)
    icon_layout.setContentsMargins(0, 0, 0, 0)

    def update(theme_data):
        if not theme_data:
            return

        title_lbl.setText(f"TITLE:\n{theme_data.get('title', 'untitled')}")
        author_lbl.setText(f"AUTHOR:\n{theme_data.get('author', 'unknown')}")
        desc_lbl.setText(f"DESCRIPTION:\n{theme_data.get('description', ';P')}")

        clear_layout(icon_layout)

        icon_path = theme_registry.find_theme_file(theme_data, "icon")
        if icon_path:
            filtering = str(theme_data.get("icon filtering", theme_data.get("background filtering", "linear"))).strip().lower()
            icon_layout.addWidget(image({
                "path": icon_path,
                "size": icon_size,
                "filtering": "nearest" if filtering in ("near", "nearest") else "linear",
                "group": "label",
            }))

    info_box = group({
        "text": data.get("text", "info"),
        "box": "h",
        "group": cg,
        "arr": [text_widget, icon_holder],
    })

    theme_registry.register_theme_listener(update)
    info_box.destroyed.connect(lambda *_: theme_registry.unregister_theme_listener(update))

    current = theme_registry.get_current_theme()
    if current:
        update(current)

    return info_box


def multitype(data=None):
    if data is None:
        data = {"arr": [], "box": "h", "group": "widget"}

    cg = data.get("group", "widget")
    box_type = data.get("box", "h")
    items = data.get("arr", [])

    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    if box_type == "h":
        group_layout = QHBoxLayout(group_widget)
    else:
        group_layout = QVBoxLayout(group_widget)

    group_layout.setContentsMargins(0, 0, 0, 0)

    type_map = {
        "label": label,
        "button": button,
        "checkbox": checkbox,
        "spinbox": spinbox,
        "doublespinbox": doublespinbox,
        "image": image,
        "combobox": combobox,
        "lineedit": lineedit,
        "hook": hook,
    }

    for item in items:
        if isinstance(item, QWidget):
            group_layout.addWidget(item)
        elif isinstance(item, dict):
            item_type = item.get("type", "").lower()
            if item_type in type_map:
                if "group" not in item:
                    item["group"] = cg
                group_layout.addWidget(type_map[item_type](item))

    attach_data_tooltip(data, group_widget)

    group_widget.setProperty("group", cg)
    return group_widget

_hook_block_counter = 0


def hook(data=None):
    if data is None:
        data = {"entry": {}, "group": "widget"}

    cg = data.get("group", "widget")
    entry = data.get("entry", {})
    on_change = data.get("on_change")
    on_delete = data.get("on_delete")

    NONE_LABEL = "pass"

    row_widget = QWidget()
    row_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    row_layout = QHBoxLayout(row_widget)

    def _notify_change():
        if callable(on_change):
            on_change()

    def _live_serials():
        return list(svr.get_trackers_dict())

    def _serial_items_preserving(saved):
        live = _live_serials()
        if saved and saved not in live:
            return [saved] + live
        return live

    serial_widget = combobox({
        "text": "serial",
        "default": entry.get("serial", ""),
        "items": _serial_items_preserving(entry.get("serial", "")),
        "group": cg,
        "index change": lambda: (
            entry.update({"serial": serial_widget.findChild(QComboBox).currentText()}),
            _notify_change(),
        ),
        "pre show": lambda cb: (
            saved := entry.get("serial", ""),
            val := cb.currentText(),
            cb.clear(),
            cb.addItems(_serial_items_preserving(saved)),
            cb.setCurrentText(val),
            None
        )[-1],
    })
    row_layout.addWidget(serial_widget)

    disable_widget = checkbox({
        "text": "disable",
        "default": bool(entry.get("disable", False)),
        "group": cg,
        "func": lambda: (
            entry.update({"disable": disable_widget.findChild(QCheckBox).isChecked()}),
            _notify_change(),
        ),
    })
    row_layout.addWidget(disable_widget)

    model_visible_widget = checkbox({
        "text": "model visible",
        "default": bool(entry.get("model visible", True)),
        "group": cg,
        "func": lambda: (
            entry.update({"model visible": model_visible_widget.findChild(QCheckBox).isChecked()}),
            _notify_change(),
        ),
    })
    row_layout.addWidget(model_visible_widget)

    def _override_items_preserving(saved_display):
        live = _live_serials()
        if saved_display != NONE_LABEL and saved_display not in live:
            return [NONE_LABEL, saved_display] + live
        return [NONE_LABEL] + live

    def _override_saved_display():
        raw = entry.get("override tracking serial", "")
        return raw if raw else NONE_LABEL

    override_serial_widget = combobox({
        "text": "override tracking serial",
        "default": _override_saved_display(),
        "items": _override_items_preserving(_override_saved_display()),
        "group": cg,
        "index change": lambda: (
            entry.update({
                "override tracking serial": (
                    "" if override_serial_widget.findChild(QComboBox).currentText() == NONE_LABEL
                    else override_serial_widget.findChild(QComboBox).currentText()
                )
            }),
            _notify_change(),
        ),
        "pre show": lambda cb: (
            saved := _override_saved_display(),
            val := cb.currentText(),
            cb.clear(),
            cb.addItems(_override_items_preserving(saved)),
            cb.setCurrentText(val),
            None
        )[-1],
    })
    row_layout.addWidget(override_serial_widget)

    role_widget = combobox({
        "text": "override role",
        "items": ["pass", "left", "right", "optout"],
        "default": entry.get("override role", "pass") or "pass",
        "group": cg,
        "tooltip": "'pass' leaves the device's controller role hint alone. "
                   "'left'/'right' assigns that hand; 'optout' keeps the "
                   "device tracking without claiming either hand -- handy "
                   "when you have more than two controllers active.",
        "index change": lambda: (
            entry.update({"override role": role_widget.findChild(QComboBox).currentText()}),
            _notify_change(),
        ),
    })
    row_layout.addWidget(role_widget)

    delete_widget = button({
        "text": "delete",
        "group": cg,
        "func": lambda: on_delete() if callable(on_delete) else None,
    })
    row_layout.addWidget(delete_widget)

    row_widget.setProperty("group", cg)
    row_widget._entry = entry

    row_g = group({
        "text": " ",
        "box": "v",
        "group": "block",
        "arr": [
            row_widget
        ]
    })

    # block index drives the rainbow hue; pass data["index"] for stable colors,
    # otherwise hooks get consecutive hues in creation order
    global _hook_block_counter
    block_index = data.get("index")
    if block_index is None:
        block_index = _hook_block_counter
        _hook_block_counter += 1
    theme_registry.style_block(row_g, block_index)

    return row_g

offsets_ui_dict = {}

def offsets(device):
    settings = se.get_settings()

    world = multitype({"box": "h", "arr": [
        {
            "type": "doublespinbox", "text": "X",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world x", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world x", world.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type": "doublespinbox", "text": "Y",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world y", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world y", world.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type": "doublespinbox", "text": "Z",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world z", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world z", world.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type": "doublespinbox", "text": "Yaw",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world yaw", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world yaw", world.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type": "doublespinbox", "text": "Pitch",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world pitch", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world pitch", world.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type": "doublespinbox", "text": "Roll",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset world roll", 0.0),
            "func": lambda: se.update_setting(f"{device} offset world roll", world.findChildren(QDoubleSpinBox)[5].value())
        }
    ]})

    world_keys = ["x", "y", "z", "yaw", "pitch", "roll"]
    for sb, k in zip(world.findChildren(QDoubleSpinBox), world_keys):
        sb._setting_key = f"{device} offset world {k}"

    local = multitype({"box": "h", "arr": [
        {
            "type": "doublespinbox", "text": "X",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local x", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local x", local.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type": "doublespinbox", "text": "Y",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local y", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local y", local.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type": "doublespinbox", "text": "Z",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local z", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local z", local.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type": "doublespinbox", "text": "Yaw",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local yaw", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local yaw", local.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type": "doublespinbox", "text": "Pitch",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local pitch", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local pitch", local.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type": "doublespinbox", "text": "Roll",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} offset local roll", 0.0),
            "func": lambda: se.update_setting(f"{device} offset local roll", local.findChildren(QDoubleSpinBox)[5].value())
        }
    ]})

    for sb, k in zip(local.findChildren(QDoubleSpinBox), world_keys):
        sb._setting_key = f"{device} offset local {k}"

    reset_method = combobox({
        "text": "Reset Source",
        "default": settings.get(f"{device} playspace reset method", "Headset"),
        "items": ["Headset", "Fixed Position"],
        "index change": lambda: se.update_setting(
            f"{device} playspace reset method",
            reset_method.findChildren(QComboBox)[0].currentText()
        )
    })
    reset_method.findChildren(QComboBox)[0]._setting_key = f"{device} playspace reset method"

    playspace = multitype({"box": "h", "arr": [
        {
            "type": "doublespinbox", "text": "X",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} playspace x", 0.0),
            "func": lambda: se.update_setting(f"{device} playspace x", playspace.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type": "doublespinbox", "text": "Y",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} playspace y", 0.0),
            "func": lambda: se.update_setting(f"{device} playspace y", playspace.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type": "doublespinbox", "text": "Z",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} playspace z", 0.0),
            "func": lambda: se.update_setting(f"{device} playspace z", playspace.findChildren(QDoubleSpinBox)[2].value())
        },
        {
            "type": "doublespinbox", "text": "Yaw",
            "min": -999999999, "max": 999999999, "steps": 0.01,
            "default": settings.get(f"{device} playspace yaw", 0.0),
            "func": lambda: se.update_setting(f"{device} playspace yaw", playspace.findChildren(QDoubleSpinBox)[3].value())
        }
    ]})

    ps_keys = ["x", "y", "z", "yaw"]
    for sb, k in zip(playspace.findChildren(QDoubleSpinBox), ps_keys):
        sb._setting_key = f"{device} playspace {k}"

    playspace_widget = QWidget()
    playspace_layout = QHBoxLayout(playspace_widget)
    playspace_layout.setContentsMargins(0, 0, 0, 0)

    playspace_layout.addWidget(
        bindable({
            "prefix": device,
            "mapping": "reset playspace",
            "func": lambda: ps.reset_playspace(device)
        })
    )

    playspace_layout.addWidget(reset_method)
    playspace_layout.addWidget(playspace)

    match device:
        case "hmd":
            group_name = "Offsets"
            hover = "Reset Method should be set to 'Fixed Position' here, increment y and click reset until your floor level feels correct"
        case "cr":
            group_name = "Offsets(Right)"
            hover = "Reset Method should be set to 'Headset' here, to reset move your controller(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"
        case "cl":
            group_name = "Offsets(Left)"
            hover = "Reset Method should be set to 'Headset' here, to reset move your controller(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"
        case _:
            group_name = "Offsets"
            hover = "Reset Method should be set to 'Headset' here, to reset move your tracker(target) above or below your headset so that its x and z are aligned with your headset(source) change y to adjust how high or low the reset point (avoid changing x z)"

    world_group = group({
        "text": "World",
        "box": "h",
        "arr": [world],
        "tooltip": "this moves a device world position and rotation"
    })

    local_group = group({
        "text": "Local",
        "box": "h",
        "arr": [local],
        "tooltip": "imagin that your source position or rotation is the parent and your emulated device is the child connected to them, if the parent changes its rotation the child will change both its position and rotation"
    })

    playspace_group = group({
        "text": "Play Space",
        "box": "h",
        "arr": [playspace_widget],
        "tooltip": hover
    })

    final_widget = group({
        "text": group_name,
        "box": "v",
        "arr": [world_group, local_group, playspace_group]
    })

    offsets_ui_dict[device] = {
        "world": world_group,
        "local": local_group,
        "playspace": playspace_group
    }

    return final_widget

class SingleBindButton(QPushButton):
    def __init__(self, mapping_name, current_bind, callback, parent=None):
        super().__init__("", parent)
        self.mapping_name = mapping_name
        self.current_bind = current_bind
        self.callback = callback
        self.is_binding = False

        self.refresh_display()
        self.clicked.connect(self.start_binding)

    def refresh_display(self):
        self.setText(f"{self.mapping_name}: {self.current_bind}")

    def start_binding(self):
        if ch.current_binding_btn and ch.current_binding_btn != self:
            ch.current_binding_btn.cancel_binding()

        ch.current_binding_btn = self
        self.is_binding = True
        self.setText("Press something (ESC to unbind)")
        self.setFocus()

    def cancel_binding(self):
        self.is_binding = False
        self.refresh_display()

    def finish_binding(self, input_name):
        self.is_binding = False
        ch.current_binding_btn = None
        self.current_bind = input_name
        self.refresh_display()

        self.callback()

    def keyPressEvent(self, event):
        if self.is_binding:
            if event.key() == Qt.Key.Key_Escape:
                self.finish_binding("[Unbound]")
            else:
                key_name = QKeySequence(event.key()).toString()
                self.finish_binding(f"Key_{key_name}")
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.is_binding:
            btn_map = {
                Qt.MouseButton.LeftButton: "Left",
                Qt.MouseButton.RightButton: "Right",
                Qt.MouseButton.MiddleButton: "Middle",
                Qt.MouseButton.XButton1: "M4",
                Qt.MouseButton.XButton2: "M5",
                Qt.MouseButton.BackButton: "Back",
                Qt.MouseButton.ForwardButton: "Forward",
                Qt.MouseButton.TaskButton: "Task"
            }

            button_id = event.button()
            button_name = btn_map.get(button_id, f"Extra_{button_id.value}")
            self.finish_binding(f"Mouse_{button_name}")
        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        if self.is_binding:
            delta = event.angleDelta().y()
            if delta > 0:
                self.finish_binding("Mouse_WheelUp")
            elif delta < 0:
                self.finish_binding("Mouse_WheelDown")
            event.accept()
        else:
            super().wheelEvent(event)

def bindable(data=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    prefix = data.get("prefix", "")
    mapping_name = data.get("mapping", "")
    trigger_func = data.get("func")
    setting_key = f"{prefix}_{mapping_name}"

    group_widget = QWidget()
    main_layout = QHBoxLayout(group_widget)

    checkbox = QCheckBox("Invert")
    checkbox.setProperty("group", cg)

    buttons_layout = QHBoxLayout()
    main_layout.addLayout(buttons_layout)
    main_layout.addWidget(checkbox)

    button_widgets = []
    
    state = {"was_active": False}

    def sync_state():
        bind_data = se.get_settings().get(setting_key, {})
        state["was_active"] = ch.eval_binding(bind_data) > 0.5

    poll_timer = QTimer(group_widget)
    poll_timer.setInterval(16)

    def check_binding_state():
        if not callable(trigger_func):
            return

        current_settings = se.get_settings()
        bind_data = current_settings.get(setting_key, {})

        val = ch.eval_binding(bind_data)
        is_active = val > 0.5

        if is_active and not state["was_active"]:
            trigger_func()

        state["was_active"] = is_active

    poll_timer.timeout.connect(check_binding_state)
    poll_timer.start()

    def render_buttons(binds):
        while button_widgets:
            btn = button_widgets.pop()
            buttons_layout.removeWidget(btn)
            btn.setParent(None)
            btn.deleteLater()

        display_list = binds + ["[Unbound]"]

        for bind_value in display_list:
            btn = SingleBindButton(mapping_name, bind_value, on_button_changed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("group", cg)

            btn.style().unpolish(btn)
            btn.style().polish(btn)

            buttons_layout.addWidget(btn)
            button_widgets.append(btn)
            btn.show()

    def save_settings():
        active_binds = [btn.current_bind for btn in button_widgets if btn.current_bind != "[Unbound]"]
        new_data = {
            "buttons": active_binds,
            "invert": checkbox.isChecked()
        }

        se.update_nested(setting_key, new_data)
        sync_state()
        render_buttons(active_binds)

    def on_button_changed():
        QTimer.singleShot(10, save_settings)

    def load_settings():
        current_settings = se.get_settings()
        bind_data = current_settings.get(setting_key, {})

        if not isinstance(bind_data, dict):
            bind_data = {}

        is_inverted = bind_data.get("invert", False)
        checkbox.blockSignals(True)
        checkbox.setChecked(is_inverted)
        checkbox.blockSignals(False)

        saved_buttons = bind_data.get("buttons", [])
        active_binds = [b for b in saved_buttons if b != "[Unbound]"]

        render_buttons(active_binds)
        sync_state()

    checkbox.stateChanged.connect(save_settings)

    load_settings()

    group_widget.setProperty("group", cg)

    return group_widget

def binding_group(mapping, prefix):
    group_widget = QWidget()
    group_layout = QVBoxLayout(group_widget)

    for n in mapping:
        group_layout.addWidget(bindable({"prefix": prefix, "mapping": n}))

    return group_widget

def comm_sub(device, type_name, data=None, on_module_change=None):
    if data is None:
        data = {"group": "widget"}

    cg = data.get("group", "widget")
    
    settings = se.get_settings()
    all_modules_by_title = mode_registry.discover_modes()

    modules_by_title = {
        title: module
        for title, module in all_modules_by_title.items()
        if mode_registry.device_matches(device, getattr(module, f"{type_name}_devices", []))
    }
    mode_titles = list(modules_by_title.keys())

    current_value = settings.get(f"{device}{type_name} mode", "app (named pipe)")
    if current_value not in mode_titles:
        current_value = mode_titles[0]

    active_module = {"current": None}

    def refresh_content(selected_title):
        module = modules_by_title.get(selected_title)

        if active_module["current"] is not module:
            if active_module["current"]:
                mode_manager.release(active_module["current"], device, type_name)
            if module:
                mode_manager.acquire(module, device, type_name)
            active_module["current"] = module

        if callable(on_module_change):
            on_module_change(module)

        if module is not None:
            module.device = device
            module.mode = type_name

    def on_index_change():
        combo_box = combo.findChild(QComboBox)
        if combo_box:
            selected = combo_box.currentText()
            se.update_setting(f"{device}{type_name} mode", selected)
            refresh_content(selected)

    combo = combobox({
        "text": f"{device} {type_name}",
        "default": current_value,
        "items": mode_titles,
        "index change": on_index_change,
        "group": cg,
    })

    refresh_content(current_value)
    return combo

def comm(device, data=None):
    if data is None:
        data = {"group": "widget"}

    group_widget = QWidget()
    group_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    group_layout = QVBoxLayout(group_widget)
    group_layout.setContentsMargins(0, 0, 0, 0)

    group_layout.addWidget(comm_sub(device, "input", data))
    group_layout.addWidget(comm_sub(device, "skeletal", data))

    return group_widget

def update_all(root_widget=None):
    if root_widget is None:
        top_widgets = QApplication.topLevelWidgets()
        for w in top_widgets:
            update_all(w)
        return

    settings = se.get_settings()

    for child in root_widget.findChildren(QWidget):
        key = getattr(child, "_setting_key", None)
        if not key:
            continue

        if isinstance(child, QDoubleSpinBox):
            child.blockSignals(True)
            child.setValue(float(settings.get(key, child.value())))
            child.blockSignals(False)
        elif isinstance(child, QSpinBox):
            child.blockSignals(True)
            child.setValue(int(settings.get(key, child.value())))
            child.blockSignals(False)
        elif isinstance(child, QCheckBox):
            child.blockSignals(True)
            child.setChecked(bool(settings.get(key, child.isChecked())))
            child.blockSignals(False)
        elif isinstance(child, QLineEdit):
            child.blockSignals(True)
            child.setText(str(settings.get(key, child.text())))
            child.blockSignals(False)
        elif isinstance(child, QComboBox):
            child.blockSignals(True)
            child.setCurrentText(str(settings.get(key, child.currentText())))
            child.blockSignals(False)