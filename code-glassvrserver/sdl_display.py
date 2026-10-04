"""
aaaa
"""

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot

import controller_handler as ch
import settings as se
import elements as el
import theme_registry as tr

class ControllerPoller(QThread):
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

        controllers = ch.get_all_controllers()

        if self.isInterruptionRequested():
            return

        data = {c.get("id", "unknown"): c for c in controllers}
        self.devices_updated.emit(data)

    def stop_and_wait(self):
        if not self.isRunning():
            return

        self.requestInterruption()
        self.quit()

        if not self.wait(2000):
            self.terminate()
            self.wait()

class SDLDisplay(QScrollArea):
    def __init__(self, parent=None, poll_interval_ms=16):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setMinimumHeight(320)

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

        self.poller = ControllerPoller(
            interval_ms=self.poll_interval_ms,
            parent=self
        )
        self.poller.devices_updated.connect(self.update_found_devices)
        self.poller.start()

    def _stop_poller(self):
        poller = self.poller
        if poller is None:
            return

        self.poller = None

        try:
            poller.devices_updated.disconnect(self.update_found_devices)
        except (TypeError, RuntimeError):
            pass

        poller.stop_and_wait()
        poller.deleteLater()

    def closeEvent(self, event):
        self._stop_poller()
        super().closeEvent(event)

    @pyqtSlot(dict)
    def update_found_devices(self, data_dict):
        active_ids = set(data_dict.keys())
        current_ids = set(self.device_widgets.keys())

        for c_id in current_ids - active_ids:
            widget_dict = self.device_widgets.pop(c_id)
            widget_dict['group'].deleteLater()

        for count, (c_id, ctrl) in enumerate(data_dict.items()):
            if c_id in self.device_widgets:
                w = self.device_widgets[c_id]
                if ctrl.get("active"):
                    w['status'].setText("CONNECTED")
                    w['status'].setStyleSheet("color: green; font-weight: bold;")
                else:
                    w['status'].setText("DISCONNECTED")
                    w['status'].setStyleSheet("color: red; font-weight: bold;")

                self._update_live_readout(w, ctrl)
                continue

            self._create_controller_block(c_id, ctrl, count)

    def _update_live_readout(self, w, ctrl):
        leftx = ctrl.get("leftx", 0.0)
        lefty = ctrl.get("lefty", 0.0)
        rightx = ctrl.get("rightx", 0.0)
        righty = ctrl.get("righty", 0.0)
        gq = ctrl.get("gyro_quat", {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})

        w['leftstick'].setText(f"(X:{leftx:+.4f}  Y:{lefty:+.4f})")
        w['rightstick'].setText(f"(X:{rightx:+.4f}  Y:{righty:+.4f})")
        w['gyro'].setText(
            f"(X:{gq.get('x', 0.0):+.4f}  Y:{gq.get('y', 0.0):+.4f}  "
            f"Z:{gq.get('z', 0.0):+.4f}  W:{gq.get('w', 1.0):+.4f})"
        )

    def _create_controller_block(self, c_id, ctrl, count):
        c_name = ctrl.get("type", "Unknown Controller")
        settings = se.get_settings()
        c_conf = settings.get(c_id, {})

        group = el.group({
            "text": f"Name:({c_name}) ID:({c_id})",
            "box": "v",
            "group": "block",
        })
        tr.style_block(group, count)

        group_layout = group.layout()
        group_layout.setSpacing(4)
        group_layout.setContentsMargins(8, 8, 8, 8)

        status_text = "CONNECTED" if ctrl.get("active") else "DISCONNECTED"
        status_color = "green" if ctrl.get("active") else "red"
        status_label = QLabel(status_text)
        status_label.setProperty("group", "label")
        status_label.setMaximumHeight(status_label.fontMetrics().height())

        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        group_layout.addWidget(status_label)

        gyro_inverts = el.group({
            "box": "h",
            "arr": [
                {"type": "label", "text": "Invert:"},
                {"type": "checkbox", "text": "X", "default": c_conf.get("invert_x", False),
                 "func": lambda: se.update_nested(c_id, {"invert_x": gyro_inverts.findChildren(QCheckBox)[0].isChecked()})},
                {"type": "checkbox", "text": "Y", "default": c_conf.get("invert_y", False),
                 "func": lambda: se.update_nested(c_id, {"invert_y": gyro_inverts.findChildren(QCheckBox)[1].isChecked()})},
                {"type": "checkbox", "text": "Z", "default": c_conf.get("invert_z", False),
                 "func": lambda: se.update_nested(c_id, {"invert_z": gyro_inverts.findChildren(QCheckBox)[2].isChecked()})},
            ],
        })

        gyro_indices = el.group({
            "box": "h",
            "arr": [
                {"type": "label", "text": "Direction:"},
                {"type": "spinbox", "text": "X", "min": 0, "max": 2, "default": c_conf.get("index_x", 0),
                 "func": lambda: se.update_nested(c_id, {"index_x": gyro_indices.findChildren(QSpinBox)[0].value()})},
                {"type": "spinbox", "text": "Y", "min": 0, "max": 2, "default": c_conf.get("index_y", 1),
                 "func": lambda: se.update_nested(c_id, {"index_y": gyro_indices.findChildren(QSpinBox)[1].value()})},
                {"type": "spinbox", "text": "Z", "min": 0, "max": 2, "default": c_conf.get("index_z", 2),
                 "func": lambda: se.update_nested(c_id, {"index_z": gyro_indices.findChildren(QSpinBox)[2].value()})},
            ],
        })

        gyro_sens = el.doublespinbox({
            "text": "Sensitivity:", "min": -99999, "max": 99999, "steps": 0.1,
            "default": c_conf.get("sensitivity", 1.0),
            "func": lambda: se.update_nested(c_id, {"sensitivity": gyro_sens.findChild(QDoubleSpinBox).value()}),
        })

        clib_b = el.button({
            "text": "Calibrate Gyro",
            "func": lambda: ch.start_calibration(c_id),
        })

        reset_b = el.bindable({
            "prefix": c_id,
            "mapping": "reset_gyro",
            "func" : lambda target=c_id: ch.reset_gyro(target)
        })

        header_style = "font-weight: bold; margin-top: 4px;"

        leftstick_header = QLabel("Left Stick:")
        leftstick_header.setStyleSheet(header_style)
        leftstick_label = QLabel("(X:+0.0000  Y:+0.0000)")

        rightstick_header = QLabel("Right Stick:")
        rightstick_header.setStyleSheet(header_style)
        rightstick_label = QLabel("(X:+0.0000  Y:+0.0000)")

        gyro_header = QLabel("Gyro:")
        gyro_header.setStyleSheet(header_style)
        gyro_label = QLabel("(X:+0.0000  Y:+0.0000  Z:+0.0000  W:+1.0000)")

        for lbl in (leftstick_label, rightstick_label, gyro_label):
            lbl.setStyleSheet("font-family: monospace;")

        for lbl in (leftstick_header, leftstick_label,
                    rightstick_header, rightstick_label,
                    gyro_header, gyro_label):
            lbl.setProperty("group", "label")

        for value_widget in (leftstick_header, leftstick_label,
                             rightstick_header, rightstick_label,
                             gyro_header, gyro_label):
            group_layout.addWidget(value_widget)

        deadzone_x_sb = el.doublespinbox({
            "text": "X:", "min": 0.0, "max": 0.95, "steps": 0.01,
            "default": c_conf.get("deadzone_x", settings.get("default deadzone x", 0.1)),
            "func": lambda: se.update_nested(c_id, {"deadzone_x": deadzone_x_sb.findChild(QDoubleSpinBox).value()}),
        })

        deadzone_y_sb = el.doublespinbox({
            "text": "Y:", "min": 0.0, "max": 0.95, "steps": 0.01,
            "default": c_conf.get("deadzone_y", settings.get("default deadzone y", 0.1)),
            "func": lambda: se.update_nested(c_id, {"deadzone_y": deadzone_y_sb.findChild(QDoubleSpinBox).value()}),
        })

        group_deadzone = el.group({"text": "deadzone",
                                   "box" : "h",
                                   "arr": [deadzone_x_sb, deadzone_y_sb]})

        group_layout.addWidget(group_deadzone)

        group_gyro = el.group({"text" : "gyro",
                               "box" : "v",
                               "arr" : [gyro_inverts,
                                        gyro_indices,
                                        gyro_sens,
                                        clib_b,
                                        reset_b
                               ]})

        group_layout.addWidget(group_gyro)

        self.detected_layout.addWidget(group)

        self.device_widgets[c_id] = {
            'group': group,
            'status': status_label,
            'leftstick': leftstick_label,
            'rightstick': rightstick_label,
            'gyro': gyro_label,
        }

        self._update_live_readout(self.device_widgets[c_id], ctrl)