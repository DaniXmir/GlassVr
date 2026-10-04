#mirrors the "headset view" window so you dont have to set your monitor to primary everytime,
#super slow!!! only for debugging, a more proper implementation will be using virtual display mode instead of extended
#but i couldnt get that fast enough

import time
import socket
import threading
import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api
from flask import Flask, Response
from screeninfo import get_monitors
import settings as settings_core

flask_app = Flask(__name__)

latest_raw_frame = None
latest_encoded_frame = None
_capture_started = False

class WindowMirror:
    def __init__(self, target_title="Headset Window"):
        self.hwnd = win32gui.FindWindow(None, target_title)
        
        if not self.hwnd:
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if target_title.lower() in title.lower():
                        extra.append(hwnd)
            hwnds = []
            win32gui.EnumWindows(enum_windows_callback, hwnds)
            if hwnds:
                self.hwnd = hwnds[0]

        if not self.hwnd:
            raise Exception(f"Could not find any window matching '{target_title}'.")

        rect = win32gui.GetWindowRect(self.hwnd)
        self.w = rect[2] - rect[0]
        self.h = rect[3] - rect[1]
        if self.w <= 0 or self.h <= 0:
            self.w, self.h = 1280, 720

    def capture_frame(self):
        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        rect = win32gui.GetWindowRect(self.hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w > 0 and h > 0:
            self.w, self.h = w, h

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, self.w, self.h)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0, 0), (self.w, self.h), mfc_dc, (0, 0), win32con.SRCCOPY)

        raw = bitmap.GetBitmapBits(True)
        img = np.frombuffer(raw, dtype="uint8").reshape((self.h, self.w, 4))

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def _shared_capture_loop():
    global latest_raw_frame, latest_encoded_frame

    while True:
        mirror = None
        while mirror is None:
            try:
                mirror = WindowMirror("Headset Window")
            except Exception:
                time.sleep(1)

        while True:
            try:
                settings = settings_core.get_settings()
                frame = mirror.capture_frame()
                latest_raw_frame = frame

                if settings.get("mirror web", False):
                    scale = settings.get("mirror web scale", 1.0)
                    if scale != 1.0:
                        small = cv2.resize(
                            frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST
                        )
                    else:
                        small = frame

                    quality = settings.get("mirror web bitrate", 100)
                    # Fast encoding flag added
                    ok, enc = cv2.imencode(
                        ".jpg",
                        small,
                        [
                            cv2.IMWRITE_JPEG_QUALITY, quality,
                            cv2.IMWRITE_JPEG_OPTIMIZE, 0,
                            cv2.IMWRITE_JPEG_PROGRESSIVE, 0,
                        ],
                    )
                    if ok:
                        latest_encoded_frame = enc.tobytes()

            except Exception as e:
                print(f"[Mirror Error] Capture failed: {e}")
                time.sleep(1)
                break

def _ensure_capture_running():
    global _capture_started
    if not _capture_started:
        _capture_started = True
        threading.Thread(target=_shared_capture_loop, daemon=True).start()

def generate_stream_bytes():
    global latest_encoded_frame
    yield b"--frame\r\n"
    last_frame = None
    while True:
        if latest_encoded_frame is not None and latest_encoded_frame is not last_frame:
            last_frame = latest_encoded_frame
            yield b"Content-Type: image/jpeg\r\n\r\n" + latest_encoded_frame + b"\r\n--frame\r\n"
        else:
            time.sleep(0.0001)

@flask_app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>Headset Window Stream</title><style>
body{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden;user-select:none}
img{width:100vw;height:100vh;object-fit:contain;image-rendering:pixelated;cursor:pointer}
</style></head><body>
<img id="stream" src="/stream" />
<script>
const img = document.getElementById('stream');
img.addEventListener('dblclick', () => {
    if(!document.fullscreenElement) img.requestFullscreen();
    else document.exitFullscreen();
});
</script></body></html>"""

@flask_app.route("/frame.jpg")
def single_frame():
    if latest_encoded_frame is None:
        return "", 204
    return Response(latest_encoded_frame, mimetype="image/jpeg")

@flask_app.route("/stream")
def video_feed():
    return Response(
        generate_stream_bytes(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def get_monitor_position(index=1):
    try:
        monitors = get_monitors()
        if index < len(monitors):
            return monitors[index].x, monitors[index].y
    except Exception:
        pass
    return 0, 0

def mirror_window():
    window_open = False
    fullscreen = False
    win_name = "Mirror - Headset Window"
    alt_enter_prev = False
    pre_monitor_index = None

    while True:
        settings = settings_core.get_settings()
        enabled = settings.get("mirror window", False)

        if not enabled:
            if window_open:
                cv2.destroyWindow(win_name)
                window_open = False
                fullscreen = False
                alt_enter_prev = False
            time.sleep(0.2)
            continue

        _ensure_capture_running()

        current_monitor_index = settings.get("start mirror window monitor index", 1)

        if not window_open:
            cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
            window_open = True
            x, y = get_monitor_position(current_monitor_index)
            cv2.moveWindow(win_name, x, y)

            fullscreen = settings.get("start mirror window fullscreen", False)
            if fullscreen:
                cv2.setWindowProperty(
                    win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                )
            pre_monitor_index = current_monitor_index

        if latest_raw_frame is not None:
            cv2.imshow(win_name, latest_raw_frame)
        else:
            blank_placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank_placeholder,
                "Waiting for Headset Window...",
                (50, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.imshow(win_name, blank_placeholder)

        cv2.waitKey(1)

        alt_held = win32api.GetAsyncKeyState(0x12) & 0x8000
        enter_held = win32api.GetAsyncKeyState(0x0D) & 0x8000
        alt_enter_now = bool(alt_held and enter_held)

        if alt_enter_now and not alt_enter_prev:
            fullscreen = not fullscreen
            prop = cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
            cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, prop)

        alt_enter_prev = alt_enter_now

        if pre_monitor_index != current_monitor_index:
            x, y = get_monitor_position(current_monitor_index)
            cv2.moveWindow(win_name, x, y)
            pre_monitor_index = current_monitor_index


def mirror_web():
    flask_started = False

    while True:
        settings = settings_core.get_settings()
        enabled = settings.get("mirror web", False)

        if not enabled:
            time.sleep(0.5)
            continue

        _ensure_capture_running()

        if not flask_started:
            port = settings.get("mirror web port", 9999)
            flask_started = True
            local_ip = get_local_ip()
            print("=" * 70)
            print(f"  LOCAL ACCESS URL:   http://localhost:{port}/")
            print(f"  NETWORK STREAM URL: http://{local_ip}:{port}/")
            print("=" * 70)

            threading.Thread(
                target=lambda: flask_app.run(
                    host="0.0.0.0",
                    port=port,
                    threaded=True,
                    debug=False,
                    use_reloader=False,
                ),
                daemon=True,
            ).start()

        time.sleep(1)


def start_mirror_window():
    threading.Thread(target=mirror_window, daemon=True).start()


def start_mirror_web():
    threading.Thread(target=mirror_web, daemon=True).start()