#gets data from steamvr like position, serial, etc...
#gets data slower the driver so avoid if can for tracking! TODO: move hand tracking sync to the driver side while keeping cv in python

#use svr.get_trackers_dict() to get devices!

import time
import threading
import numpy as np
import openvr as vr
from scipy.spatial.transform import Rotation as R

trackers_dict = {}
trackers_arr = []

_lock = threading.Lock()
_vr_thread = None
_vr_running = False

def is_process_running(process_name):
    import psutil
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def _update_vr_loop():
    global trackers_dict, trackers_arr, _vr_running
    
    can_enter = True

    while True:
        process_active = is_process_running("vrserver.exe")

        if can_enter and process_active:
            can_enter = False
            _vr_running = True
            _run_vr_session()

        if not can_enter and not process_active:
            can_enter = True
            _vr_running = False
            with _lock:
                trackers_dict.clear()
                trackers_arr.clear()
            vr.shutdown()

        time.sleep(1)

def _run_vr_session():
    global trackers_dict, trackers_arr

    try:
        vr.init(vr.VRApplication_Utility)
        vr_system = vr.VRSystem()
        
        PROP_SERIAL = vr.Prop_SerialNumber_String
        PROP_MODEL = vr.Prop_ControllerType_String
        PROP_RENDER = vr.Prop_RenderModelName_String

        while is_process_running("vrserver.exe"):
            try:
                poses = vr_system.getDeviceToAbsoluteTrackingPose(2, 0.0, vr.k_unMaxTrackedDeviceCount)
                
                current_frame_dict = {}
                current_frame_arr = []

                for i in range(vr.k_unMaxTrackedDeviceCount):
                    device_class = vr_system.getTrackedDeviceClass(i)
                    
                    if device_class in (vr.TrackedDeviceClass_HMD, 
                                      vr.TrackedDeviceClass_Controller, 
                                      vr.TrackedDeviceClass_GenericTracker, 
                                      vr.TrackedDeviceClass_TrackingReference):
                        
                        serial = vr_system.getStringTrackedDeviceProperty(i, PROP_SERIAL)
                        model = vr_system.getStringTrackedDeviceProperty(i, PROP_MODEL)
                        render = vr_system.getStringTrackedDeviceProperty(i, PROP_RENDER)
                        
                        role_hint = "Unknown"
                        if device_class in (vr.TrackedDeviceClass_Controller, vr.TrackedDeviceClass_GenericTracker):
                            role_enum = vr_system.getControllerRoleForTrackedDeviceIndex(i)
                            role_map = {
                                vr.TrackedControllerRole_LeftHand: "LeftHand",
                                vr.TrackedControllerRole_RightHand: "RightHand",
                                vr.TrackedControllerRole_OptOut: "OptOut",
                                vr.TrackedControllerRole_Treadmill: "Treadmill",
                                vr.TrackedControllerRole_Stylus: "Stylus"
                            }
                            role_hint = role_map.get(role_enum, "Tracker/Controller")
                        elif device_class == vr.TrackedDeviceClass_HMD:
                            role_hint = "HMD"
                        elif device_class == vr.TrackedDeviceClass_TrackingReference:
                            role_hint = "BaseStation"

                        pose = poses[i]
                        is_connected = pose.bDeviceIsConnected
                        is_valid = pose.bPoseIsValid

                        device_data = {
                            "index": i,
                            "class": device_class,
                            "model": model,
                            "render": render,
                            "role": role_hint,
                            "connected": is_connected,
                            "pose_valid": is_valid,
                            "serial": serial
                        }

                        if is_connected and is_valid:
                            m = pose.mDeviceToAbsoluteTracking
                            
                            pos_x, pos_y, pos_z = float(m[0][3]), float(m[1][3]), float(m[2][3])
                            
                            rotation_matrix = np.array([
                                [m[0][0], m[0][1], m[0][2]],
                                [m[1][0], m[1][1], m[1][2]],
                                [m[2][0], m[2][1], m[2][2]]
                            ])

                            yaw, pitch, roll = R.from_matrix(rotation_matrix).as_euler('yxz', degrees=True)

                            device_data.update({
                                "pos x": pos_x,
                                "pos y": pos_y,
                                "pos z": pos_z,
                                "rotation matrix": rotation_matrix,
                                "yaw": yaw,
                                "pitch": pitch,
                                "roll": roll
                            })

                            current_frame_arr.append(device_data)

                        current_frame_dict[serial] = device_data

                with _lock:
                    trackers_dict = current_frame_dict
                    trackers_arr = current_frame_arr

                time.sleep(0.001)

            except Exception:
                time.sleep(0.01)
                continue

    except Exception:
        time.sleep(1)

def start():
    global _vr_thread
    if _vr_thread is None or not _vr_thread.is_alive():
        _vr_thread = threading.Thread(target=_update_vr_loop, daemon=True)
        _vr_thread.start()

def is_running():
    return _vr_running

def get_trackers_dict():
    with _lock:
        return dict(trackers_dict)

def get_trackers_arr():
    with _lock:
        return list(trackers_arr)

start()