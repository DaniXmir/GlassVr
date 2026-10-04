#hand tracking main!
#kinda bad so if you think you can improve this plz go ahead!

import time
import threading

import numpy as np
import cv2
from cvzone.HandTrackingModule import HandDetector
from scipy.spatial.transform import Rotation as R

import settings as se
import steamvr as svr

SHOW_FEED           = True
RESOLUTION_X        = 640
RESOLUTION_Y        = 480
SWAP_HANDS_MODE     = False

REFERENCE_DEPTH_CM  = 0.5
REFERENCE_BBOX = 200.0

ref_3d_mag_right    = 0.08
ref_3d_mag_left     = 0.08

hand_data = {
    "l flexion": [0.0] * 20,
    "l splay":   [0.0] * 5,
    "l pos x": 0.0, "l pos y": 0.0, "l pos z": 0.0,
    "l rot x": 0.0, "l rot y": 0.0, "l rot z": 0.0, "l rot w": 1.0,

    "r flexion": [0.0] * 20,
    "r splay":   [0.0] * 5,
    "r pos x": 0.0, "r pos y": 0.0, "r pos z": 0.0,
    "r rot x": 0.0, "r rot y": 0.0, "r rot z": 0.0, "r rot w": 1.0,
}

camera_running = False
camera_thread  = None
camera_ready   = threading.Event()

def _vec(l1, l2):
    return np.array([l2[0]-l1[0], l2[1]-l1[1], l2[2]-l1[2]], dtype=float)


def _angle(v1, v2):
    n = np.linalg.norm(v1) * np.linalg.norm(v2)
    return np.arccos(np.clip(np.dot(v1, v2) / n, -1.0, 1.0)) if n > 1e-9 else 0.0


def _norm01(v, lo, hi):
    return float(np.clip((v - lo) / (hi - lo), 0.0, 1.0)) if hi != lo else 0.0

def _mat_to_quat(m):
    tr = m[0,0] + m[1,1] + m[2,2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        return (m[2,1]-m[1,2])/s, (m[0,2]-m[2,0])/s, (m[1,0]-m[0,1])/s, 0.25*s
    elif (m[0,0] > m[1,1]) and (m[0,0] > m[2,2]):
        s = np.sqrt(1.0 + m[0,0] - m[1,1] - m[2,2]) * 2
        return 0.25*s, (m[0,1]+m[1,0])/s, (m[0,2]+m[2,0])/s, (m[2,1]-m[1,2])/s
    elif m[1,1] > m[2,2]:
        s = np.sqrt(1.0 + m[1,1] - m[0,0] - m[2,2]) * 2
        return (m[0,1]+m[1,0])/s, 0.25*s, (m[1,2]+m[2,1])/s, (m[0,2]-m[2,0])/s
    else:
        s = np.sqrt(1.0 + m[2,2] - m[0,0] - m[1,1]) * 2
        return (m[0,2]+m[2,0])/s, (m[1,2]+m[2,1])/s, 0.25*s, (m[1,0]-m[0,1])/s

FINGER_BASES  = [1, 5, 9, 13, 17]
FINGER_TIPS   = [4, 8, 12, 16, 20]
FINGER_MIDS   = [3, 7, 11, 15, 19]

FLEXION_MIN, FLEXION_MAX     = 0.0, 20.5
SPLAY_THUMB_MIN,  SPLAY_THUMB_MAX  = 0.0, 20.0
SPLAY_FINGER_MIN, SPLAY_FINGER_MAX = 0.0, 20.35

def _process_hand(lm_list, is_right, img_w, img_h):
    prefix = "r" if is_right else "l"

    P = [(r[0], r[1]) for r in lm_list]

    P3 = [(r[0]/img_w, 1.0-(r[1]/img_h), -r[2]) for r in lm_list]

    #pos////////////////////////////////////////////////////////////////////////////////////////////
    wx, wy = P[0]
    hand_data[f"{prefix} pos x"] = wx / img_w
    hand_data[f"{prefix} pos y"] = 1.0 - (wy / img_h)

    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    bbox_size = max(max(xs) - min(xs), max(ys) - min(ys))
    raw_z = -(REFERENCE_DEPTH_CM * REFERENCE_BBOX / bbox_size) if bbox_size > 1 else -REFERENCE_DEPTH_CM
    hand_data[f"{prefix} pos z"] = raw_z

    #rot////////////////////////////////////////////////////////////////////////////////////////////
    p_wrist  = np.array(P3[0],  dtype=float)
    p_index  = np.array(P3[5],  dtype=float)
    p_middle = np.array(P3[9],  dtype=float)
    p_pinky  = np.array(P3[17], dtype=float)

    v_fwd_raw = p_middle - p_wrist
    v_fwd_raw /= np.linalg.norm(v_fwd_raw) + 1e-6
    v_z = -v_fwd_raw

    if is_right:
        v_right_raw = p_pinky - p_index
    else:
        v_right_raw = p_index - p_pinky
    v_right_raw /= np.linalg.norm(v_right_raw) + 1e-6

    v_y = np.cross(v_z, v_right_raw)
    v_y /= np.linalg.norm(v_y) + 1e-6

    v_x = np.cross(v_y, v_z)
    v_x /= np.linalg.norm(v_x) + 1e-6

    mat = np.stack([v_x, v_y, v_z], axis=1)
    qx, qy, qz, qw = _mat_to_quat(mat)

    if v_x[2] > 0:
        qx, qy, qz, qw = -qx, -qy, -qz, -qw

    hand_data[f"{prefix} rot x"] = qx
    hand_data[f"{prefix} rot y"] = qy
    hand_data[f"{prefix} rot z"] = qz
    hand_data[f"{prefix} rot w"] = qw

    #curl////////////////////////////////////////////////////
    finger_lms = [
        (1,  2,  3,  4),
        (5,  6,  7,  8),
        (9,  10, 11, 12),
        (13, 14, 15, 16),
        (17, 18, 19, 20),
    ]
    flexion = [0.0] * 20
    curl_values = []

    for fi, (base, k1, k2, tip) in enumerate(finger_lms):
        pb   = np.array(P[base], dtype=float)
        pk1  = np.array(P[k1],   dtype=float)
        ptip = np.array(P[tip],  dtype=float)

        if fi == 0:
            p1, p2, p3, p4 = [np.array(P[i], dtype=float) for i in range(1, 5)]
            total_angle = _angle(p1-p2, p3-p2) + _angle(p2-p3, p4-p3)
            curl = _norm01(total_angle, 6.0, 4.5)
            flexion[fi * 4] = curl
            curl_values.append(curl)
        else:
            seg_len  = np.linalg.norm(pk1 - pb)
            extended = seg_len * 3.0
            actual   = np.linalg.norm(ptip - pb)
            curl     = 1.0 - np.clip(actual / (extended + 1e-6), 0.0, 1.0)
            flexion[fi * 4] = curl
            curl_values.append(curl)

    hand_data[f"{prefix} flexion"] = flexion

    #curl also affect pos, that a bug, this should fix that (it did not :( )///////////////////////////////////////////////////////////////////
    wx, wy = P[0]
    hand_data[f"{prefix} pos x"] = wx / img_w
    hand_data[f"{prefix} pos y"] = 1.0 - (wy / img_h)

    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    bbox_size = max(max(xs) - min(xs), max(ys) - min(ys))
    raw_z = -(REFERENCE_DEPTH_CM * REFERENCE_BBOX / bbox_size) if bbox_size > 1 else -REFERENCE_DEPTH_CM

    global_min_curl = min(curl_values)

    z_offset = global_min_curl * 0.28
    final_z = raw_z + z_offset

    hand_data[f"{prefix} pos z"] = final_z

    #splay/////////////////////////////////////////////////////////////////////////////////
    splay_range = 0.1
    splay = [0.0] * 5

    p_w = np.array(P3[0], dtype=float)
    tips = [
        np.array(P3[4], dtype=float),#thumb
        np.array(P3[8], dtype=float),#index
        np.array(P3[12], dtype=float),#mid
        np.array(P3[16], dtype=float),#ring
        np.array(P3[20], dtype=float)#pinky
    ]

    def get_angle(t1, t2, wrist):
        v1, v2 = t1 - wrist, t2 - wrist
        u1 = v1 / (np.linalg.norm(v1) + 1e-6)
        u2 = v2 / (np.linalg.norm(v2) + 1e-6)
        return np.arccos(np.clip(np.dot(u1, u2), -1.0, 1.0))

    def map_splay_dynamic(angle, min_a, max_a, r_scale):
        n = (angle - min_a) / (max_a - min_a + 1e-6)
        n = np.clip(n, 0.0, 1.0)

        return ((n ** 0.3) * 2.0 - 1.0) * r_scale

    splay[0] = map_splay_dynamic(get_angle(tips[0], tips[1], p_w), 0.10, 0.40, splay_range)
    splay[1] = map_splay_dynamic(get_angle(tips[1], tips[2], p_w), 0.05, 0.20, splay_range)*5
    splay[2] = map_splay_dynamic(get_angle(tips[2], tips[3], p_w), 0.05, 0.18, splay_range)*5
    splay[3] = map_splay_dynamic(get_angle(tips[3], tips[4], p_w), 0.05, 0.20, splay_range)*5
    splay[4] = map_splay_dynamic(get_angle(tips[3], tips[4], p_w), 0.05, 0.22, splay_range)*5

    hand_data[f"{prefix} splay"] = splay

hand_side_buffer = [0, 0]
side_threshold = 1
last_known_x = {"l": 0.1, "r": 0.9}

def camera_loop():
    #todo: improve hand tracking: make side detection less aggressive(if only right is enabled then the hand can only be right)
    global camera_running, last_known_x

    try:
        idx = se.get_settings().get("camera index", 0)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            camera_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  RESOLUTION_X)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_Y)

        detector = HandDetector(maxHands=2, detectionCon=0.5, minTrackCon=0.5)
        camera_ready.set()

        while camera_running:
            success, image = cap.read()
            if not success:
                time.sleep(0.001)
                continue

            try:
                hands_found, image = detector.findHands(image, draw=True)
            except Exception:
                continue

            if hands_found:
                h, w = image.shape[:2]
                num_hands = len(hands_found)

                current_hands = []
                for i in range(num_hands):
                    raw_lms = detector.results.multi_hand_landmarks[i].landmark
                    current_hands.append({
                        "x": raw_lms[0].x,
                        "raw_lms": raw_lms
                    })

                assignments = []
                if num_hands == 2:
                    sorted_hands = sorted(current_hands, key=lambda x: x["x"])
                    assignments = [("l", sorted_hands[0]), ("r", sorted_hands[1])]
                else:
                    hand = current_hands[0]
                    dist_l = abs(hand["x"] - last_known_x["l"])
                    dist_r = abs(hand["x"] - last_known_x["r"])
                    side = "l" if dist_l < dist_r else "r"
                    assignments = [(side, hand)]

                for side, hand_info in assignments:
                    prefix = side
                    is_right = (side == "r")
                    label = "Right" if is_right else "Left"

                    last_known_x[side] = hand_info["x"]

                    lm = [[int(l.x * w), int(l.y * h), l.z] for l in hand_info["raw_lms"]]
                    _process_hand(lm, is_right, w, h)

                    try:
                        px, py, pz = hand_data[f"{prefix} pos x"], hand_data[f"{prefix} pos y"], hand_data[f"{prefix} pos z"]
                        rx, ry, rz, rw = hand_data[f"{prefix} rot x"], hand_data[f"{prefix} rot y"], hand_data[f"{prefix} rot z"], hand_data[f"{prefix} rot w"]
                        fl = hand_data[f"{prefix} flexion"]
                        sp = hand_data[f"{prefix} splay"]

                        cx, cy = lm[0][0], lm[0][1]
                        lines = [
                            f"{label} pos x:{px:.2f} y:{py:.2f} z:{pz:.3f}",
                            f"rot x:{rx:.2f} y:{ry:.2f} z:{rz:.2f} w:{rw:.2f}",
                            f"flex T:{fl[0]:.2f} I:{fl[4]:.2f} M:{fl[8]:.2f} R:{fl[12]:.2f} P:{fl[16]:.2f}",
                            f"splay T:{sp[0]:.2f} I:{sp[1]:.2f} M:{sp[2]:.2f} R:{sp[3]:.2f} P:{sp[4]:.2f}",
                        ]
                        for j, line in enumerate(lines):
                            cv2.putText(image, line, (cx, cy - 20 - j*18),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0), 1)
                    except KeyError:
                        continue

            if SHOW_FEED:
                cv2.imshow("Hand Tracking", image)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    camera_running = False

            time.sleep(0.0001)

    except Exception:
        camera_running = False
    finally:
        cap.release()
        cv2.destroyAllWindows()

def start_camera():
    global camera_running, camera_thread

    if camera_running:
        return

    camera_ready.clear()
    camera_running = True
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()

    if not camera_ready.wait(timeout=3.0):
        camera_running = False

def stop_camera():
    global camera_running

    if not camera_running:
        return

    camera_running = False
    if camera_thread:
        camera_thread.join(timeout=2.0)

def _get_hmd_device_data():
    for device_data in svr.trackers_dict.values():
        if device_data.get("role") == "HMD" and "pos x" in device_data:
            return device_data
    return None


def get_hand_world_transform(device):
    try:
        hand_prefix = 'r' if device == "cr" else 'l'

        settings = se.get_settings()
        cam_offset_x = settings.get('camera offset x', 0.0)
        cam_offset_y = settings.get('camera offset y', 0.0)
        cam_offset_z = settings.get('camera offset z', 0.0)
        outer_stereo  = settings.get('outer stereo',  41.070)
        inner_stereo  = settings.get('inner stereo',  41.070)
        top_stereo    = settings.get('top stereo',    26.120)
        bottom_stereo = settings.get('bottom stereo', 26.120)

        fov_horizontal = outer_stereo + inner_stereo
        fov_vertical   = top_stereo  + bottom_stereo

        hmd_data = _get_hmd_device_data()
        if hmd_data is None:
            raise ValueError("no HMD found in svr.trackers_dict")

        hmd_pos = np.array([
            hmd_data['pos x'],
            hmd_data['pos y'],
            hmd_data['pos z']
        ])
        hmd_rot = R.from_matrix(hmd_data['rotation matrix'])

        screen_x = hand_data[f'{hand_prefix} pos x']
        screen_y = hand_data[f'{hand_prefix} pos y']
        depth    = abs(hand_data[f'{hand_prefix} pos z'])

        ndc_x = (screen_x - 0.5) * 2.0
        ndc_y = (screen_y - 0.5) * 2.0

        fov_h_rad = np.radians(fov_horizontal / 2)
        fov_v_rad = np.radians(fov_vertical   / 2)

        cam_pos = np.array([
            depth * np.tan(fov_h_rad) * ndc_x,
            depth * np.tan(fov_v_rad) * ndc_y,
            -depth
        ])

        cam_mount = np.array([cam_offset_x, cam_offset_y, cam_offset_z])
        world_pos = hmd_pos + hmd_rot.apply(cam_mount + cam_pos)

        hand_rot_local = R.from_quat([
            hand_data[f'{hand_prefix} rot x'],
            hand_data[f'{hand_prefix} rot y'],
            hand_data[f'{hand_prefix} rot z'],
            hand_data[f'{hand_prefix} rot w']
        ])

        #hardcoded offsets
        if hand_prefix == "r":
            offset_yaw   = 1.660 + settings.get(f'{device} offset world yaw',   0.0)
            offset_pitch = -0.680 + settings.get(f'{device} offset world pitch', 0.0)
            offset_roll  = 0.670 + settings.get(f'{device} offset world roll',  0.0)
        else:
            offset_yaw   = -1.660 + settings.get(f'{device} offset world yaw',   0.0)
            offset_pitch = 0.680 + settings.get(f'{device} offset world pitch', 0.0)
            offset_roll  = 0.670 + settings.get(f'{device} offset world roll',  0.0)

        offset_rot   = R.from_euler('ZYX', [offset_yaw, offset_pitch, offset_roll], degrees=False)

        world_rot  = hmd_rot * hand_rot_local * offset_rot
        final_quat = world_rot.as_quat()

        return {
            "pos x": world_pos[0],
            "pos y": world_pos[1],
            "pos z": world_pos[2],
            "rot x": final_quat[0],
            "rot y": final_quat[1],
            "rot z": final_quat[2],
            "rot w": final_quat[3]
        }

    except Exception:
        return {
            "pos x": 0.0,
            "pos y": 0.0,
            "pos z": 0.0,
            "rot x": 0.0,
            "rot y": 0.0,
            "rot z": 0.0,
            "rot w": 1.0
        }