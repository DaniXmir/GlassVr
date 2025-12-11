from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

import sys
import shutil
import psutil
import os
import json
import struct
import time
import socket
import threading
import openvr as vr
import numpy as np
from scipy.spatial.transform import Rotation as R

import settings_core

app = QApplication([])#sys.argv)

window = QTabWidget()
#window.setWindowTitle("PuffinVR")
window.setWindowTitle("GlassVR")
window.resize(800, 600)

#core/////////////////////////////////////////////////////////////////////////////////////////////////////////////
# layout_main.addWidget(create_group_label([{"text" : "a", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "b", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "c", "alignment" : Qt.AlignmentFlag.AlignCenter}]))
# layout_main.addWidget(create_group_button([{"text" : "a", "enabled" : True},{"text" : "b", "enabled" : True},{"text" : "c", "enabled" : False}]))
# layout_main.addWidget(create_group_checkbox([{"text" : "a", "checked" : True},{"text" : "a", "checked" : False}]))
# layout_main.addWidget(create_group_spinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))
# layout_main.addWidget(create_group_doublespinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))

def create_label(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(dict['alignment'])
    group_layout.addWidget(label)

    return group_widget

def create_group_label(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_label(dict))

        return group_widget

def create_button(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    button = QPushButton(dict['text'])
    if 'func' in dict:
        button.clicked.connect(lambda: dict['func']())
    button.setEnabled(dict['enabled'])

    group_layout.addWidget(button)

    return group_widget

def create_group_button(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_button(dict))

        return group_widget

def create_checkbox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    group_layout.addWidget(label)

    checkbox = QCheckBox()
    checkbox.setChecked(dict['default'])
    if 'func' in dict:
        checkbox.clicked.connect(lambda: dict['func']())#dict))
    group_layout.addWidget(checkbox)

    return group_widget

def create_group_checkbox(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_checkbox(dict))

        return group_widget

def create_spinbox(dict):#text = "", min = -1, max = -1, default = 0):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    spinbox = QSpinBox()
    spinbox.setRange(dict['min'], dict['max'])
    spinbox.setValue(dict['default'])
    spinbox.setSingleStep(dict['steps'])
    if 'func' in dict:
        spinbox.valueChanged.connect(lambda: dict['func']())
    group_layout.addWidget(spinbox)

    return group_widget

def create_group_spinbox(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_spinbox(dict))

        return group_widget

def create_doublespinbox(dict):#text = "", min = -1, max = -1, default = 0):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    spinbox = QDoubleSpinBox()
    spinbox.setRange(dict['min'], dict['max'])
    spinbox.setValue(dict['default'])
    spinbox.setSingleStep(dict['steps'])
    if 'func' in dict:
        spinbox.valueChanged.connect(lambda: dict['func']())
    group_layout.addWidget(spinbox)

    return group_widget

def create_group_doublespinbox(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_doublespinbox(dict))

        return group_widget
    
def create_lineedit(dict):#text = "", min = -1, max = -1, default = 0):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict['text'])
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    lineedit = QLineEdit()
    lineedit.setText(dict['default'])
    if 'func' in dict:
        lineedit.textChanged.connect(lambda: dict['func']())
    group_layout.addWidget(lineedit)

    return group_widget

def create_group_lineedit(arr = []):#[{"text" : "hi"},{},{}]
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_lineedit(dict))

        return group_widget

def create_group_horizontal(arr = []):
    if arr:
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)

        for dict in arr:
            match dict['type']:
                case "label":
                    group_layout.addWidget(create_label(dict))
                case "button":
                    group_layout.addWidget(create_button(dict))
                case "checkbox":
                    group_layout.addWidget(create_checkbox(dict))
                case "spinbox":
                    group_layout.addWidget(create_spinbox(dict))
                case "doublespinbox":
                    group_layout.addWidget(create_doublespinbox(dict))
                case "lineedit":
                    group_layout.addWidget(create_lineedit(dict))
                case "image":
                    group_layout.addWidget(create_image(dict))
        return group_widget
    
def create_image(dict = {}):
    image_label = QLabel()
    image = QPixmap("D:/UltimateFolder0/Gallery-Y/projects/GlassVr/code-glassvrserver/fix.png")
    scaled_pixmap = image.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    image_label.setPixmap(scaled_pixmap)
    image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    return image_label

#core/////////////////////////////////////////////////////////////////////////////////////////////////////////////

# main/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_main = QWidget()
layout_main = QVBoxLayout(tab_main)

first_label = create_label({
    "text" : "steamvr is not running :(", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(first_label)

label2 = create_label({
    "text" : "---------Trackers---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(label2)

trackers_widget =create_spinbox({
        "text" : "0 found", 
        "min":0, 
        "max":999999999, 
        "default": settings_core.get_settings()['tracker index'],
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("tracker index", trackers_widget.findChild(QSpinBox).value())
    })

tracker_dict = {"x" : 0.0,
                "y" : 0.0,
                "z" : 0.0,

                "yaw" : 0.0,
                "pitch" : 0.0,
                "roll" : 0.0,
                "w" : 0.0}

trackers = []

def is_prosses_running(PROCESS_NAME):
    for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == PROCESS_NAME.lower():
                return True
    
    return False

PACK_FORMAT = '<9d'
PACKET_SIZE = struct.calcsize(PACK_FORMAT)

def udp_send():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            settings = settings_core.get_settings()

            pos_x = tracker_dict['x'] + settings['offset x']
            pos_y = tracker_dict['y'] + settings['offset y']
            pos_z = tracker_dict['z'] + settings['offset z']

            rot_w = tracker_dict['w']
            rot_x = tracker_dict['yaw']
            rot_y = tracker_dict['pitch']
            rot_z = tracker_dict['roll']

            ipd = settings['ipd']
            head_to_eye_dist = settings['head to eye dist']

            buffer = struct.pack(
            PACK_FORMAT, 
            pos_x, pos_y, pos_z, 
            rot_w, rot_x, rot_y, rot_z,
            ipd, head_to_eye_dist
            )
            
            sock.sendto(buffer, (settings['ip sending'], settings['port receiving']))

            time.sleep(0)
        except:
            time.sleep(1.0 / 120.0)

def start_t_udp_send():
    t = threading.Thread(target=udp_send, daemon=True)
    t.start()
    return t








def update_vrlabel():
    can_enter = True
    while True:
        #first_label.findChild(QLabel).setText(str(is_prosses_running("vrserver.exe")))

        if can_enter and is_prosses_running("vrserver.exe"):
            can_enter = False

            first_label.findChild(QLabel).setText("steamvr is running!")

            start_vr_utility()
            #print("steamvr opened")

        if not can_enter and not is_prosses_running("vrserver.exe"):
            can_enter = True

            first_label.findChild(QLabel).setText("steamvr is not running :(")

            end_vr_utility()
            #print("steamvr closed")

        time.sleep(1)

def start_t_update_vrlabel():
    t = threading.Thread(target=update_vrlabel, daemon=True)
    t.start()
    return t


def start_vr_utility():
    try:
        vr.init(vr.VRApplication_Utility)
        vr_system = vr.VRSystem()


        while True:
            try:
                trackers = get_trackers(vr_system)
                
                #print connected
                count = 0
                text = str(len(trackers)) + " found= "
                for n in trackers:
                    text += "[" + str(count) + "]"
                    if n['class'] == 2:
                        text += "{controller "
                    if n['class'] == 3:
                        text += "tracker "
                    text += n['model'] + " "
                    text += n['role'] + "} "

                    count += 1
                trackers_widget.findChild(QLabel).setText(text)
                #print connected

                #keep the first argument as 2, do not change it
                poses = vr_system.getDeviceToAbsoluteTrackingPose(
                    2, 0.0, vr.k_unMaxTrackedDeviceCount
                )

                if 0 <= settings_core.get_settings()['tracker index'] < len(trackers):#len(trackers) > 0:
                    index = trackers[settings_core.get_settings()['tracker index']]['index']
                    pose = poses[index]

                    if pose.bDeviceIsConnected and pose.bPoseIsValid:
                        m = pose.mDeviceToAbsoluteTracking

                        #position---
                        tracker_dict['x'] = m[0][3]
                        tracker_dict['y'] = m[1][3]
                        tracker_dict['z'] = m[2][3]

                        #rotation---
                        rotation_matrix = np.array([
                            [m[0][0], m[0][1], m[0][2]],
                            [m[1][0], m[1][1], m[1][2]],
                            [m[2][0], m[2][1], m[2][2]]
                        ])
                        
                        device_rotation = R.from_matrix(rotation_matrix)

                        offset_angles_rad = [
                            settings_core.get_settings()['offset roll'],
                            settings_core.get_settings()['offset yaw'],
                            settings_core.get_settings()['offset pitch']
                        ]
                        
                        offset_rotation = R.from_euler('ZYX', offset_angles_rad, degrees=False)

                        final_rotation = device_rotation * offset_rotation

                        quat_final = final_rotation.as_quat()

                        tracker_dict['yaw'] = quat_final[0]
                        tracker_dict['pitch'] = quat_final[1]
                        tracker_dict['roll'] = quat_final[2]
                        tracker_dict['w'] = quat_final[3]

                    time.sleep(0)
            except:
                time.sleep(1)
                start_vr_utility()

    except:
        time.sleep(1)
        start_vr_utility()

def end_vr_utility():
    vr.shutdown()

# def get_trackers(vr_system):
#     arr = []
#     for i in range(vr.k_unMaxTrackedDeviceCount):
#         device_class = vr_system.getTrackedDeviceClass(i)
#         if device_class in (vr.TrackedDeviceClass_Controller, vr.TrackedDeviceClass_GenericTracker):
#             #vr.TrackedDeviceClass_Controller == 2
#             #vr.TrackedDeviceClass_GenericTracker == 3
#             arr.append({"index" : i, "type" : device_class})      
#     return arr

def get_trackers(vr_system):
    #vr.TrackedDeviceClass_Controller == 2
    #vr.TrackedDeviceClass_GenericTracker == 3
    arr = []
    
    PROP_CONTROLLER_TYPE = vr.Prop_ControllerType_String 
    PROP_RENDER_MODEL = vr.Prop_RenderModelName_String
    
    for i in range(vr.k_unMaxTrackedDeviceCount):
        device_class = vr_system.getTrackedDeviceClass(i)
        
        if device_class in (vr.TrackedDeviceClass_Controller, vr.TrackedDeviceClass_GenericTracker):
            
            controller_model = "unknown"
            render_model_name = "unknown"
            role_hint = "unknown"

            try:
                controller_model = vr_system.getStringTrackedDeviceProperty(i, PROP_CONTROLLER_TYPE)
                
                render_model_name = vr_system.getStringTrackedDeviceProperty(i, PROP_RENDER_MODEL)
                
                if 'right' in render_model_name.lower():
                    role_hint = "right"
                elif 'left' in render_model_name.lower():
                    role_hint = "left"
                else:
                    role_enum = vr_system.getControllerRoleForTrackedDeviceIndex(i)
                    if role_enum == vr.TrackedControllerRole_LeftHand:
                        role_hint = "left"
                    elif role_enum == vr.TrackedControllerRole_RightHand:
                        role_hint = "right"
                    elif role_enum == vr.TrackedControllerRole_Treadmill:
                        role_hint = "treadmill"

            except Exception as e:
                pass

            arr.append({
                "index" : i, 
                "class" : device_class,
                "model" : controller_model,
                "render" : render_model_name,
                "role" : role_hint
            })
            
    return arr

if __name__ == '__main__':
    start_t_udp_send()
    start_t_update_vrlabel()


# def update_trackers_Hbox(trackers):
#     print(trackers)




















































layout_main.addWidget(trackers_widget)

# button = create_button({"text" : "is steamvr running?",
#                         "enabled" : True,
#                         "func" : lambda: button.findChild(QPushButton).setText(str(is_prosses_running("vrserver.exe")))})
# layout_main.addWidget(button)

layout_main.addWidget(create_label({
    "text" : "---------Network(sending to headset)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
network = create_group_horizontal([
    {
        "type" : "lineedit", 
        "text" : "Ip address", 
        "default" : settings_core.get_settings()['ip sending'], 
        "func" : lambda: settings_core.update_setting("ip sending", network.findChild(QLineEdit).text())
    },
    {
        "type" : "spinbox", 
        "text" :"Port", 
        "min":0, 
        "max":65535, 
        "default" : settings_core.get_settings()['port sending'], 
        "steps" : 1, 
        "func" : lambda: settings_core.update_setting("port sending", network.findChild(QSpinBox).value())
    }
])
layout_main.addWidget(network)


layout_main.addWidget(create_label({
    "text" : "---------Misc---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
misc = create_group_doublespinbox([
    {
        "text" : "IPD", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['ipd'], 
        "steps" : 0.01, 
        "func" : lambda: settings_core.update_setting("ipd", misc.findChildren(QDoubleSpinBox)[0].value()) 
    },
    {
        "text" : "Distance from tracker to eyes", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['head to eye dist'], 
        "steps" : 0.01, 
        "func" : lambda: settings_core.update_setting("head to eye dist", misc.findChildren(QDoubleSpinBox)[1].value()) 
    }
])
layout_main.addWidget(misc)

layout_main.addWidget(create_label({
    "text" : "---------Offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
position_offsets = create_group_doublespinbox([
    {
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset x", position_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset y", position_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset z", position_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

rotation_offsets = create_group_doublespinbox([
    {
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset yaw", rotation_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset pitch", rotation_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['offset roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("offset roll", rotation_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

layout_main.addWidget(position_offsets)
layout_main.addWidget(rotation_offsets)
#main/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#driver/////////////////////////////////////////////////////////////////////////////////////////////////////////////

def change_FOV_on_check(group):
    settings = settings_core.get_settings()
    
    if group != None:
        check = group.findChild(QCheckBox)
        
        settings_core.update_setting("stereoscopic", check.isChecked())

        settings['stereoscopic'] = check.isChecked()

    spinboxes = fov_group.findChildren(QDoubleSpinBox)

    if settings['stereoscopic']:
        fov_label.findChild(QLabel).setText("---------FOV(using Stereo)---------")
        
        spinboxes[0].setValue(settings['outer stereo'])
        spinboxes[1].setValue(settings['inner stereo'])
        spinboxes[2].setValue(settings['top stereo'])
        spinboxes[3].setValue(settings['bottom stereo'])

    else:
        fov_label.findChild(QLabel).setText("---------FOV(using Mono)---------")

        spinboxes[0].setValue(settings['outer mono'])
        spinboxes[1].setValue(settings['inner mono'])
        spinboxes[2].setValue(settings['top mono'])
        spinboxes[3].setValue(settings['bottom mono'])


def update_FOV():
    settings = settings_core.get_settings()
    
    spinboxes = fov_group.findChildren(QDoubleSpinBox)

    if settings['stereoscopic']:
        fov_label.findChild(QLabel).setText("---------FOV(using Stereo)---------")
        
        settings_core.update_setting('outer stereo', spinboxes[0].value())
        settings_core.update_setting('inner stereo', spinboxes[1].value())
        settings_core.update_setting('top stereo', spinboxes[2].value())
        settings_core.update_setting('bottom stereo', spinboxes[3].value())

    else:
        fov_label.findChild(QLabel).setText("---------FOV(using Mono)---------")

        settings_core.update_setting('outer mono', spinboxes[0].value())
        settings_core.update_setting('inner mono', spinboxes[1].value())
        settings_core.update_setting('top mono', spinboxes[2].value())
        settings_core.update_setting('bottom mono', spinboxes[3].value())
        
def set_activateMultipleDrivers_true():
    file_path = settings_core.get_settings()['vrsettings path'] + "/steamvr.vrsettings"
    #C:\Program Files (x86)\Steam\config\steamvr.vrsettings
    #"activateMultipleDrivers" : true,
    try:
        if not os.path.exists(file_path):
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        if "steamvr" not in data:
            data["steamvr"] = {}
        
        if data["steamvr"].get("activateMultipleDrivers") is True:
            return

        data["steamvr"]["activateMultipleDrivers"] = True

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(e)

set_activateMultipleDrivers_true()

def install_driver():
    #copy driver to steamvr/drivers
    source_folder = 'driver to copy'
    destination_folder = settings_core.get_settings()['drivers path']
    
    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

        # install_buttons.findChildren(QPushButton)[0].setText("installed successfully")
        # time.sleep(3)
        # install_buttons.findChildren(QPushButton)[0].setText("install")

    except Exception as e:
        print(e)

    update_install_label()

def remove_driver():
    folder_path = settings_core.get_settings()['drivers path'] + '/glassvrdriver'

    if not os.path.exists(folder_path):
            return

    try:
        shutil.rmtree(folder_path)
        
        # install_buttons.findChildren(QPushButton)[1].setText("uninstalled successfully")
        # time.sleep(3)
        # install_buttons.findChildren(QPushButton)[1].setText("uninstall")

    except OSError as e:
        print(e)

    update_install_label()

tab_driver = QWidget()
layout_driver = QVBoxLayout(tab_driver)

layout_driver.addWidget(create_label({
    "text" : "---------Driver(everything in this tab requires restarting steamvr to apply)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

def folder_exist(path: str):
    return os.path.isdir(path)

install_label = create_label({
    "text" : "driver is not installed, click to install to install!", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(install_label)

install_buttons = create_group_horizontal([
    {
        "type" : "button", 
        "text" : "install", 
        "enabled" : True,
        "func"  : lambda: install_driver()
    },
    {
        "type" : "button", 
        "text" : "uninstall", 
        "enabled" : True,
        "func"  : lambda: remove_driver()
    }
])
layout_driver.addWidget(install_buttons)

def update_install_label():
    leb =  install_label.findChild(QLabel)

    if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
        leb.setText("driver is installed!")
        install_buttons.findChildren(QPushButton)[0].setText("reinstall")
        install_buttons.findChildren(QPushButton)[1].setEnabled(True)
    else:
        leb.setText("driver is not installed, click to install to install!")
        install_buttons.findChildren(QPushButton)[0].setText("install")
        install_buttons.findChildren(QPushButton)[1].setEnabled(False)

update_install_label()

layout_driver.addWidget(create_label({
    "text" : "---------Network(headset receiving from)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
network2 = create_group_horizontal([
    {
        "type" : "lineedit", 
        "text" : "Ip address", 
        "default" : settings_core.get_settings()['ip receiving'],
        "func"  : lambda: settings_core.update_setting("ip sending", network2.findChild(QLineEdit).text())
    },
    {
        "type" : "spinbox", 
        "text" :"Port", 
        "min":0, 
        "max":65535, 
        "default" : settings_core.get_settings()['port receiving'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("port sending", network2.findChild(QSpinBox).value())
    }
])
layout_driver.addWidget(network2)

layout_driver.addWidget(create_label({
    "text" : "---------Resolution---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

res = create_group_horizontal([
    {
        "type" : "spinbox", 
        "text" :"X", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['resolution x'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("resolution x", res.findChildren(QSpinBox)[0].value())
    },
    {
        "type" : "spinbox", 
        "text" :"Y", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['resolution y'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("resolution y", res.findChildren(QSpinBox)[1].value())
    },
    {
        "type" : "spinbox", 
        "text" :"Refresh Rate", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['refresh rate'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("refresh rate", res.findChildren(QSpinBox)[2].value())
    }
])
layout_driver.addWidget(res)

layout_driver.addWidget(create_label({
    "text" : "---------Misc---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
misc_group = create_group_checkbox([
    {
        "text" : "Stereoscopic(SBS)", 
        "default" : settings_core.get_settings()['stereoscopic'], 
        "func" : lambda: change_FOV_on_check(misc_group)
    },
    {
        "text" : "Fullscreen", 
        "default": settings_core.get_settings()['fullscreen'],
        "func"  : lambda: settings_core.update_setting("fullscreen", misc_group.findChildren(QCheckBox)[1].isChecked())
    }
])
layout_driver.addWidget(misc_group)

fov_label = create_label({
    "text" : "---------FOV(using Mono)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(fov_label)

fov_group = create_group_doublespinbox([
    {
        "text" : "Outer", 
        "min":-999999999, 
        "max":999999999, 
        "default": settings_core.get_settings()['outer stereo'] \
           if settings_core.get_settings()["stereoscopic"] \
           else settings_core.get_settings()['outer mono'],
        "steps" : 0.01,
        "func"  : lambda: update_FOV()
    },
    {
        "text" : "Inner", 
        "min":-999999999, 
        "max":999999999, 
        "default": settings_core.get_settings()['inner stereo'] \
           if settings_core.get_settings()["stereoscopic"] \
           else settings_core.get_settings()['inner mono'],
        "steps" : 0.01,
        "func"  : lambda: update_FOV()
    },
    {
        "text" : "Top", 
        "min":-999999999, 
        "max":999999999, 
        "default": settings_core.get_settings()['top stereo'] \
           if settings_core.get_settings()["stereoscopic"] \
           else settings_core.get_settings()['top mono'],
        "steps" : 0.01,
        "func"  : lambda: update_FOV()
    },
    {
        "text" : "Bottom", 
        "min":-999999999, 
        "max":999999999, 
        "default": settings_core.get_settings()['bottom stereo'] \
           if settings_core.get_settings()["stereoscopic"] \
           else settings_core.get_settings()['bottom mono'],
        "steps" : 0.01,
        "func"  : lambda: update_FOV()
    }
])
layout_driver.addWidget(fov_group)

change_FOV_on_check(misc_group)

#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_credits = QWidget()
layout_credits = QVBoxLayout(tab_credits)

def create_credits():
    create_group = QWidget()
    layout_credits1 = QVBoxLayout(create_group)

    label = QLabel("DaniXmir")
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)

    image_label = QLabel()
    image = QPixmap("D:/UltimateFolder0/Gallery-Y/projects/GlassVr/code-glassvrserver/fix.png")
    scaled_pixmap = image.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    image_label.setPixmap(scaled_pixmap)
    image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(image_label)

    link = '<a href=https://github.com/DaniXmir/GlassVr> https://github.com/DaniXmir/GlassVr </a>'
    label = QLabel("project github:" + link)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    #label.setStyleSheet("text-decoration: underline; color: blue;")

    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)

    return create_group


layout_credits.addWidget(create_credits())
#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Add tabs to the window
window.addTab(tab_main, "Main")
window.addTab(tab_driver, "Driver")
window.addTab(tab_credits, "Credits")

window.show()
app.exec()