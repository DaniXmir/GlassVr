#kinda sloppy

#creates a 3d visualizer for steamvr devices

#use this to add
#import visualizer as Renderer3D
#renderer = Renderer3D()
#layout.addWidget(renderer)

import math
import time
import weakref
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QThread, pyqtSignal, pyqtSlot, QTimer, QMetaObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPolygonF

import steamvr as svr
import settings as se
import theme_registry

_CUBE_VERTS = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1),  (1, -1, 1),  (1, 1, 1),  (-1, 1, 1),
]

_CUBE_FACES = [
    (0, 1, 2, 3),  # Back
    (4, 5, 6, 7),  # Front
    (0, 1, 5, 4),  # Bottom
    (2, 3, 7, 6),  # Top
    (0, 3, 7, 4),  # Left
    (1, 2, 6, 5),  # Right
]

_DEFAULT_VISUALIZER_COLORS = {
    "hmd": "#00e5ff",
    "left": "#ff3366",
    "right": "#33ff66",
    "base station": "#ffaa00",
    "trackers": "#aa55ff",
    "background": "#1e1e1e",
    "grid": "#ffffff",
}

_ROLE_THEME_KEY = {
    "HMD": "hmd",
    "LeftHand": "left",
    "RightHand": "right",
    "BaseStation": "base station",
}

def _resolve_theme_color(theme_dict, key):
    fallback_hex = _DEFAULT_VISUALIZER_COLORS[key]
    value = (theme_dict or {}).get(key)
    if isinstance(value, str) and value.strip():
        color = QColor(value)
        if color.isValid():
            return color
    return QColor(fallback_hex)

_visualizer_colors = {key: QColor(hexval) for key, hexval in _DEFAULT_VISUALIZER_COLORS.items()}

_active_renderers = weakref.WeakSet()


def _apply_visualizer_theme(theme_dict):
    global _visualizer_colors
    _visualizer_colors = {
        key: _resolve_theme_color(theme_dict, key) for key in _DEFAULT_VISUALIZER_COLORS
    }
    for renderer in list(_active_renderers):
        renderer._on_visualizer_theme_changed()


def role_color(role):
    key = _ROLE_THEME_KEY.get(role, "trackers")
    return QColor(_visualizer_colors[key])


def background_color():
    return QColor(_visualizer_colors["background"])


def grid_color():
    return QColor(_visualizer_colors["grid"])

_apply_visualizer_theme(theme_registry.get_visualizer_theme())
theme_registry.register_visualizer_listener(_apply_visualizer_theme)


def _values_equal(a, b):
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return np.array_equal(a, b)
    return a == b


def _trackers_equal(a, b):
    if a is b:
        return True
    if a is None or b is None:
        return False
    if a.keys() != b.keys():
        return False
    for serial, dev_a in a.items():
        dev_b = b[serial]
        if dev_a.keys() != dev_b.keys():
            return False
        for field, val_a in dev_a.items():
            if not _values_equal(val_a, dev_b[field]):
                return False
    return True

_SETTINGS_TTL = 0.2  # seconds
_settings_cache = {"value": None, "time": 0.0}

def _get_cached_settings():
    now = time.monotonic()
    if _settings_cache["value"] is None or (now - _settings_cache["time"]) > _SETTINGS_TTL:
        _settings_cache["value"] = se.get_settings()
        _settings_cache["time"] = now
    return _settings_cache["value"]

class TrackerWorker(QThread):
    trackers_updated = pyqtSignal(dict)

    def __init__(self, interval_ms=16, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.timer = None
        self._last_trackers = None

    def run(self):
        self.timer = QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._poll_trackers)
        self.timer.start()
        self.exec()

    def _poll_trackers(self):
        if self.isInterruptionRequested():
            if self.timer:
                self.timer.stop()
            self.quit()
            return

        current_settings = _get_cached_settings()
        if not current_settings.get("enable_visualizer", True):
            return

        trackers = svr.get_trackers_dict()
        if trackers and not _trackers_equal(trackers, self._last_trackers):
            self._last_trackers = trackers
            self.trackers_updated.emit(trackers)

    def stop_async(self):
        self.requestInterruption()
        if self.timer and self.isRunning():
            QMetaObject.invokeMethod(self.timer, "stop", Qt.ConnectionType.QueuedConnection)
        self.quit()

class Cube:
    def __init__(self, serial, role="Unknown", size=0.2):
        self.serial = serial
        self.role = role
        self.size = size
        self.pos = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.rot_mat = np.eye(3, dtype=np.float64)
        self.color = role_color(role)

    def update_from_tracker(self, tracker_data):
        if not tracker_data:
            return

        self.role = tracker_data.get("role", self.role)
        self.color = role_color(self.role)

        if "pos x" in tracker_data and "pos y" in tracker_data and "pos z" in tracker_data:
            self.pos = np.array([
                tracker_data["pos x"],
                tracker_data["pos y"],
                tracker_data["pos z"]
            ], dtype=np.float64)

        if "rotation matrix" in tracker_data:
            self.rot_mat = np.array(tracker_data["rotation matrix"], dtype=np.float64)

class Renderer3D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cubes_by_serial = {}

        self.cam_dist = 4.0
        self.cam_yaw = 0.0
        self.cam_pitch = 0.2
        self.pan_offset = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.fov_scale = 300.0

        self.last_mouse_pos = None
        self.setMinimumHeight(400)

        self._label_font = QFont("Sans-Serif", 9, QFont.Weight.Bold)
        self._label_metrics = QFontMetrics(self._label_font)

        self._minor_grid_pens = {}
        self._major_grid_pens = {}
        self._axis_pen_z = QPen(QColor(60, 60, 255, 220))
        self._axis_pen_z.setWidthF(2.0)
        self._axis_pen_x = QPen(QColor(255, 60, 60, 220))
        self._axis_pen_x.setWidthF(2.0)

        self.worker = None
        self._start_worker()

        _active_renderers.add(self)

    def _on_visualizer_theme_changed(self):
        for cube in self.cubes_by_serial.values():
            cube.color = role_color(cube.role)

        self._minor_grid_pens.clear()
        self._major_grid_pens.clear()

        self.update()

    def _start_worker(self):
        if self.worker is None or not self.worker.isRunning():
            self.worker = TrackerWorker(interval_ms=16, parent=None)
            self.worker.trackers_updated.connect(self._on_trackers_updated)
            self.worker.start()

    def _stop_worker(self):
        if self.worker is not None:
            self.worker.trackers_updated.disconnect(self._on_trackers_updated)
            self.worker.stop_async()
            self.worker = None

    def hideEvent(self, event):
        self._stop_worker()
        super().hideEvent(event)

    def showEvent(self, event):
        self._start_worker()
        super().showEvent(event)

    def closeEvent(self, event):
        self._stop_worker()
        super().closeEvent(event)

    def _get_attach_setting(self):
        return _get_cached_settings().get("attach cam", False)

    def _get_hmd_cube(self):
        for cube in self.cubes_by_serial.values():
            if cube.role == "HMD":
                return cube
        return None

    @pyqtSlot(dict)
    def _on_trackers_updated(self, trackers_dict):
        self.sync_devices(trackers_dict)
        self.update()

    def sync_devices(self, trackers_dict):
        active_serials = set(trackers_dict.keys())
        current_serials = set(self.cubes_by_serial.keys())

        for serial in current_serials - active_serials:
            del self.cubes_by_serial[serial]

        for serial, data in trackers_dict.items():
            if serial not in self.cubes_by_serial:
                role = data.get("role", "Unknown")
                size = 0.25 if role == "HMD" else 0.15
                self.cubes_by_serial[serial] = Cube(serial, role=role, size=size)

            self.cubes_by_serial[serial].update_from_tracker(data)

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is None:
            return

        current_pos = event.position()
        delta = current_pos - self.last_mouse_pos
        dx, dy = delta.x(), delta.y()

        buttons = event.buttons()

        if self._get_attach_setting():
            self.last_mouse_pos = current_pos
            return

        if buttons & Qt.MouseButton.LeftButton:
            self.cam_yaw -= dx * 0.005
            self.cam_pitch += dy * 0.005
            self.cam_pitch = max(-math.pi / 2.2, min(math.pi / 2.2, self.cam_pitch))
            self.update()

        elif buttons & (Qt.MouseButton.MiddleButton | Qt.MouseButton.RightButton):
            pan_speed = self.cam_dist / self.fov_scale
            R_view = self._get_view_matrix()
            cam_right = R_view[0, :]
            cam_up = R_view[1, :]

            self.pan_offset += (cam_right * dx + cam_up * dy) * pan_speed
            self.update()

        self.last_mouse_pos = current_pos

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = None

    def wheelEvent(self, event):
        if not self._get_attach_setting():
            delta = event.angleDelta().y()
            if delta > 0:
                self.cam_dist = max(0.1, self.cam_dist * 0.9)
            else:
                self.cam_dist = min(100.0, self.cam_dist * 1.1)
            self.update()

    def _get_view_matrix(self):
        cy, sy = math.cos(self.cam_yaw), math.sin(self.cam_yaw)
        cp, sp = math.cos(self.cam_pitch), math.sin(self.cam_pitch)

        R_yaw = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
        R_pitch = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])

        return R_pitch @ R_yaw

    def _get_first_person_view(self, hmd_cube):
        R_y_180 = np.array([
            [-1.0,  0.0,  0.0],
            [ 0.0,  1.0,  0.0],
            [ 0.0,  0.0, -1.0]
        ], dtype=np.float64)

        R_view = R_y_180 @ hmd_cube.rot_mat.T
        pan_offset = hmd_cube.pos.copy()
        cam_dist = 0.0
        return R_view, pan_offset, cam_dist

    def _get_third_person_view(self):
        R_view = self._get_view_matrix()
        pan_offset = self.pan_offset
        cam_dist = self.cam_dist
        return R_view, pan_offset, cam_dist

    def _project_point(self, p_cam, screen_w, screen_h, cam_dist):
        z = p_cam[2] + cam_dist
        factor = self.fov_scale / z
        sx = -p_cam[0] * factor + screen_w / 2.0
        sy = -p_cam[1] * factor + screen_h / 2.0
        return QPointF(sx, sy)

    def _draw_clipped_line(self, painter, p1_cam, p2_cam, w, h, pen, cam_dist, near_plane=0.1):
        z1 = p1_cam[2] + cam_dist
        z2 = p2_cam[2] + cam_dist

        if z1 < near_plane and z2 < near_plane:
            return

        if z1 < near_plane:
            t = (near_plane - z1) / (z2 - z1)
            p1_cam = p1_cam + t * (p2_cam - p1_cam)

        if z2 < near_plane:
            t = (near_plane - z2) / (z1 - z2)
            p2_cam = p2_cam + t * (p1_cam - p2_cam)

        painter.setPen(pen)
        pt1 = self._project_point(p1_cam, w, h, cam_dist)
        pt2 = self._project_point(p2_cam, w, h, cam_dist)
        painter.drawLine(pt1, pt2)

    def _draw_clipped_face(self, painter, pts_cam, w, h, fill_color, border_pen, cam_dist, near_plane=0.1):
        clipped_pts = []
        n = len(pts_cam)
        for i in range(n):
            p1 = pts_cam[i]
            p2 = pts_cam[(i + 1) % n]
            z1 = p1[2] + cam_dist
            z2 = p2[2] + cam_dist

            if z1 >= near_plane:
                clipped_pts.append(p1)

            if (z1 >= near_plane and z2 < near_plane) or (z1 < near_plane and z2 >= near_plane):
                t = (near_plane - z1) / (z2 - z1)
                p_intersect = p1 + t * (p2 - p1)
                clipped_pts.append(p_intersect)

        if len(clipped_pts) < 3:
            return

        polygon = QPolygonF()
        for p in clipped_pts:
            polygon.append(self._project_point(p, w, h, cam_dist))

        painter.setPen(border_pen)
        painter.setBrush(fill_color)
        painter.drawPolygon(polygon)

    def _draw_label_3d(self, painter, text, world_pos, R_view, w, h, color, cam_dist, pan_offset, near_plane=0.1):
        cam_p = R_view @ (world_pos - pan_offset)
        z = cam_p[2] + cam_dist

        if z < near_plane:
            return

        pt = self._project_point(cam_p, w, h, cam_dist)

        painter.setFont(self._label_font)
        metrics = self._label_metrics

        text_w = metrics.horizontalAdvance(text)
        text_h = metrics.height()

        padding_x, padding_y = 6, 2
        rect_w = text_w + padding_x * 2
        rect_h = text_h + padding_y * 2

        rx = pt.x() - rect_w / 2.0
        ry = pt.y() - rect_h / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 20, 20, 180))
        painter.drawRoundedRect(int(rx), int(ry), int(rect_w), int(rect_h), 4.0, 4.0)

        painter.setPen(color)
        painter.drawText(int(rx + padding_x), int(ry + rect_h - padding_y - 2), text)

    def _get_grid_pen(self, pool, alpha, base_color):
        pen = pool.get(alpha)
        if pen is None:
            color = QColor(base_color)
            color.setAlpha(alpha)
            pen = QPen(color)
            pen.setWidthF(1.0)
            pool[alpha] = pen
        return pen

    def _draw_grid(self, painter, R_view, w, h, cam_dist, pan_offset):
        extent = max(10.0, cam_dist * 3.5)

        for step, base_alpha, pool in [(1.0, 25, self._minor_grid_pens), (10.0, 60, self._major_grid_pens)]:
            center_x = math.floor(pan_offset[0] / step) * step
            center_z = math.floor(pan_offset[2] / step) * step
            half_count = int(extent / step)

            for i in range(-half_count, half_count + 1):
                x = center_x + i * step
                if abs(x) < 1e-5:
                    continue

                p1_world = np.array([x, 0.0, center_z - extent]) - pan_offset
                p2_world = np.array([x, 0.0, center_z + extent]) - pan_offset

                dist_factor = 1.0 - min(1.0, abs(x - pan_offset[0]) / extent)
                alpha = int(base_alpha * (dist_factor ** 1.5))
                if alpha <= 2:
                    continue

                pen = self._get_grid_pen(pool, alpha, grid_color())
                self._draw_clipped_line(painter, R_view @ p1_world, R_view @ p2_world, w, h, pen, cam_dist)

            for i in range(-half_count, half_count + 1):
                z = center_z + i * step
                if abs(z) < 1e-5:
                    continue

                p1_world = np.array([center_x - extent, 0.0, z]) - pan_offset
                p2_world = np.array([center_x + extent, 0.0, z]) - pan_offset

                dist_factor = 1.0 - min(1.0, abs(z - pan_offset[2]) / extent)
                alpha = int(base_alpha * (dist_factor ** 1.5))
                if alpha <= 2:
                    continue

                pen = self._get_grid_pen(pool, alpha, grid_color())
                self._draw_clipped_line(painter, R_view @ p1_world, R_view @ p2_world, w, h, pen, cam_dist)

        axis_len = extent * 1.5

        p1_z_axis = np.array([0.0, 0.0, pan_offset[2] - axis_len]) - pan_offset
        p2_z_axis = np.array([0.0, 0.0, pan_offset[2] + axis_len]) - pan_offset
        self._draw_clipped_line(painter, R_view @ p1_z_axis, R_view @ p2_z_axis, w, h, self._axis_pen_z, cam_dist)

        p1_x_axis = np.array([pan_offset[0] - axis_len, 0.0, 0.0]) - pan_offset
        p2_x_axis = np.array([pan_offset[0] + axis_len, 0.0, 0.0]) - pan_offset
        self._draw_clipped_line(painter, R_view @ p1_x_axis, R_view @ p2_x_axis, w, h, self._axis_pen_x, cam_dist)

    def paintEvent(self, event):
        settings = _get_cached_settings()
        if not settings.get("enable_visualizer", True):
            painter = QPainter(self)
            painter.fillRect(self.rect(), background_color())
            painter.end()
            return

        attach_cam = settings.get("attach cam", False)
        hmd_cube = self._get_hmd_cube()

        if attach_cam and hmd_cube is not None:
            R_view, pan_offset, cam_dist = self._get_first_person_view(hmd_cube)
        else:
            R_view, pan_offset, cam_dist = self._get_third_person_view()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, background_color())

        self._draw_grid(painter, R_view, w, h, cam_dist, pan_offset)

        unit_verts = np.array(_CUBE_VERTS, dtype=np.float64)
        render_faces = []

        for cube in self.cubes_by_serial.values():
            if attach_cam and cube.role == "HMD":
                continue

            rel_pos = cube.pos - pan_offset
            cam_verts = (unit_verts * cube.size) @ cube.rot_mat.T @ R_view.T + (rel_pos @ R_view.T)

            fill_color = QColor(cube.color)
            fill_color.setAlpha(180)

            border_pen = QPen(cube.color.lighter(130))
            border_pen.setWidthF(1.5)

            for face_indices in _CUBE_FACES:
                face_pts = [cam_verts[i] for i in face_indices]
                avg_z = sum((p[2] + cam_dist) for p in face_pts) / 4.0
                render_faces.append((avg_z, face_pts, fill_color, border_pen))

            label_world_pos = cube.pos + np.array([0.0, cube.size + 0.08, 0.0], dtype=np.float64)
            self._draw_label_3d(painter, cube.serial, label_world_pos, R_view, w, h, cube.color, cam_dist, pan_offset)

        render_faces.sort(key=lambda item: item[0], reverse=True)

        for _, face_pts, fill_color, border_pen in render_faces:
            self._draw_clipped_face(painter, face_pts, w, h, fill_color, border_pen, cam_dist)

        painter.end()