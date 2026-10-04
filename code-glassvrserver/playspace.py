#udp playspace sync

import time
import math
import socket
import threading
import settings as settings_core
import controller_handler
import steamvr as svr
from udp_relay import get_latest_packet
import controller_handler as sdl

def send_reset_to_phone(device: str):
    try:
        settings = settings_core.get_settings()
        port = settings.get(f"{device} port", 9001)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"RESET", ("<broadcast>", port))
        sock.close()
    except Exception:
        pass


def reset_playspace(device: str):
    settings = settings_core.get_settings()
    reset_method = settings.get(f"{device} playspace reset method", "Headset")

    match reset_method:
        case "Headset":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)

            trackers = svr.get_trackers_dict()
            hmd_dict = list(trackers.values())[0] if trackers else {}

            raw_p_packet = get_latest_packet(device, 'P') or {"x": ps_x, "y": 0.0, "z": ps_z}
            raw_r_packet = get_latest_packet(device, 'R') or {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

            hmd_x = hmd_dict.get('pos x', 0.0) if hmd_dict else 0.0
            hmd_y = hmd_dict.get('pos y', 0.0) if hmd_dict else 0.0
            hmd_z = hmd_dict.get('pos z', 0.0) if hmd_dict else 0.0

            hmd_yaw = 0.0
            if hmd_dict and 'rotation matrix' in hmd_dict:
                hmd_mat = hmd_dict['rotation matrix']
                hmd_yaw = math.atan2(hmd_mat[0][2], hmd_mat[0][0])

            ps_yaw = hmd_yaw

            w = raw_r_packet["w"]
            x = raw_r_packet["x"]
            y = raw_r_packet["y"]
            z = raw_r_packet["z"]
            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            cos_hmd = math.cos(hmd_yaw)
            sin_hmd = math.sin(hmd_yaw)
            unrotated_hmd_x = hmd_x * cos_hmd - hmd_z * sin_hmd
            unrotated_hmd_z = hmd_x * sin_hmd + hmd_z * cos_hmd

            mid_x = unrotated_hmd_x + ps_x
            mid_y = hmd_y + ps_y
            mid_z = unrotated_hmd_z + ps_z

            offset_x = mid_x - raw_p_packet.get("x", 0.0)
            offset_y = mid_y - raw_p_packet.get("y", 0.0)
            offset_z = mid_z - raw_p_packet.get("z", 0.0)

            settings_core.update_setting(f"{device} playspace yaw", ps_yaw)
            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)
            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

        case "Fixed Position":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)

            raw_p_packet = get_latest_packet(device, 'P') or {"x": 0.0, "y": 0.0, "z": 0.0}
            raw_r_packet = get_latest_packet(device, 'R') or {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

            w = raw_r_packet["w"]
            x = raw_r_packet["x"]
            y = raw_r_packet["y"]
            z = raw_r_packet["z"]
            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            mid_x = ps_x
            mid_y = ps_y
            mid_z = ps_z

            offset_x = mid_x - raw_p_packet.get("x", 0.0)
            offset_y = mid_y - raw_p_packet.get("y", 0.0)
            offset_z = mid_z - raw_p_packet.get("z", 0.0)

            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)
            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

        case "QR":
            ps_x = settings.get(f"{device} playspace x", 0.0)
            ps_y = settings.get(f"{device} playspace y", 0.0)
            ps_z = settings.get(f"{device} playspace z", 0.0)

            raw_p_packet = get_latest_packet(device, 'P') or {"x": 0.0, "y": 0.0, "z": 0.0}

            transform = controller_handler.get_hand_world_transform("cr")
            w, x, y, z = transform["rot w"], transform["rot x"], transform["rot y"], transform["rot z"]

            w_prime = w + x
            y_prime = y - z
            raw_yaw = 2.0 * math.atan2(y_prime, w_prime)

            world_offset_yaw = -raw_yaw
            world_offset_yaw = (world_offset_yaw + math.pi) % (2 * math.pi) - math.pi

            offset_x = ps_x - transform["pos x"]
            offset_y = ps_y - transform["pos y"]
            offset_z = ps_z - transform["pos z"]

            settings_core.update_setting(f"{device} offset world yaw", world_offset_yaw)
            settings_core.update_setting(f"{device} offset world x", offset_x)
            settings_core.update_setting(f"{device} offset world y", offset_y)
            settings_core.update_setting(f"{device} offset world z", offset_z)

    try:
        import elements
        elements.update_all()
    except Exception:
        pass

    if hasattr(svr, "ui_updater") and hasattr(svr.ui_updater, "trigger_ui_update"):
        svr.ui_updater.trigger_ui_update.emit()

def trigger_ui_reset(device: str):
    send_reset_to_phone(device)
    reset_playspace(device)

def reset_playspace_on_input():
    device_states = {}

    while True:
        try:
            settings = settings_core.get_settings()
            devices = ["hmd", "cr", "cl"]

            for i in range(settings.get("trackers num", 2)):
                devices.append(f"{i}tracker")

            for n in devices:
                if n not in device_states:
                    device_states[n] = {"packet_triggered": False, "ui_triggered": False}

                raw_e_packet = get_latest_packet(n, 'E')
                packet_reset_requested = raw_e_packet.get("reset", False) if raw_e_packet else False

                packet_fired = False
                if packet_reset_requested:
                    if not device_states[n]["packet_triggered"]:
                        packet_fired = True
                        device_states[n]["packet_triggered"] = True
                else:
                    device_states[n]["packet_triggered"] = False

                setting_key = f"{n}_reset playspace"
                bind_data = settings.get(setting_key, {})
                ui_reset_requested = False

                if isinstance(bind_data, dict) and "eval_binding" in globals():
                    ui_binding_expr = bind_data.get("buttons", [])
                    if ui_binding_expr:
                        ui_reset_requested = bool(sdl.eval_binding(ui_binding_expr))

                ui_fired = False
                if ui_reset_requested:
                    if not device_states[n]["ui_triggered"]:
                        ui_fired = True
                        device_states[n]["ui_triggered"] = True
                else:
                    device_states[n]["ui_triggered"] = False

                if packet_fired:
                    reset_playspace(n)
                elif ui_fired:
                    trigger_ui_reset(n)

            time.sleep(0.001)

        except Exception:
            time.sleep(0.001)


def start_reset_playspace():
    thread = threading.Thread(target=reset_playspace_on_input, daemon=True, name="Playspace_Reset_Watcher")
    thread.start()

start_reset_playspace()