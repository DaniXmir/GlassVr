#https://steamcommunity.com/app/358720/discussions/0/357287304432957721
#https://www.reddit.com/r/gamedev/comments/6u7p6s/using_openvr_is_there_any_way_to_get_tracked_hmd/

import openvr as vr
import time
import threading
import numpy as np
from scipy.spatial.transform import Rotation as R
import json

file_path = 'settings.json'

controller_arr = []
tracker_arr = []

def get_default_settings():
    return {
    "ip address": "127.0.0.1",
    "port": 9999,
    
    "controller/tracker": "controller",
    "index": 1,

    "ipd": 0.0,
    "head to eye dist" : 0.0,
    
    "offsets": {
        "position x": 0,
        "position y": 0.0,
        "position z": 0.0,

        "rotation yaw": 0.0,
        "rotation pitch": 0.0,
        "rotation roll": 0.0
        }
    }
    
class values:
    def __init__(self):
        self.vr_system = None
        self.init_vr()
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def init_vr(self):
        try:
            vr.init(vr.VRApplication_Utility)
            self.vr_system = vr.VRSystem()
        except vr.OpenVRError:
            self.vr_system = None

    def __del__(self):
        self.stop()
        try:
            vr.shutdown()
        except:
            pass

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None

    def _worker(self):
        last_scan_time = 0
        while self.running:
            if time.time() - last_scan_time > 1.0:
                self.get_controllers_and_trackers()
                last_scan_time = time.time()
            
            settings = self.get_settings()
            to_use = settings.get("controller/tracker", "controller")
            
            if to_use == "tracker":
                devices = tracker_arr
            elif to_use == "controller":
                devices = controller_arr
            else:
                devices = []
            
            target_index = -1
            
            if len(devices) > 0:
                idx = settings['index']
                if idx < len(devices):
                    target_index = devices[idx]

            new_data = self.get_device_position(target_index)

            with self.lock:
                self.current_data = new_data
            
            time.sleep(0.008)

    def get_controllers_and_trackers(self):
        controller_arr.clear()
        tracker_arr.clear()

        if not self.vr_system:
            return

        for i in range(vr.k_unMaxTrackedDeviceCount):
            device_class = self.vr_system.getTrackedDeviceClass(i)
            if device_class == vr.TrackedDeviceClass_Controller:
                controller_arr.append(i)
            if device_class == vr.TrackedDeviceClass_GenericTracker:
                tracker_arr.append(i)

    def get_settings(self):
        DEFAULT_SETTINGS = get_default_settings()
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            try:
                with open(file_path, 'w') as f:
                    json.dump(DEFAULT_SETTINGS, f, indent=4)
            except OSError:
                pass
            return DEFAULT_SETTINGS
        except Exception:
            return DEFAULT_SETTINGS
        
    def get_device_position(self, device_index=-1):
            settings = self.get_settings()
            
            data = {
                "position x": 0.0 + settings['offsets']['position x'],
                "position y": 0.0 + settings['offsets']['position y'],
                "position z": 0.0 + settings['offsets']['position z'],
                "rotation w": 1.0,
                "rotation x": 0.0 + settings['offsets']['rotation yaw'],
                "rotation y": 0.0 + settings['offsets']['rotation pitch'],
                "rotation z": 0.0 + settings['offsets']['rotation roll']
            }

            try:
                to_use = settings.get("controller/tracker", "controller")
                if to_use == "tracker" and len(tracker_arr) == 0:
                    return data
                elif to_use == "controller" and len(controller_arr) == 0:
                    return data

                if device_index == -1:
                    return data

                if not self.vr_system:
                    return data
                
                #keep the first argument as 2, do not change it
                poses = self.vr_system.getDeviceToAbsoluteTrackingPose(
                    2, 0.0, vr.k_unMaxTrackedDeviceCount
                )
                
                if device_index >= len(poses):
                    return data

                pose = poses[device_index]
                
                if pose.bDeviceIsConnected and pose.bPoseIsValid:
                    m = pose.mDeviceToAbsoluteTracking
                    
                    rotation_matrix = np.array([
                        [m[0][0], m[0][1], m[0][2]],
                        [m[1][0], m[1][1], m[1][2]],
                        [m[2][0], m[2][1], m[2][2]]
                    ])
                    
                    pos_x_world = m[0][3]
                    pos_y_world = m[1][3]
                    pos_z_world = m[2][3]

                    data["position x"] = pos_x_world + settings['offsets']['position x']
                    data["position y"] = pos_y_world + settings['offsets']['position y']
                    data["position z"] = pos_z_world + settings['offsets']['position z']

                    device_rotation = R.from_matrix(rotation_matrix)

                    offset_angles_rad = [
                        settings['offsets']['rotation yaw'],
                        settings['offsets']['rotation pitch'],
                        settings['offsets']['rotation roll']
                    ]
                    
                    offset_rotation = R.from_euler('ZYX', offset_angles_rad, degrees=False)

                    final_rotation = device_rotation * offset_rotation

                    quat_final = final_rotation.as_quat()

                    data["rotation x"] = quat_final[0]
                    data["rotation y"] = quat_final[1]
                    data["rotation z"] = quat_final[2]
                    data["rotation w"] = quat_final[3]
                    
                    return data

            except Exception:
                return data