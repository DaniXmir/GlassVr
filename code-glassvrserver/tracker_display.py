#creates a visual scroll for connected steamvr devices

import sys
from scipy.spatial.transform import Rotation as R

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGroupBox, QScrollArea
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot

import steamvr as svr
import settings as se
import theme_registry as tr


class TrackerPoller(QThread):
    devices_updated = pyqtSignal(dict)

    def __init__(self, interval_ms=16, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.timer = None

    def run(self):
        self.timer = QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._poll)
        self.timer.start()

        self.exec()

        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

    def _poll(self):
        if self.isInterruptionRequested():
            self.quit()
            return

        current_settings = se.get_settings()

        if self.isInterruptionRequested():
            self.quit()
            return

        if not current_settings.get("enable_tracker_display", True):
            return

        data = svr.get_trackers_dict()

        if self.isInterruptionRequested():
            return

        if data is not None:
            self.devices_updated.emit(data)

    def stop_and_wait(self):
        if not self.isRunning():
            return

        self.requestInterruption()

        self.quit()

        if not self.wait(2000):
            self.terminate()
            self.wait()


class TrackerDisplay(QScrollArea):
    def __init__(self, parent=None, poll_interval_ms=16):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setMaximumHeight(200)

        self.container_widget = QWidget()
        self.detected_layout = QHBoxLayout(self.container_widget)
        self.detected_layout.setContentsMargins(4, 4, 4, 4)
        self.detected_layout.setSpacing(8)
        self.setWidget(self.container_widget)

        self.device_widgets = {}
        self.poll_interval_ms = poll_interval_ms

        self.poller = None

        self._start_poller()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._stop_poller)

    def _start_poller(self):
        if self.poller is not None and self.poller.isRunning():
            return

        self.poller = TrackerPoller(
            interval_ms=self.poll_interval_ms,
            parent=self
        )

        self.poller.devices_updated.connect(
            self.update_found_devices
        )

        self.poller.start()

    def _stop_poller(self):
        poller = self.poller

        if poller is None:
            return

        self.poller = None

        try:
            poller.devices_updated.disconnect(
                self.update_found_devices
            )
        except (TypeError, RuntimeError):
            pass

        poller.stop_and_wait()

        poller.deleteLater()

    def hideEvent(self, event):
        self._stop_poller()
        super().hideEvent(event)

    def showEvent(self, event):
        self._start_poller()
        super().showEvent(event)

    def closeEvent(self, event):
        self._stop_poller()
        super().closeEvent(event)

    @pyqtSlot(dict)
    def update_found_devices(self, data_dict):
        active_serials = set(data_dict.keys())
        current_serials = set(self.device_widgets.keys())

        for serial in current_serials - active_serials:
            widget_dict = self.device_widgets.pop(serial)
            widget_dict['group'].deleteLater()

        for count, (serial, data) in enumerate(data_dict.items()):
            if serial in self.device_widgets:
                w = self.device_widgets[serial]
                conn = data.get('connected')
                valid = data.get('pose_valid')

                if not conn:
                    w['status'].setText("DISCONNECTED")
                    w['status'].setStyleSheet("color: red; font-weight: bold;")
                elif not valid:
                    w['status'].setText("SEARCHING...")
                    w['status'].setStyleSheet("color: yellow; font-weight: bold;")
                else:
                    w['status'].setText("TRACKING")
                    w['status'].setStyleSheet("color: green; font-weight: bold;")

                if "pos x" in data:
                    px, py, pz = data['pos x'], data['pos y'], data['pos z']
                    w['pos'].setText(f"(X:{px:+.4f}  Y:{py:+.4f}  Z:{pz:+.4f})")

                if "rotation matrix" in data:
                    m = data['rotation matrix']
                    yaw, pitch, roll = R.from_matrix(m).as_euler('yxz', degrees=True)
                    w['rot'].setText(f"(Yaw:{yaw:+.1f}°  Pitch:{pitch:+.1f}°  Roll:{roll:+.1f}°)")
                continue

            role = data.get('role', 'Unknown')
            model = data.get('model', 'Device')

            group = QGroupBox(f"[{count}]  {role}  |  {model}")
            tr.style_block(group, count)

            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(0)
            group_layout.setContentsMargins(8, 8, 8, 8)

            conn = data.get('connected')
            valid = data.get('pose_valid')
            if not conn:
                status_text, status_color = "DISCONNECTED", "red"
            elif not valid:
                status_text, status_color = "SEARCHING...", "yellow"
            else:
                status_text, status_color = "TRACKING", "green"

            status_label = QLabel(status_text)
            status_label.setProperty("group", "block_label")
            status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            group_layout.addWidget(status_label)

            pos_label = QLabel("(X: —  Y: —  Z: —)")
            rot_label = QLabel("(Yaw: —  Pitch: —  Roll: —)")
            pos_label.setProperty("group", "block_label")
            rot_label.setProperty("group", "block_label")

            if "pos x" in data:
                px, py, pz = data['pos x'], data['pos y'], data['pos z']
                pos_label.setText(f"(X:{px:+.4f}  Y:{py:+.4f}  Z:{pz:+.4f})")

            if "rotation matrix" in data:
                yaw, pitch, roll = R.from_matrix(data['rotation matrix']).as_euler('yxz', degrees=True)
                rot_label.setText(f"(Yaw:{yaw:+.1f}°  Pitch:{pitch:+.1f}°  Roll:{roll:+.1f}°)")

            serial_btn = QPushButton(f"Serial: {serial}")
            serial_btn.setToolTip("Click to copy serial to clipboard")
            serial_btn.setProperty("group", "widget")
            serial_btn.setStyleSheet("text-align: left;")

            def on_copy(_, s=serial, btn=serial_btn):
                QApplication.clipboard().setText(s)
                btn.setText("Copied to clipboard!")
                QTimer.singleShot(500, lambda: btn.setText(f"Serial: {s}"))

            serial_btn.clicked.connect(on_copy)

            pos_header = QLabel("Position:")
            pos_header.setProperty("group", "block_label")
            pos_header.setStyleSheet("margin-top: 4px;")
            group_layout.addWidget(pos_header)
            group_layout.addWidget(pos_label)

            rot_header = QLabel("Rotation:")
            rot_header.setProperty("group", "block_label")
            rot_header.setStyleSheet("margin-top: 4px;")
            group_layout.addWidget(rot_header)
            group_layout.addWidget(rot_label)

            group_layout.addWidget(serial_btn)

            self.detected_layout.addWidget(group)

            self.device_widgets[serial] = {
                'group': group,
                'status': status_label,
                'pos': pos_label,
                'rot': rot_label,
            }