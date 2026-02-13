#pyinstaller --noconfirm --windowed --collect-binaries "sdl2dll" --collect-all "sdl2" --collect-binaries "openvr" --collect-all "mediapipe" --collect-all "cv2" --hidden-import "sdl2dll" main.py
#or
#pyinstaller --noconfirm --windowed --uac-admin --collect-binaries "sdl2dll" --collect-all "sdl2" --collect-binaries "openvr" --collect-all "mediapipe" --collect-all "cv2" --hidden-import "sdl2dll" main.py

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox, QComboBox

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

import shutil
import psutil
import os
import json
import struct
import time
import threading
import math
import openvr as vr
import numpy as np
from scipy.spatial.transform import Rotation as R
import sys

import win32file
from typing import List, Dict, Any, Tuple
import cv2
import mediapipe as mp
import cv2.aruco as aruco

import time
from sdl2 import *
from sdl2.ext import Resources
import keyboard

import ctypes
import webbrowser
import platform
import requests

import win32pipe
import pywintypes

import settings_core

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('sdl2dll')

app = QApplication([])#sys.argv)

window = QWidget()
window_layout = QHBoxLayout(window)

tabs = QTabWidget()
#window.setWindowTitle("PuffinVR")
window.setWindowTitle("GlassVR")
#window.resize(1150, 1100)
window.resize(900, 900)

#ui core/////////////////////////////////////////////////////////////////////////////////////////////////////////////
# layout_main.addWidget(create_group_label([{"text" : "a", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "b", "alignment" : Qt.AlignmentFlag.AlignCenter},{"text" : "c", "alignment" : Qt.AlignmentFlag.AlignCenter}]))
# layout_main.addWidget(create_group_button([{"text" : "a", "enabled" : True},{"text" : "b", "enabled" : True},{"text" : "c", "enabled" : False}]))
# layout_main.addWidget(create_group_checkbox([{"text" : "a", "checked" : True},{"text" : "a", "checked" : False}]))
# layout_main.addWidget(create_group_spinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))
# layout_main.addWidget(create_group_doublespinbox([{"text" : "x","min":-3,"max":3,"default":1},{"text" : "y","min":-3,"max":3,"default":2},{"text" : "z","min":-3,"max":3,"default":3}]))

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())

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
    spinbox.setSingleStep(dict.get('steps',1))
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
    spinbox.setSingleStep(dict.get('steps',1))
    spinbox.setDecimals(3)
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
                case "combobox":
                    group_layout.addWidget(create_combobox(dict))
        return group_widget
    
def create_image(dict = {}):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "assets", "fix.png")

    image_label = QLabel()
    image = QPixmap(image_path)#"D:/UltimateFolder0/Gallery-Y/projects/GlassVr/code-glassvrserver/fix.png")
    scaled_pixmap = image.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    image_label.setPixmap(scaled_pixmap)
    image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    return image_label

def create_combobox(dict):
    group_widget = QWidget()
    group_layout = QHBoxLayout(group_widget)

    label = QLabel(dict.get('text', ""))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    group_layout.addWidget(label)

    combobox = QComboBox()
    
    if 'items' in dict:
        combobox.addItems(dict['items'])
    
    if 'default' in dict:\
        combobox.setCurrentText(dict['default'])

    if 'func' in dict:
        combobox.currentIndexChanged.connect(lambda: dict['func']())
        
    group_layout.addWidget(combobox)

    return group_widget

def create_group_combobox(arr = [], direction = "h"):
    if arr:
        group_widget = QWidget()
        group_layout = 0

        match direction:
            case "h":
                group_layout = QHBoxLayout(group_widget)
            case "v":
                group_layout = QVBoxLayout(group_widget)

        for dict in arr:
            group_layout.addWidget(create_combobox(dict))

        return group_widget
#ui core/////////////////////////////////////////////////////////////////////////////////////////////////////////////

# main/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_main = QWidget()
layout_main = QVBoxLayout(tab_main)
layout_main.setSpacing(0)

check_box_hmd = create_checkbox(
    {
        "text" : "enable hmd", 
        "default" : settings_core.get_settings()['enable hmd'], 
        "func" : lambda: settings_core.update_setting("enable hmd",check_box_hmd.findChild(QCheckBox).isChecked())
    })
layout_main.addWidget(check_box_hmd)

#hmd modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def hmdpos_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    #settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        case "keyboard":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

def create_hmdpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "hmd position mode",
            "default": settings.get(f'hmdpos mode', "redirect"),
            "items": ["redirect"],# "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: hmdpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    hmdpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_main.addWidget(create_hmdpos_widget())
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def hmdrot_specific_widget(layout, combo):
    settings_core.update_setting(f'hmdrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    #settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['hmdrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmdrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "gyro":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"controller index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings().get(f'hmd gyro index',0), 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("hmd gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

def create_hmdrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "hmd rotation mode",
            "default": settings.get(f'hmdrot mode', "redirect"),
            "items": ["redirect","gyro"],# "mouse"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: hmdrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    hmdrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_main.addWidget(create_hmdrot_widget())
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#hmd modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

trackers_arr = [] #[{"pos x" : m[0][3],
                    #"pos y" : m[1][3],
                    #"pos z" : m[2][3], 
                    #"rotation matrix" :[
                    #[m[0][0], m[0][1], m[0][2]],
                    #[m[1][0], m[1][1], m[1][2]],
                    # [m[2][0], m[2][1], m[2][2]]
                    # ]}]

def is_prosses_running(PROCESS_NAME):
    for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == PROCESS_NAME.lower():
                return True
    
    return False

def check_hardware_key_exists(hardware_name):
    settings = settings_core.get_settings()
    
    return hardware_name in settings.values()

def get_final_transform(device = "hmd", override = None):
    settings = settings_core.get_settings()

    try:
        tracker_pos_idx = settings.get(f'{device}pos index', 0)

        if override == None:
            tracker_pos = trackers_arr[tracker_pos_idx]
        else:
            tracker_pos = override

        tracker_rot_idx = settings.get(f'{device}rot index', 0)

        if override == None:
            tracker_rot = trackers_arr[tracker_rot_idx]
        else:
            tracker_rot = override

        offset_local = np.array([
            settings.get(f'{device} offset local x', 0.0),
            settings.get(f'{device} offset local y', 0.0),
            settings.get(f'{device} offset local z', 0.0)
        ])
        
        offset_world = np.array([
            settings.get(f'{device} offset world x', 0.0),
            settings.get(f'{device} offset world y', 0.0),
            settings.get(f'{device} offset world z', 0.0)
        ])
        
        device_rotation = R.from_matrix(tracker_rot['rotation matrix'])
        
        rotated_local_offset = device_rotation.apply(offset_local)
        
        pos_x = tracker_pos['pos x'] + rotated_local_offset[0] + offset_world[0]
        pos_y = tracker_pos['pos y'] + rotated_local_offset[1] + offset_world[1]
        pos_z = tracker_pos['pos z'] + rotated_local_offset[2] + offset_world[2]
        
        offset_local_angles_rad = [
            settings.get(f'{device} offset local roll', 0.0),
            settings.get(f'{device} offset local yaw', 0.0),
            settings.get(f'{device} offset local pitch', 0.0)
        ]
        
        offset_world_angles_rad = [
            settings.get(f'{device} offset world roll', 0.0),
            settings.get(f'{device} offset world yaw', 0.0),
            settings.get(f'{device} offset world pitch', 0.0)
        ]
        
        offset_local_rotation = R.from_euler('ZYX', offset_local_angles_rad, degrees=False)
        offset_world_rotation = R.from_euler('ZYX', offset_world_angles_rad, degrees=False)
        
        final_rotation = offset_world_rotation * device_rotation * offset_local_rotation
        quat_final = final_rotation.as_quat()
        
        return({
            "pos x" : pos_x, "pos y" : pos_y, "pos z" : pos_z,
            "rot x" : quat_final[0], "rot y" : quat_final[1], "rot z" : quat_final[2], "rot w" : quat_final[3]
        })
    except:
        try:
            offset_local_angles_rad = [
                settings.get(f'{device} offset local roll', 0.0),
                settings.get(f'{device} offset local yaw', 0.0),
                settings.get(f'{device} offset local pitch', 0.0)
            ]
            
            offset_world_angles_rad = [
                settings.get(f'{device} offset world roll', 0.0),
                settings.get(f'{device} offset world yaw', 0.0),
                settings.get(f'{device} offset world pitch', 0.0)
            ]
            
            offset_local_rotation = R.from_euler('ZYX', offset_local_angles_rad, degrees=False)
            offset_world_rotation = R.from_euler('ZYX', offset_world_angles_rad, degrees=False)
            combined_rotation = offset_world_rotation * offset_local_rotation
            quat = combined_rotation.as_quat()
            
            return({
                "pos x" : settings.get(f'{device} offset local x', 0.0) + settings.get(f'{device} offset world x', 0.0),
                "pos y" : settings.get(f'{device} offset local y', 0.0) + settings.get(f'{device} offset world y', 0.0),
                "pos z" : settings.get(f'{device} offset local z', 0.0) + settings.get(f'{device} offset world z', 0.0),
                "rot x" : quat[0], "rot y" : quat[1], "rot z" : quat[2], "rot w" : quat[3]
            })
        except:
            return({
                "pos x" : 0.0, "pos y" : 0.0, "pos z" : 0.0,
                "rot x" : 0.0, "rot y" : 0.0, "rot z" : 0.0, "rot w" : 1.0
            })

#this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def get_new_transform(device="hmd", px=0.0, py=0.0, pz=0.0, rx=0.0, ry=0.0, rz=0.0, rw=0.0):
    settings = settings_core.get_settings()
    
    try:
        device_rotation = R.from_quat([rx, ry, rz, rw])
        
        offset_local = np.array([
            settings.get(f'{device} offset local x', 0.0),
            settings.get(f'{device} offset local y', 0.0),
            settings.get(f'{device} offset local z', 0.0)
        ])
        
        offset_world = np.array([
            settings.get(f'{device} offset world x', 0.0),
            settings.get(f'{device} offset world y', 0.0),
            settings.get(f'{device} offset world z', 0.0)
        ])
        
        rotated_local_offset = device_rotation.apply(offset_local)
        
        pos_x = px + rotated_local_offset[0] + offset_world[0]
        pos_y = py + rotated_local_offset[1] + offset_world[1]
        pos_z = pz + rotated_local_offset[2] + offset_world[2]
        
        off_loc_angles = [
            settings.get(f'{device} offset local roll', 0.0),
            settings.get(f'{device} offset local yaw', 0.0),
            settings.get(f'{device} offset local pitch', 0.0)
        ]
        
        off_world_angles = [
            settings.get(f'{device} offset world roll', 0.0),
            settings.get(f'{device} offset world yaw', 0.0),
            settings.get(f'{device} offset world pitch', 0.0)
        ]
        
        offset_local_rotation = R.from_euler('ZYX', off_loc_angles, degrees=False)
        offset_world_rotation = R.from_euler('ZYX', off_world_angles, degrees=False)
        
        final_rotation = offset_world_rotation * device_rotation * offset_local_rotation
        quat_final = final_rotation.as_quat()
        
        return {
            "pos x" : pos_x, "pos y" : pos_y, "pos z" : pos_z,
            "rot x" : quat_final[0], "rot y" : quat_final[1], 
            "rot z" : quat_final[2], "rot w" : quat_final[3]
        }

    except Exception as e:
        return {
            "pos x" : px, "pos y" : py, "pos z" : pz,
            "rot x" : rx, "rot y" : ry, "rot z" : rz, "rot w" : rw
        }
    
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


HMD_PACK_FORMAT = '<9d'  # pos(3) + rot(4) + ipd + head_to_eye_dist
CONTROLLER_PACK_FORMAT = '<12d6?'  # pos(3) + rot(4) + joy(2) + touch(2) + trigger + 5 buttons
TRACKER_PACK_FORMAT = '<7d'  # id + pos(3) + rot(4)

HMD_PACKER = struct.Struct(HMD_PACK_FORMAT)
CONTROLLER_PACKER = struct.Struct(CONTROLLER_PACK_FORMAT)
TRACKER_PACKER = struct.Struct(TRACKER_PACK_FORMAT)

PIPE_HMD = r'\\.\pipe\GlassVR_HMD'
PIPE_LEFT = r'\\.\pipe\GlassVR_Left'
PIPE_RIGHT = r'\\.\pipe\GlassVR_Right'
PIPE_TRACKER_PREFIX = r'\\.\pipe\GlassVR_Tracker_'

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )

def send_hmd_data():
    while True:
        handle = None
        try:
            handle = create_pipe(PIPE_HMD)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()

                final_transform = get_final_transform("hmd")
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings['hmdpos mode']:
                        case "redirect":
                            pass

                        case "keyboard":
                            pass

                        case _:
                            final_transform = get_final_transform("hmd")

                            pos_x = final_transform['pos x']
                            pos_y = final_transform['pos y']
                            pos_z = final_transform['pos z']
                except:
                    pass
                try:
                    match settings['hmdrot mode']:
                        case "redirect":
                            pass

                        case "mouse":
                            pass

                        case "gyro":
                            if settings[f'hmd gyro index'] == 0:
                                transform = get_new_transform("hmd",pos_x,pos_y,pos_z,
                                                            controller_1_dict['gyro_quat']['x'],
                                                            controller_1_dict['gyro_quat']['y'],
                                                            controller_1_dict['gyro_quat']['z'],
                                                            controller_1_dict['gyro_quat']['w'])
                                rot_x = transform['rot x']
                                rot_y = transform['rot y']
                                rot_z = transform['rot z']
                                rot_w = transform['rot w']
                            else:
                                transform = get_new_transform("hmd",pos_x,pos_y,pos_z,
                                                            controller_2_dict['gyro_quat']['x'],
                                                            controller_2_dict['gyro_quat']['y'],
                                                            controller_2_dict['gyro_quat']['z'],
                                                            controller_2_dict['gyro_quat']['w'])
                                
                        case _:
                            final_transform = get_final_transform("hmd")

                            rot_x = final_transform['rot x']
                            rot_y = final_transform['rot y']
                            rot_z = final_transform['rot z']
                            rot_w = final_transform['rot w']
                except:
                    pass
                hmd_ipd = settings.get('ipd', 0.0)
                hmd_head_to_eye_dist = settings.get('head to eye dist', 0.0)

                buffer = HMD_PACKER.pack(
                    pos_x, pos_y, pos_z,
                    rot_w, rot_x, rot_y, rot_z,
                    hmd_ipd, hmd_head_to_eye_dist
                )
                
                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        #print(e)
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            #print(e)
            pass

        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

#predict next pose test/////////////////////////////////////////////////////
# def send_hmd_data():
#     last_pose = None
#     last_time = None
    
#     while True:
#         handle = None
#         try:
#             handle = create_pipe(PIPE_HMD)
#             win32pipe.ConnectNamedPipe(handle, None)
            
#             while True:
#                 settings = settings_core.get_settings()
#                 current_time = time.time()
                
#                 hmd_final_transform = get_final_transform("hmd")
                
#                 if last_pose and last_time:
#                     dt = current_time - last_time
#                     if dt > 0:
#                         vel_x = (hmd_final_transform['pos x'] - last_pose['pos x']) / dt
#                         vel_y = (hmd_final_transform['pos y'] - last_pose['pos y']) / dt
#                         vel_z = (hmd_final_transform['pos z'] - last_pose['pos z']) / dt
                        
#                         prediction_time = 0.008
#                         hmd_pos_x = hmd_final_transform['pos x'] + vel_x * prediction_time
#                         hmd_pos_y = hmd_final_transform['pos y'] + vel_y * prediction_time
#                         hmd_pos_z = hmd_final_transform['pos z'] + vel_z * prediction_time
#                     else:
#                         hmd_pos_x = hmd_final_transform['pos x']
#                         hmd_pos_y = hmd_final_transform['pos y']
#                         hmd_pos_z = hmd_final_transform['pos z']
#                 else:
#                     hmd_pos_x = hmd_final_transform['pos x']
#                     hmd_pos_y = hmd_final_transform['pos y']
#                     hmd_pos_z = hmd_final_transform['pos z']
                
#                 last_pose = hmd_final_transform.copy()
#                 last_time = current_time
                
#                 hmd_rot_x = hmd_final_transform['rot x']
#                 hmd_rot_y = hmd_final_transform['rot y']
#                 hmd_rot_z = hmd_final_transform['rot z']
#                 hmd_rot_w = hmd_final_transform['rot w']
#                 hmd_ipd = settings.get('ipd', 0.0)
#                 hmd_head_to_eye_dist = settings.get('head to eye dist', 0.0)
                
#                 buffer = HMD_PACKER.pack(
#                     hmd_pos_x, hmd_pos_y, hmd_pos_z,
#                     hmd_rot_w, hmd_rot_x, hmd_rot_y, hmd_rot_z,
#                     hmd_ipd, hmd_head_to_eye_dist
#                 )
                
#                 try:
#                     win32file.WriteFile(handle, buffer)
#                 except pywintypes.error as e:
#                     if e.winerror in [109, 232]:
#                         print("HMD pipe disconnected. Reconnecting...")
#                         break
#                     raise
                
#                 time.sleep(0)
                
#         except Exception as e:
#             print(f"HMD pipe error: {e}")
#         finally:
#             if handle:
#                 try:
#                     win32pipe.DisconnectNamedPipe(handle)
#                     win32file.CloseHandle(handle)
#                 except: pass
#             time.sleep(1)
#predict next pose test/////////////////////////////////////////////////////

def get_hand_world_transform(device):
    try:
        hand_prefix = 'r' if device == "cr" else 'l'
        
        settings = settings_core.get_settings()

        mod_x = settings.get('camera z', 0.05)#0.05
        mod_y = settings.get('camera z', 0.05)#0.05
        mod_z = settings.get('camera z', 0.05)

        outer_stereo = settings.get('outer stereo', 41.070)
        inner_stereo = settings.get('inner stereo', 41.070)
        top_stereo = settings.get('top stereo', 26.120)
        bottom_stereo = settings.get('bottom stereo', 26.120)
        
        fov_horizontal = outer_stereo + inner_stereo
        fov_vertical = top_stereo + bottom_stereo

        hmd_pos = (trackers_arr[0]['pos x'],trackers_arr[0]['pos y'],trackers_arr[0]['pos z'])

        rot = R.from_matrix(trackers_arr[0]['rotation matrix'])
        hmd_rot = R.from_quat(rot.as_quat())

        screen_x = 1.0 - hand_data[f'{hand_prefix} pos x']
        screen_y = 1.0 - hand_data[f'{hand_prefix} pos y']
        depth = hand_data[f'{hand_prefix} pos z']
        
        normalized_x = (screen_x - 0.5) * 2.0
        normalized_y = (screen_y - 0.5) * 2.0
        
        fov_h_rad = np.radians(fov_horizontal / 2)
        fov_v_rad = np.radians(fov_vertical / 2)
        
        camera_relative_pos = np.array([
            depth * np.tan(fov_h_rad) * normalized_x,
            -depth * np.tan(fov_v_rad) * normalized_y,
            -depth
        ])
        
        world_relative_pos = hmd_rot.apply(camera_relative_pos)
        
        world_relative_pos_fixed = np.array([
            -world_relative_pos[0],
            -world_relative_pos[1],
            -world_relative_pos[2]
        ])

        world_pos = hmd_pos + np.array([
            world_relative_pos_fixed[0] * mod_x,
            world_relative_pos_fixed[1] * mod_y,
            world_relative_pos_fixed[2] * mod_z
        ])
        
        #////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        hand_rot_local_full = R.from_quat([
            hand_data[f'{hand_prefix} rot x'],
            hand_data[f'{hand_prefix} rot y'],
            hand_data[f'{hand_prefix} rot z'],
            hand_data[f'{hand_prefix} rot w']
        ])

        angles = hand_rot_local_full.as_euler('ZYX', degrees=False)

        if device == "cl":
            isolated_angles = [-angles[1], angles[2], angles[0]] 
        else:
            isolated_angles = [-angles[1], -angles[2], -angles[0]] 

        hand_rot_local = R.from_euler('ZYX', isolated_angles, degrees=False)

        offset_yaw = settings.get(f'{device} offset world yaw', 0.0)
        offset_pitch = settings.get(f'{device} offset world pitch', 0.0)
        offset_roll = settings.get(f'{device} offset world roll', 0.0)

        offset_rotation = R.from_euler('ZYX', [offset_yaw, offset_pitch, offset_roll], degrees=False)
        hand_rot_with_offset = hand_rot_local * offset_rotation

        world_rot = hmd_rot * hand_rot_with_offset
        final_quat = world_rot.as_quat()
        #////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        return {
            "pos x": world_pos[0],
            "pos y": world_pos[1],
            "pos z": world_pos[2],
            "rot x": final_quat[0],
            "rot y": final_quat[1],
            "rot z": final_quat[2],
            "rot w": final_quat[3]
        }
        
    except Exception as e:
        #print(e)
        return {
            "pos x": 0.0,
            "pos y": 0.0,
            "pos z": 0.0,
            "rot x": 0.0,
            "rot y": 0.0,
            "rot z": 0.0,
            "rot w": 1.0
        }

#best offsets/////////////////////////////////////////////////////////////////////////////////////////////////////////
#right 2.560 -0.280 2.060
#left 3.860 0.190 1.990

def send_controller_data(is_right):
    pipe_name = PIPE_RIGHT if is_right else PIPE_LEFT
    device_name = "cr" if is_right else "cl"
    side = "right" if is_right else "left"

    while True:
        handle = None
        try:
            handle = create_pipe(pipe_name)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()

                final_transform = get_final_transform(device_name)
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings[f'{device_name}pos mode']:
                        case "hand tracking":
                            if settings_core.get_settings()['opengloves'] != False:
                                final_c_transform = get_final_transform(device_name)
                                final_transform = get_hand_world_transform(device_name)

                                pos_x = final_transform['pos x']# + final_c_transform['pos x']
                                pos_y = final_transform['pos y']# + final_c_transform['pos y']
                                pos_z = final_transform['pos z']# + final_c_transform['pos z']
                            else:
                                final_transform = get_final_transform(device_name)

                                pos_x = final_transform['pos x']
                                pos_y = final_transform['pos y']
                                pos_z = final_transform['pos z']
                        case _:
                            final_transform = get_final_transform(device_name)

                            pos_x = final_transform['pos x']
                            pos_y = final_transform['pos y']
                            pos_z = final_transform['pos z']
                except:
                    pass
                try:
                    match settings[f'{device_name}rot mode']:
                        case "hand tracking":
                            if settings_core.get_settings()['opengloves'] != False:
                                final_c_transform = get_final_transform(device_name)
                                final_transform = get_hand_world_transform(device_name)

                                rot_x = final_transform['rot x']
                                rot_y = final_transform['rot y']
                                rot_z = final_transform['rot z']
                                rot_w = final_transform['rot w']

                            else:
                                final_transform = get_final_transform(device_name)

                                rot_x = final_transform['rot x']
                                rot_y = final_transform['rot y']
                                rot_z = final_transform['rot z']
                                rot_w = final_transform['rot w']
                        case "gyro":
                            if settings[f'{device_name} gyro index'] == 0:
                                transform = get_new_transform(device_name,pos_x,pos_y,pos_z,
                                                            controller_1_dict['gyro_quat']['x'],
                                                            controller_1_dict['gyro_quat']['y'],
                                                            controller_1_dict['gyro_quat']['z'],
                                                            controller_1_dict['gyro_quat']['w'])
                                rot_x = transform['rot x']
                                rot_y = transform['rot y']
                                rot_z = transform['rot z']
                                rot_w = transform['rot w']

                                #print(controller_1_dict["gyro_quat"])
                                #print(transform)
                            else:
                                transform = get_new_transform(device_name,pos_x,pos_y,pos_z,
                                                            controller_2_dict['gyro_quat']['x'],
                                                            controller_2_dict['gyro_quat']['y'],
                                                            controller_2_dict['gyro_quat']['z'],
                                                            controller_2_dict['gyro_quat']['w'])
                                rot_x = transform['rot x']
                                rot_y = transform['rot y']
                                rot_z = transform['rot z']
                                rot_w = transform['rot w']
                        case _:
                            final_transform = get_final_transform(device_name)

                            rot_x = final_transform['rot x']
                            rot_y = final_transform['rot y']
                            rot_z = final_transform['rot z']
                            rot_w = final_transform['rot w']
                except:
                    pass

                trigger = get_mapped_action(f'{side} trigger')
                a = get_mapped_action(f'{side} a')
                b = get_mapped_action(f'{side} b')
                grip = get_mapped_action(f'{side} grip')
                menu = get_mapped_action(f'{side} menu')
                joy_btn = get_mapped_action(f'{side} joy button')
                touch_btn = get_mapped_action(f'{side} touch button')
                
                if check_hardware_key_exists(f'{side} touch modifier') and get_mapped_action(f'{side} touch modifier'):
                    joy_x, joy_y = 0.0, 0.0
                    touch_x = get_mapped_action(f'{side} joy x')
                    touch_y = -get_mapped_action(f'{side} joy y')
                    touch_btn = get_mapped_action(f'{side} joy button')
                else:
                    joy_x = get_mapped_action(f'{side} joy x')
                    joy_y = -get_mapped_action(f'{side} joy y')
                    touch_x = get_mapped_action(f'{side} touch x')
                    touch_y = -get_mapped_action(f'{side} touch y')
                
                buffer = CONTROLLER_PACKER.pack(
                    float(pos_x), float(pos_y), float(pos_z),      # 3
                    float(rot_w), float(rot_x), float(rot_y), float(rot_z), # 4
                    float(joy_x), float(joy_y),                    # 2
                    float(touch_x), float(touch_y),                # 2
                    float(trigger),                                # 1 (Total 12)
                    bool(a), bool(b), bool(menu), 
                    bool(joy_btn), bool(touch_btn), bool(grip)     # 6 bools
                )
                
                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        #print(e)
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            #print(e)
            pass
        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

def send_tracker_data(tracker_id):
    pipe_name = f"{PIPE_TRACKER_PREFIX}{tracker_id}"
    
    while True:
        handle = None
        try:
            handle = create_pipe(pipe_name)
            win32pipe.ConnectNamedPipe(handle, None)
            
            while True:
                settings = settings_core.get_settings()
                override = None

                final_transform = get_final_transform(f'{tracker_id}tracker')
                pos_x = final_transform['pos x']
                pos_y = final_transform['pos y']
                pos_z = final_transform['pos z']
                rot_x = final_transform['rot x']
                rot_y = final_transform['rot y']
                rot_z = final_transform['rot z']
                rot_w = final_transform['rot w']
                try:
                    match settings.get(f"{tracker_id}trackerpos mode", "redirect"):
                        case "redirect":
                            pass

                        case "hip emulation":
                            pass

                        case _:
                            final_transform = get_final_transform(f'{tracker_id}tracker')

                            pos_x = final_transform['pos x']
                            pos_x = final_transform['pos y']
                            pos_x = final_transform['pos z']
                except:
                    pass
                try:
                    match settings.get(f"{tracker_id}trackerrot mode", "redirect"):
                        case "redirect":
                            pass

                        case "gyro":
                            if settings.get(f'{tracker_id}tracker gyro index',0) == 0:
                                transform = get_new_transform(f'{tracker_id}tracker',pos_x,pos_y,pos_z,
                                                            controller_1_dict['gyro_quat']['x'],
                                                            controller_1_dict['gyro_quat']['y'],
                                                            controller_1_dict['gyro_quat']['z'],
                                                            controller_1_dict['gyro_quat']['w'])
                                rot_x = transform['rot x']
                                rot_y = transform['rot y']
                                rot_z = transform['rot z']
                                rot_w = transform['rot w']
                            else:
                                transform = get_new_transform(f'{tracker_id}tracker',pos_x,pos_y,pos_z,
                                                            controller_2_dict['gyro_quat']['x'],
                                                            controller_2_dict['gyro_quat']['y'],
                                                            controller_2_dict['gyro_quat']['z'],
                                                            controller_2_dict['gyro_quat']['w'])
                        case _:
                            final_transform = get_final_transform(f'{tracker_id}tracker')

                            rot_x = final_transform['rot x']
                            rot_y = final_transform['rot y']
                            rot_z = final_transform['rot z']
                            rot_w = final_transform['rot w']
                except:
                    pass
                buffer = TRACKER_PACKER.pack(
                    float(pos_x), float(pos_y), float(pos_z),
                    float(rot_w), float(rot_x), float(rot_y), float(rot_z)
                )
                
                try:
                    win32file.WriteFile(handle, buffer)
                except pywintypes.error as e:
                    if e.winerror in [109, 232]:
                        #print(e)
                        break
                    raise
                
                time.sleep(0.001)
                
        except Exception as e:
            #print(e)
            pass
        finally:
            if handle:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                    win32file.CloseHandle(handle)
                except: pass
            time.sleep(1)

def start_send_data():
    threads = []
    
    t_hmd = threading.Thread(target=send_hmd_data, daemon=True)
    t_hmd.start()
    threads.append(t_hmd)
    
    t_left = threading.Thread(target=lambda: send_controller_data(False), daemon=True)
    t_left.start()
    threads.append(t_left)
    
    t_right = threading.Thread(target=lambda: send_controller_data(True), daemon=True)
    t_right.start()
    threads.append(t_right)
    
    settings = settings_core.get_settings()
    max_trackers = settings.get('trackers num', 0)
    for tracker_id in range(max_trackers):
        t_tracker = threading.Thread(target=lambda tid=tracker_id: send_tracker_data(tid), daemon=True)
        t_tracker.start()
        threads.append(t_tracker)
    
    return threads

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

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

def start_update_vrlabel():
    t = threading.Thread(target=update_vrlabel, daemon=True)
    t.start()
    return t

trackers_dict = {}

def start_vr_utility():
    global trackers_dict, trackers_arr

    try:
        vr.init(vr.VRApplication_Utility)
        vr_system = vr.VRSystem()
        
        PROP_SERIAL = vr.Prop_SerialNumber_String
        PROP_MODEL = vr.Prop_ControllerType_String
        PROP_RENDER = vr.Prop_RenderModelName_String

        while True:
            try:
                poses = vr_system.getDeviceToAbsoluteTrackingPose(2, 0.0, vr.k_unMaxTrackedDeviceCount)
                
                new_dict = {}
                new_arr = []

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
                            
                            pos_x, pos_y, pos_z = m[0][3], m[1][3], m[2][3]
                            
                            rotation_matrix = np.array([
                                [m[0][0], m[0][1], m[0][2]],
                                [m[1][0], m[1][1], m[1][2]],
                                [m[2][0], m[2][1], m[2][2]]
                            ])

                            device_data.update({
                                "pos x": pos_x,
                                "pos y": pos_y,
                                "pos z": pos_z,
                                "rotation matrix": rotation_matrix
                            })

                            new_arr.append({
                                "pos x": pos_x,
                                "pos y": pos_y,
                                "pos z": pos_z,
                                "rotation matrix": rotation_matrix
                            })

                        new_dict[serial] = device_data

                trackers_dict = new_dict
                trackers_arr = new_arr

                update_found_label()
                time.sleep(0.001)

            except Exception as e:
                #print(e)
                time.sleep(0.001)
                continue

    except Exception as e:
        #print(e)
        time.sleep(1)
        start_vr_utility()

def end_vr_utility():
    vr.shutdown()

def update_found_label():
    global trackers_dict
    display_text = ""
    count = 0
    for serial, data in trackers_dict.items():
        display_text += f'[{count}] '
        display_text += f"ROLE: {data['role']} | {data['model']}\n"
        display_text += f"Serial: {serial}\n"
        
        if data.get('connected'):# and data.get('pose_valid'):
            px, py, pz = data['pos x'], data['pos y'], data['pos z']
            display_text += f"Pos: X:{px:+.3f} Y:{py:+.3f} Z:{pz:+.3f}\n"
            
            if "rotation matrix" in data:
                m = data['rotation matrix']
                display_text += "Rot Matrix:\n"
                display_text += f"  [{m[0][0]:+.2f}, {m[0][1]:+.2f}, {m[0][2]:+.2f}]\n"
                display_text += f"  [{m[1][0]:+.2f}, {m[1][1]:+.2f}, {m[1][2]:+.2f}]\n"
                display_text += f"  [{m[2][0]:+.2f}, {m[2][1]:+.2f}, {m[2][2]:+.2f}]\n"
        else:
            display_text += "OFFLINE"# OR UNTRACKED\n"
        
        display_text += "-----------------------------------\n"

        count += 1

    try:
        label = trackers_label1.findChild(QLabel)
        if label:
            label.setText(display_text)
    except Exception as e:
        #print(e)
        pass




#controller handler/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER)
SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI_COMBINE_JOY_CONS, b"0")

SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4", b"1")
SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS5", b"1")

SDL_SetHint(b"SDL_JOYSTICK_HIDAPI_PS4_RUMBLE", b"1")

controller_arr = []
DEADZONE = 0.1

def get_default_state():
    return {
        "a": False, "b": False, "x": False, "y": False,
        "back": False, "guide": False, "start": False, "misc1": False,
        "leftshoulder": False, "rightshoulder": False,
        "leftstick": False, "rightstick": False,
        "dpup": False, "dpdown": False, "dpleft": False, "dpright": False,
        "paddle1": False, "paddle2": False, "paddle3": False, "paddle4": False,
        "touchpad": False,
        
        "leftx": 0.0, "lefty": 0.0, "rightx": 0.0, "righty": 0.0,
        "lefttrigger": 0.0, "righttrigger": 0.0,

        "gyro_quat": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "last_good_quat": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "last_ts": 0,
        
        "gyro_bias": {
            "wx": 0.0, "wy": 0.0, "wz": 0.0,
            "ax": 0.0, "ay": 0.0, "az": 0.0,
            "tx": 0.02, "ty": 0.02, "tz": 0.02,
            "samples": 0
        }
    }

controller_1_dict = get_default_state()
controller_2_dict = get_default_state()

def get_mapped_action(action_name="none", target="any"):
    settings = settings_core.get_settings()
    is_analog_req = any(word in action_name.lower() for word in ['trigger', 'joy x', 'joy y'])
    
    vals = []
    
    for map_key, mapped_action in settings.items():
        if mapped_action != action_name:
            continue

        if len(map_key) < 2: continue

        prefix = map_key[0]
        
        if not prefix.isdigit():
            continue
            
        p_num = int(prefix) + 1  
        raw_btn = map_key[1:]

        val = None
        target_dict = None
        
        if prefix == "0" and (target == "1" or target == "any"):
            target_dict = controller_1_dict
        elif prefix == "1" and (target == "2" or target == "any"):
            target_dict = controller_2_dict

        if target_dict and raw_btn in target_dict:
            val = target_dict[raw_btn]

            if "leftx" in raw_btn or "rightx" in raw_btn:
                if settings.get(f"joy{p_num} invert x", False):
                    val = -val
            elif "lefty" in raw_btn or "righty" in raw_btn:
                if settings.get(f"joy{p_num} invert y", False):
                    val = -val

        if val is not None:
            vals.append(val)

    if not vals:
        return 0.0 if is_analog_req else False

    if is_analog_req:
        float_vals = [float(v) for v in vals]
        return max(float_vals, key=abs)
    else:
        return any(bool(v) for v in vals)

controller_arr = []
controller_1_dict = {}
controller_2_dict = {}

CALIBRATION_SAMPLES = 200
DEFAULT_THRESHOLD = 0.02
DEADZONE = 0.1
ALPHA = 0.98

def normalize_quat(q):
    mag = math.sqrt(q["x"]**2 + q["y"]**2 + q["z"]**2 + q["w"]**2)
    if mag == 0: return {"x": 0, "y": 0, "z": 0, "w": 1}
    return {"x": q["x"]/mag, "y": q["y"]/mag, "z": q["z"]/mag, "w": q["w"]/mag}

def normalize_vec3(v):
    """Normalize a 3D vector"""
    mag = math.sqrt(v["x"]**2 + v["y"]**2 + v["z"]**2)
    if mag == 0: return {"x": 0, "y": 0, "z": 1}
    return {"x": v["x"]/mag, "y": v["y"]/mag, "z": v["z"]/mag}

def quat_from_two_vectors(v1, v2):
    v1 = normalize_vec3(v1)
    v2 = normalize_vec3(v2)
    
    cross = {
        "x": v1["y"]*v2["z"] - v1["z"]*v2["y"],
        "y": v1["z"]*v2["x"] - v1["x"]*v2["z"],
        "z": v1["x"]*v2["y"] - v1["y"]*v2["x"]
    }
    
    dot = v1["x"]*v2["x"] + v1["y"]*v2["y"] + v1["z"]*v2["z"]
    
    if dot < -0.999999:
        if abs(v1["x"]) < 0.6:
            axis = normalize_vec3({"x": 1, "y": 0, "z": 0})
        else:
            axis = normalize_vec3({"x": 0, "y": 1, "z": 0})
        axis = {
            "x": v1["y"]*axis["z"] - v1["z"]*axis["y"],
            "y": v1["z"]*axis["x"] - v1["x"]*axis["z"],
            "z": v1["x"]*axis["y"] - v1["y"]*axis["x"]
        }
        axis = normalize_vec3(axis)
        return {"w": 0, "x": axis["x"], "y": axis["y"], "z": axis["z"]}
    
    q = {
        "w": 1.0 + dot,
        "x": cross["x"],
        "y": cross["y"],
        "z": cross["z"]
    }
    return normalize_quat(q)

def quat_multiply(q1, q2):
    return {
        "w": q1["w"]*q2["w"] - q1["x"]*q2["x"] - q1["y"]*q2["y"] - q1["z"]*q2["z"],
        "x": q1["w"]*q2["x"] + q1["x"]*q2["w"] + q1["y"]*q2["z"] - q1["z"]*q2["y"],
        "y": q1["w"]*q2["y"] - q1["x"]*q2["z"] + q1["y"]*q2["w"] + q1["z"]*q2["x"],
        "z": q1["w"]*q2["z"] + q1["x"]*q2["y"] - q1["y"]*q2["x"] + q1["z"]*q2["w"]
    }

def quat_slerp(q1, q2, t):
    dot = q1["w"]*q2["w"] + q1["x"]*q2["x"] + q1["y"]*q2["y"] + q1["z"]*q2["z"]
    
    if dot > 0.9995:
        result = {
            "w": q1["w"] + t * (q2["w"] - q1["w"]),
            "x": q1["x"] + t * (q2["x"] - q1["x"]),
            "y": q1["y"] + t * (q2["y"] - q1["y"]),
            "z": q1["z"] + t * (q2["z"] - q1["z"])
        }
        return normalize_quat(result)
    
    if dot < 0:
        q2 = {"w": -q2["w"], "x": -q2["x"], "y": -q2["y"], "z": -q2["z"]}
        dot = -dot
    
    dot = max(-1.0, min(1.0, dot))
    
    theta_0 = math.acos(dot)
    theta = theta_0 * t
    
    sin_theta = math.sin(theta)
    sin_theta_0 = math.sin(theta_0)
    
    s1 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s2 = sin_theta / sin_theta_0
    
    return {
        "w": s1 * q1["w"] + s2 * q2["w"],
        "x": s1 * q1["x"] + s2 * q2["x"],
        "y": s1 * q1["y"] + s2 * q2["y"],
        "z": s1 * q1["z"] + s2 * q2["z"]
    }

def reset_rotation(controller_num=None):
    global controller_1_dict, controller_2_dict
    
    rot = R.from_matrix(trackers_arr[0]['rotation matrix'])
    q = rot.as_quat() 
    hmd_quat_dict = {"x": q[0], "y": q[1], "z": q[2], "w": q[3]}
    
    if controller_num == 1:
        if "gyro_quat" in controller_1_dict:
            controller_1_dict["gyro_quat"] = hmd_quat_dict.copy()
            controller_1_dict["last_good_quat"] = hmd_quat_dict.copy()
    elif controller_num == 2:
        if "gyro_quat" in controller_2_dict:
            controller_2_dict["gyro_quat"] = hmd_quat_dict.copy()
            controller_2_dict["last_good_quat"] = hmd_quat_dict.copy()
    else:
        if "gyro_quat" in controller_1_dict:
            controller_1_dict["gyro_quat"] = hmd_quat_dict.copy()
            controller_1_dict["last_good_quat"] = hmd_quat_dict.copy()
        if "gyro_quat" in controller_2_dict:
            controller_2_dict["gyro_quat"] = hmd_quat_dict.copy()
            controller_2_dict["last_good_quat"] = hmd_quat_dict.copy()

def start_calibration(controller_num=None):
    global controller_1_dict, controller_2_dict
    if controller_num == 1:
        if "gyro_bias" in controller_1_dict:
            has_accel = controller_1_dict["gyro_bias"].get("has_accel", False)
            controller_1_dict["gyro_bias"] = {
                "wx": 0.0, "wy": 0.0, "wz": 0.0,
                "ax": 0.0, "ay": 0.0, "az": 0.0,
                "tx": 0.0, "ty": 0.0, "tz": 0.0,
                "samples": 0,
                "has_accel": has_accel
            }
            p_controller_group.findChildren(QPushButton)[0].setText("calibrating...")
            settings_core.update_setting("gyro_calibration_1", None)
    elif controller_num == 2:
        if "gyro_bias" in controller_2_dict:
            has_accel = controller_2_dict["gyro_bias"].get("has_accel", False)
            controller_2_dict["gyro_bias"] = {
                "wx": 0.0, "wy": 0.0, "wz": 0.0,
                "ax": 0.0, "ay": 0.0, "az": 0.0,
                "tx": 0.0, "ty": 0.0, "tz": 0.0,
                "samples": 0,
                "has_accel": has_accel
            }
            p_controller_group.findChildren(QPushButton)[0].setText("calibrating...")
            settings_core.update_setting("gyro_calibration_2", None)  # Clear saved calibration
    else:
        # Calibrate both
        if "gyro_bias" in controller_1_dict:
            has_accel = controller_1_dict["gyro_bias"].get("has_accel", False)
            controller_1_dict["gyro_bias"] = {
                "wx": 0.0, "wy": 0.0, "wz": 0.0,
                "ax": 0.0, "ay": 0.0, "az": 0.0,
                "tx": 0.0, "ty": 0.0, "tz": 0.0,
                "samples": 0,
                "has_accel": has_accel
            }
            settings_core.update_setting("gyro_calibration_1", None)
        if "gyro_bias" in controller_2_dict:
            has_accel = controller_2_dict["gyro_bias"].get("has_accel", False)
            controller_2_dict["gyro_bias"] = {
                "wx": 0.0, "wy": 0.0, "wz": 0.0,
                "ax": 0.0, "ay": 0.0, "az": 0.0,
                "tx": 0.0, "ty": 0.0, "tz": 0.0,
                "samples": 0,
                "has_accel": has_accel
            }
            settings_core.update_setting("gyro_calibration_2", None)

running = True

def run_sdl_event_loop():
    global controller_1_dict, controller_2_dict, controller_arr, gyro_mod
    
    id_map = {} 

    def refresh_id_map():
        id_map.clear()
        for i, c in enumerate(controller_arr):
            iid = SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(c))
            id_map[iid] = i
           # print("f{iid} = {i}")

    while running:
        try:
            SDL_GameControllerUpdate()
            settings = settings_core.get_settings()
            
            p1_idx = settings.get("controller index 1", 0)
            p2_idx = settings.get("controller index 2", 1)
            

            event = SDL_Event()
            while SDL_PollEvent(event):
                if event.type == SDL_CONTROLLERDEVICEADDED:
                    new_c = SDL_GameControllerOpen(event.cdevice.which)
                    if new_c:
                        name = SDL_GameControllerName(new_c)
                        #print(name)

                        if SDL_GameControllerHasSensor(new_c, SDL_SENSOR_GYRO):
                            result = SDL_GameControllerSetSensorEnabled(new_c, SDL_SENSOR_GYRO, SDL_TRUE)
                        
                        if SDL_GameControllerHasSensor(new_c, SDL_SENSOR_ACCEL):
                            SDL_GameControllerSetSensorEnabled(new_c, SDL_SENSOR_ACCEL, SDL_TRUE)

                        controller_arr.append(new_c)
                        refresh_id_map()

                elif event.type == SDL_CONTROLLERDEVICEREMOVED:
                    instance_id = event.cdevice.which
                    to_remove = None
                    for i, c in enumerate(controller_arr):
                        if SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(c)) == instance_id:
                            to_remove = i
                            SDL_GameControllerClose(c)
                            break
                    if to_remove is not None:
                        controller_arr.pop(to_remove)
                        refresh_id_map()

                elif event.type == SDL_CONTROLLERSENSORUPDATE:
                    sender_id = event.csensor.which
                    if sender_id not in id_map: continue
                    
                    real_index = id_map[sender_id]
                    
                    target_dict = None
                    player_num = 0
                    
                    if real_index == p1_idx:
                        target_dict = controller_1_dict
                        player_num = 1
                    elif real_index == p2_idx:
                        target_dict = controller_2_dict
                        player_num = 2
                    
                    if target_dict is None: continue

                    if "gyro_quat" not in target_dict:
                        target_dict["gyro_quat"] = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                        target_dict["last_ts"] = event.csensor.timestamp
                        target_dict["last_good_quat"] = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                        
                        cal_key = f"gyro_calibration_{player_num}" 
                        saved_cal = settings.get(cal_key, {})
                        
                        if saved_cal is None:
                            saved_cal = {}
                        
                        target_dict["gyro_bias"] = {
                            "wx": saved_cal.get("wx", 0.0), "wy": saved_cal.get("wy", 0.0), "wz": saved_cal.get("wz", 0.0),
                            "ax": saved_cal.get("ax", 0.0), "ay": saved_cal.get("ay", 0.0), "az": saved_cal.get("az", 0.0),
                            "tx": saved_cal.get("tx", 0.02), "ty": saved_cal.get("ty", 0.02), "tz": saved_cal.get("tz", 0.02),
                            "samples": CALIBRATION_SAMPLES if saved_cal else 0
                        }

                    bias = target_dict["gyro_bias"]

                    if event.csensor.sensor == SDL_SENSOR_GYRO:
                        curr_ts = event.csensor.timestamp
                        dt = (curr_ts - target_dict["last_ts"]) / 1000000.0
                        target_dict["last_ts"] = curr_ts

                        pfx = f"gyro{player_num}"
                        raw_data = event.csensor.data
                        sens = settings.get(f"{pfx} sensitivity", 1.0)

                        ix = settings.get(f"{pfx} index x", 0)
                        iy = settings.get(f"{pfx} index y", 1)
                        iz = settings.get(f"{pfx} index z", 2)
                        
                        rwx = raw_data[ix] * (-1 if settings.get(f"{pfx} invert x", False) else 1)
                        rwy = raw_data[iy] * (-1 if settings.get(f"{pfx} invert y", False) else 1)
                        rwz = raw_data[iz] * (-1 if settings.get(f"{pfx} invert z", False) else 1)

                        if bias["samples"] < CALIBRATION_SAMPLES:
                            bias["wx"] += rwx; bias["wy"] += rwy; bias["wz"] += rwz
                            bias["samples"] += 1
                            if bias["samples"] == CALIBRATION_SAMPLES:
                                bias["wx"] /= CALIBRATION_SAMPLES
                                bias["wy"] /= CALIBRATION_SAMPLES
                                bias["wz"] /= CALIBRATION_SAMPLES
                                
                                save_data = {k: v for k, v in bias.items() if k != "samples"}
                                settings_core.update_setting(f"gyro_calibration_{player_num}", save_data)

                                p_controller_group.findChildren(QPushButton)[0].setText("calibration")
                            continue

                        wx = (rwx - bias["wx"]) * sens
                        wy = (rwy - bias["wy"]) * sens
                        wz = (rwz - bias["wz"]) * sens
                        
                        if math.sqrt(wx**2 + wy**2 + wz**2) < bias["tx"]: 
                            wx = wy = wz = 0

                        mag = math.sqrt(wx**2 + wy**2 + wz**2)
                        if mag > 0:
                            half_angle = (mag * dt) / 2.0
                            s = math.sin(half_angle) / mag
                            dq = {"w": math.cos(half_angle), "x": wx * s, "y": wy * s, "z": wz * s}
                            new_quat = normalize_quat(quat_multiply(target_dict["gyro_quat"], dq))
                            
                            if settings.get("bluetooth skip correction", True):
                                dot = abs(new_quat["w"] * target_dict["last_good_quat"]["w"] + 
                                         new_quat["x"] * target_dict["last_good_quat"]["x"] + 
                                         new_quat["y"] * target_dict["last_good_quat"]["y"] + 
                                         new_quat["z"] * target_dict["last_good_quat"]["z"])
                                
                                if dot > 0.95:
                                    target_dict["gyro_quat"] = new_quat
                                    target_dict["last_good_quat"] = new_quat
                                else:
                                    target_dict["gyro_quat"] = target_dict["last_good_quat"]
                            else:
                                target_dict["gyro_quat"] = new_quat
                                target_dict["last_good_quat"] = new_quat

                    elif event.csensor.sensor == SDL_SENSOR_ACCEL:
                        pfx = f"gyro{player_num}"
                        raw_accel = event.csensor.data

                        ix = settings.get(f"{pfx} index x", 0)
                        iy = settings.get(f"{pfx} index y", 1)
                        iz = settings.get(f"{pfx} index z", 2)

                        rax = raw_accel[ix] * (-1 if settings.get(f"{pfx} invert x", False) else 1)
                        ray = raw_accel[iy] * (-1 if settings.get(f"{pfx} invert y", False) else 1)
                        raz = raw_accel[iz] * (-1 if settings.get(f"{pfx} invert z", False) else 1)

                        if bias["samples"] < CALIBRATION_SAMPLES:
                            bias["ax"] += rax; bias["ay"] += ray; bias["az"] += raz
                        else:
                            ax = rax - bias.get("ax", 0.0)
                            ay = ray - bias.get("ay", 0.0)
                            az = raz - bias.get("az", 0.0)
                            
                            accel_mag = math.sqrt(ax**2 + ay**2 + az**2)
                            
                            if 0.9 < accel_mag < 1.1:
                                correction = quat_from_two_vectors(
                                    {"x": ax/accel_mag, "y": ay/accel_mag, "z": az/accel_mag}, 
                                    {"x": 0, "y": 0, "z": -1}
                                )
                                target_dict["gyro_quat"] = normalize_quat(quat_slerp(target_dict["gyro_quat"], correction, ALPHA))

            time.sleep(0.001)

        except Exception as e:
            #print(e)
            time.sleep(0.001)

def run_controller_worker(player_num):
    global controller_1_dict, controller_2_dict, controller_arr
    
    target_dict = controller_1_dict if player_num == 1 else controller_2_dict
    
    while running:
        try:
            settings = settings_core.get_settings()
            hw_index = settings.get(f"controller index {player_num}", player_num - 1)
            
            if 0 <= hw_index < len(controller_arr):
                controller_handle = controller_arr[hw_index]
                
                new_data = poll_hardware(controller_handle)
                
                detect_input_change(player_num, new_data, target_dict)
                
                target_dict.update(new_data)
                
                if get_mapped_action("reset gyro", str(player_num)):
                    reset_rotation(player_num)
                if get_mapped_action("calibrate gyro", str(player_num)):
                    start_calibration(player_num)
                    
            else:
                pass

            time.sleep(0.001)
            
        except Exception as e:
            #print(e)
            time.sleep(0.001)

def start_controller_mapping():
    global running
    running = True

    t_events = threading.Thread(target=run_sdl_event_loop, daemon=True, name="SDL_Event_Manager")
    t_events.start()
    
    t_p1 = threading.Thread(target=run_controller_worker, args=(1,), daemon=True, name="P1_Worker")
    t_p1.start()

    t_p2 = threading.Thread(target=run_controller_worker, args=(2,), daemon=True, name="P2_Worker")
    t_p2.start()

    return [t_events, t_p1, t_p2]


def poll_hardware(c):
    def a(axis):
        v = SDL_GameControllerGetAxis(c, axis) / 32767.0
        if abs(v) < DEADZONE: return 0.0
        return (v - (DEADZONE if v > 0 else -DEADZONE)) / (1.0 - DEADZONE)

    return {
        "a": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_A)),
        "b": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_B)),
        "x": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_X)),
        "y": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_Y)),
        "back": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_BACK)),
        "start": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_START)),
        
        "leftstick": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_LEFTSTICK)),
        "rightstick": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_RIGHTSTICK)),
        "guide": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_GUIDE)),
        "misc1": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_MISC1)),
        
        "leftshoulder": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_LEFTSHOULDER)),
        "rightshoulder": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_RIGHTSHOULDER)),
        "dpup": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_UP)),
        "dpdown": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_DOWN)),
        "dpleft": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_LEFT)),
        "dpright": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_RIGHT)),
        
        "leftx": a(SDL_CONTROLLER_AXIS_LEFTX),
        "lefty": a(SDL_CONTROLLER_AXIS_LEFTY),
        "rightx": a(SDL_CONTROLLER_AXIS_RIGHTX),
        "righty": a(SDL_CONTROLLER_AXIS_RIGHTY),
        "lefttrigger": a(SDL_CONTROLLER_AXIS_TRIGGERLEFT),
        "righttrigger": a(SDL_CONTROLLER_AXIS_TRIGGERRIGHT),
        
        "paddle1": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_PADDLE1)),
        "paddle2": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_PADDLE2)),
        "paddle3": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_PADDLE3)),
        "paddle4": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_PADDLE4)),
        "touchpad": bool(SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_TOUCHPAD)),
    }

def detect_input_change(c_idx, new_state, old_state):
    for key, val in new_state.items():
        old_val = old_state.get(key)
        
        if isinstance(val, bool):
            if val and not old_val:
                msg = f"{c_idx} {key}"
                mapping_label.findChild(QLabel).setText(msg)
                
        elif isinstance(val, float):
            if abs(val) > 0.1 and abs(val - old_val) > 0.05:
                msg = f"{c_idx} {key} {val:.2f}"
                mapping_label.findChild(QLabel).setText(msg)

#controller handler/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#camera//////////////////////////////////////////////////////////////////////////////////////////////////
SHOW_FEED = True
RESOLUTION_X = 640
RESOLUTION_Y = 480
MAX_HANDS_PER_CAMERA = 2
SWAP_HANDS_MODE = False
SMOOTHING_FACTOR = 0.8
Splay_mod = 2.0
MIN_CHANGE_THRESHOLD = 0.04
MAX_CHANGE_THRESHOLD = 0.4

REFERENCE_DEPTH_CM = 50.0
ref_3d_mag_right = 0.08
ref_3d_mag_left = 0.08
smoothed_z_right = REFERENCE_DEPTH_CM
smoothed_z_left = REFERENCE_DEPTH_CM
DEPTH_SMOOTHING = 0.2

caps = {}
caps_lock = threading.Lock()
camera_running = False
camera_ready = threading.Event()
camera_thread = None
hands = None

HAND_R, HAND_L = "right", "left"
VERSION = "v2"
PIPE_NAME_R = fr'\\.\pipe\vrapplication\input\glove\{VERSION}\{HAND_R}'
PIPE_NAME_L = fr'\\.\pipe\vrapplication\input\glove\{VERSION}\{HAND_L}'
PACK_FORMAT2 = '<20f5f2f8?f'
SEND_INTERVAL = 0.0001

hand_data = {
    "l pos x": 0.0, "l pos y": 0.0, "l pos z": 0.0,
    "l rot x": 0.0, "l rot y": 0.0, "l rot z": 0.0, "l rot w": 1.0,
    "l flexion": [0.0] * 20,
    "l splay": [0.0] * 5,
    "l joy_x": 0.0, "l joy_y": 0.0,
    "l joy_button": False, "l trigger_button": False,
    "l a_button": False, "l b_button": False,
    "l grab": False, "l pinch": False,
    "l menu": False, "l calibrate": False,
    "l trigger_value": 0.0,
    
    "r pos x": 0.0, "r pos y": 0.0, "r pos z": 0.0,
    "r rot x": 0.0, "r rot y": 0.0, "r rot z": 0.0, "r rot w": 1.0,
    "r flexion": [0.0] * 20,
    "r splay": [0.0] * 5,
    "r joy_x": 0.0, "r joy_y": 0.0,
    "r joy_button": False, "r trigger_button": False,
    "r a_button": False, "r b_button": False,
    "r grab": False, "r pinch": False,
    "r menu": False, "r calibrate": False,
    "r trigger_value": 0.0,
}

right_hand_smoothed_flexion = [0.0] * 20
left_hand_smoothed_flexion = [0.0] * 20
right_hand_smoothed_splay = [0.0] * 5
left_hand_smoothed_splay = [0.0] * 5

MP_LANDMARK_IDS = [
    (1, 2, 3, 4),      #thumb
    (5, 6, 7, 8),      #index
    (9, 10, 11, 12),   #middle
    (13, 14, 15, 16),  #ring
    (17, 18, 19, 20)   #pinky
]

FINGER_JOINTS_FOR_SPLAY = [(5, 6), (9, 10), (13, 14), (17, 18)]
THUMB_SPLAY_ID = 2

FLEXION_MIN_ANGLE, FLEXION_MAX_ANGLE = 2.5, 3.1
SPLAY_THUMB_MIN_ANGLE, SPLAY_THUMB_MAX_ANGLE = 0.5, 1.5
SPLAY_FINGER_MIN_ANGLE, SPLAY_FINGER_MAX_ANGLE = 0.1, 0.7


def get_vector(l1, l2):
    return np.array([l2['x'] - l1['x'], l2['y'] - l1['y'], l2['z'] - l1['z']])

def get_angle(v1, v2):
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return np.arccos(np.clip(dot / norm, -1.0, 1.0)) if norm != 0 else 0.0

def normalize_value(value, min_val, max_val):
    return np.clip((value - min_val) / (max_val - min_val), 0.0, 1.0) if max_val != min_val else 0.0

def matrix_to_quaternion(m):
    tr = m[0,0] + m[1,1] + m[2,2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        return (m[2,1] - m[1,2])/s, (m[0,2] - m[2,0])/s, (m[1,0] - m[0,1])/s, 0.25*s
    elif (m[0,0] > m[1,1]) and (m[0,0] > m[2,2]):
        s = np.sqrt(1.0 + m[0,0] - m[1,1] - m[2,2]) * 2
        return 0.25*s, (m[0,1] + m[1,0])/s, (m[0,2] + m[2,0])/s, (m[2,1] - m[1,2])/s
    elif m[1,1] > m[2,2]:
        s = np.sqrt(1.0 + m[1,1] - m[0,0] - m[2,2]) * 2
        return (m[0,1] + m[1,0])/s, 0.25*s, (m[1,2] + m[2,1])/s, (m[0,2] - m[2,0])/s
    else:
        s = np.sqrt(1.0 + m[2,2] - m[0,0] - m[1,1]) * 2
        return (m[0,2] + m[2,0])/s, (m[1,2] + m[2,1])/s, 0.25*s, (m[1,0] - m[0,1])/s

def map_to_glove(hand_label, hand_landmarks, hand_prefix):
    global right_hand_smoothed_flexion, left_hand_smoothed_flexion
    global right_hand_smoothed_splay, left_hand_smoothed_splay
    
    is_right = (hand_label.lower() == "right")
    flex_buf = right_hand_smoothed_flexion if is_right else left_hand_smoothed_flexion
    splay_buf = right_hand_smoothed_splay if is_right else left_hand_smoothed_splay
    
    L = {lm['id']: lm for lm in hand_landmarks}
    
    # Flexion
    for finger_i, mp_ids in enumerate(MP_LANDMARK_IDS):
        for joint_i in range(3):
            p1_id = mp_ids[joint_i-1] if joint_i > 0 else (0 if finger_i == 0 else mp_ids[0]-1)
            p2_id, p3_id = mp_ids[joint_i], mp_ids[joint_i+1]
            angle = get_angle(get_vector(L[p2_id], L[p1_id]), get_vector(L[p2_id], L[p3_id]))
            val = 1.0 - normalize_value(angle, FLEXION_MIN_ANGLE, FLEXION_MAX_ANGLE)
            idx = finger_i * 4 + joint_i
            flex_buf[idx] = (SMOOTHING_FACTOR * val) + ((1 - SMOOTHING_FACTOR) * flex_buf[idx])
        flex_buf[finger_i * 4 + 3] = flex_buf[finger_i * 4 + 2]
    
    # Splay
    splay_buf[0] = normalize_value(
        get_angle(get_vector(L[0], L[9]), get_vector(L[0], L[THUMB_SPLAY_ID])),
        SPLAY_THUMB_MIN_ANGLE, SPLAY_THUMB_MAX_ANGLE
    )
    for i in range(len(FINGER_JOINTS_FOR_SPLAY)-1):
        v1 = get_vector(L[FINGER_JOINTS_FOR_SPLAY[i][0]], L[FINGER_JOINTS_FOR_SPLAY[i][1]])
        v2 = get_vector(L[FINGER_JOINTS_FOR_SPLAY[i+1][0]], L[FINGER_JOINTS_FOR_SPLAY[i+1][1]])
        splay_buf[i+1] = normalize_value(
            get_angle(v1, v2) * Splay_mod,
            SPLAY_FINGER_MIN_ANGLE, SPLAY_FINGER_MAX_ANGLE
        )
    
    px, py, pz, rx, ry, rz, rw = calculate_hand_position_rotation(L, is_right)
    
    hand_data.update({
        f"{hand_prefix} pos x": px,
        f"{hand_prefix} pos y": py,
        f"{hand_prefix} pos z": pz,
        f"{hand_prefix} rot x": rx,
        f"{hand_prefix} rot y": ry,
        f"{hand_prefix} rot z": rz,
        f"{hand_prefix} rot w": rw,
        f"{hand_prefix} flexion": flex_buf.copy(),
        f"{hand_prefix} splay": splay_buf.copy(),
        f"{hand_prefix} pinch": np.linalg.norm(get_vector(L[8], L[4])) < 0.05
    })

def update_actions():
    #try:
    for prefix, full_name in [("r", "right"), ("l", "left")]:
        hand_data[f"{prefix} a_button"] = get_mapped_action(f'{full_name} a')
        hand_data[f"{prefix} b_button"] = get_mapped_action(f'{full_name} b')
        hand_data[f"{prefix} grab"] = get_mapped_action(f'{full_name} grip')
        hand_data[f"{prefix} menu"] = get_mapped_action(f'{full_name} menu')
        hand_data[f"{prefix} calibrate"] = get_mapped_action(f'{full_name} touch modifier')
        
        t_val = int(get_mapped_action(f'{full_name} trigger'))
        hand_data[f"{prefix} trigger_value"] = t_val
        hand_data[f"{prefix} trigger_button"] = (t_val == 1.0)
        
        hand_data[f"{prefix} joy_x"] = get_mapped_action(f'{full_name} joy x')
        hand_data[f"{prefix} joy_y"] = get_mapped_action(f'{full_name} joy y')
        hand_data[f"{prefix} joy_button"] = get_mapped_action(f'{full_name} joy button')
    # except:
    #     pass

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def calculate_hand_position_rotation(L, is_right):
    global smoothed_z_right, smoothed_z_left
    
    wrist, mid, idx, pky = L[0], L[9], L[5], L[17]
    dx, dy, dz = mid['x']-wrist['x'], mid['y']-wrist['y'], (mid['z']-wrist['z'])*2.2
    mag = np.sqrt(dx**2 + dy**2 + dz**2)
    ref = ref_3d_mag_right if is_right else ref_3d_mag_left
    raw_z = (ref / mag * REFERENCE_DEPTH_CM) if mag > 1e-6 else REFERENCE_DEPTH_CM
    
    if is_right:
        smoothed_z_right = (smoothed_z_right * (1 - DEPTH_SMOOTHING)) + (raw_z * DEPTH_SMOOTHING)
        pos_z = -smoothed_z_right
    else:
        smoothed_z_left = (smoothed_z_left * (1 - DEPTH_SMOOTHING)) + (raw_z * DEPTH_SMOOTHING)
        pos_z = -smoothed_z_left
    
    v_fwd = np.array([mid['x'] - wrist['x'], -(mid['y'] - wrist['y']), -(mid['z'] - wrist['z'])])
    v_side_t = np.array([idx['x'] - pky['x'], -(idx['y'] - pky['y']), -(idx['z'] - pky['z'])])
    v_fwd /= (np.linalg.norm(v_fwd) + 1e-6)
    v_side_t /= (np.linalg.norm(v_side_t) + 1e-6)
    v_up = np.cross(v_fwd, v_side_t) if is_right else np.cross(v_side_t, v_fwd)
    v_up /= (np.linalg.norm(v_up) + 1e-6)
    v_side = np.cross(v_up, v_fwd)
    
    qx, qy, qz, qw = matrix_to_quaternion(np.stack([v_side, v_up, v_fwd], axis=1))
    return wrist['x'], 1.0 - wrist['y'], pos_z, qx, qy, qz, qw

def camera_loop():
    global camera_running, caps, hands
    
    try:
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS_PER_CAMERA,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        p_time = 0
        camera_running = True
        
        timeout = 0
        while camera_running and timeout < 50:
            with caps_lock:
                if caps:
                    break
            time.sleep(0.0001)
            timeout += 1
        
        if not caps:
            camera_running = False
            return
        
        camera_ready.set()
        
        while camera_running:
            update_actions()
            
            with caps_lock:
                cam_items = list(caps.items())
            
            for cam_id, cap in cam_items:
                success, image = cap.read()
                if not success:
                    continue
                
                image = cv2.flip(image, 1)
                
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                res = hands.process(rgb_image)
                
                if res.multi_hand_landmarks:
                    for i, hand_lms in enumerate(res.multi_hand_landmarks):
                        # Get Hand Label (Left/Right)
                        label = res.multi_handedness[i].classification[0].label
                        
                        # Draw Landmarks
                        mp_drawing.draw_landmarks(
                            image,
                            hand_lms,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style()
                        )
                        
                        # Process data for Gloves
                        l_list = [{'id': id, 'x': lm.x, 'y': lm.y, 'z': lm.z} 
                                 for id, lm in enumerate(hand_lms.landmark)]
                        prefix = ("l" if label == "Right" else "r") if SWAP_HANDS_MODE else \
                                ("r" if label == "Right" else "l")
                        map_to_glove(label, l_list, prefix)
                        
                        # Add Label Text to Preview
                        h, w, _ = image.shape
                        cx, cy = int(hand_lms.landmark[0].x * w), int(hand_lms.landmark[0].y * h)
                        cv2.putText(image, f"{label} Hand", (cx, cy - 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # FPS Calculation
                c_time = time.time()
                fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
                p_time = c_time
                cv2.putText(image, f"FPS: {int(fps)}", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                if SHOW_FEED:
                    cv2.imshow(f'Hand Tracking {cam_id}', image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        camera_running = False
            
            time.sleep(0.0001)
    
    except Exception as e:
        #print(e)
        camera_running = False
    
    finally:
        with caps_lock:
            for cap in caps.values():
                cap.release()
            caps.clear()
        cv2.destroyAllWindows()
        if hands:
            hands.close()
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def opengloves_sender(pipe_name, hand_prefix):
    while camera_running:
        handle = None
        try:
            payload = (hand_data[f"{hand_prefix} flexion"] +
                      hand_data[f"{hand_prefix} splay"] +
                      [hand_data[f"{hand_prefix} joy_x"],
                       hand_data[f"{hand_prefix} joy_y"],
                       hand_data[f"{hand_prefix} joy_button"],
                       hand_data[f"{hand_prefix} trigger_button"],
                       hand_data[f"{hand_prefix} a_button"],
                       hand_data[f"{hand_prefix} b_button"],
                       hand_data[f"{hand_prefix} grab"],
                       hand_data[f"{hand_prefix} pinch"],
                       hand_data[f"{hand_prefix} menu"],
                       hand_data[f"{hand_prefix} calibrate"],
                       hand_data[f"{hand_prefix} trigger_value"]])
            
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            win32file.WriteFile(handle, struct.pack(PACK_FORMAT2, *payload))
        except:
            pass
        finally:
            if handle:
                win32file.CloseHandle(handle)
        time.sleep(SEND_INTERVAL)

def create_cameras():
    global caps
    
    with caps_lock:
        for cap in caps.values():
            cap.release()
        caps.clear()
        
        try:
            idx = settings_core.get_settings().get('camera index', 0)
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            
            if not cap.isOpened():
                #print(e)
                return False
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_X)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_Y)
            caps[idx] = cap
            return True
        
        except Exception as e:
            #print(e)
            return False

def start_opengloves():
    global camera_running, camera_thread
    
    if camera_running:
        camera_running = False
        if camera_thread:
            camera_thread.join(timeout=2.0)
        time.sleep(0.2)
    
    camera_ready.clear()
    
    if settings_core.get_settings().get('opengloves'):
        if create_cameras():
            camera_running = True
            camera_thread = threading.Thread(target=camera_loop, daemon=True)
            camera_thread.start()
            
            if camera_ready.wait(timeout=3.0):
                threading.Thread(target=opengloves_sender, 
                               args=(PIPE_NAME_R, "r"), daemon=True).start()
                threading.Thread(target=opengloves_sender, 
                               args=(PIPE_NAME_L, "l"), daemon=True).start()
            else:
                camera_running = False
        else:
            #no camera on startup
            pass
#camera//////////////////////////////////////////////////////////////////////////////////////////////////

first_label = create_label({
    "text" : "steamvr is not running :(", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})

if __name__ == '__main__':
    if settings_core.get_settings()['opengloves']:
        start_opengloves()

    start_controller_mapping()

    start_send_data()
    start_update_vrlabel()

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

layout_main.addWidget(create_label({
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
layout_main.addWidget(res)

layout_main.addWidget(create_label({
    "text" : "---------Misc---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
misc_group1 = create_group_checkbox([
    {
        "text" : "Stereoscopic(SBS)", 
        "default" : settings_core.get_settings()['stereoscopic'], 
        "func" : lambda: change_FOV_on_check(misc_group1)
    },
    {
        "text" : "Fullscreen", 
        "default": settings_core.get_settings()['fullscreen'],
        "func"  : lambda: settings_core.update_setting("fullscreen", misc_group1.findChildren(QCheckBox)[1].isChecked())
    }
])
layout_main.addWidget(misc_group1)

misc = create_group_doublespinbox([
    {
        "text" : "IPD", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['ipd'], 
        "steps" : 0.001, 
        "func" : lambda: settings_core.update_setting("ipd", misc.findChildren(QDoubleSpinBox)[0].value()) 
    },
    {
        "text" : "Distance from tracker to eyes", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['head to eye dist'], 
        "steps" : 0.001, 
        "func" : lambda: settings_core.update_setting("head to eye dist", misc.findChildren(QDoubleSpinBox)[1].value()) 
    }
])
layout_main.addWidget(misc)

fov_label = create_label({
    "text" : "---------FOV(using Mono)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(fov_label)

#/////////////////////////////////////////////////////
def calculate_vr_fov():
    settings = settings_core.get_settings()
    diagonal_fov_deg = recommended_label.findChild(QDoubleSpinBox).value()
    settings_core.update_setting("fov",diagonal_fov_deg)
    width = settings['resolution x']
    height = settings['resolution y']

    diag_rad = math.radians(diagonal_fov_deg)

    aspect = width / height
    
    tan_half_diag = math.tan(diag_rad / 2)
    tan_half_v = tan_half_diag / math.sqrt(aspect**2 + 1)
    tan_half_h = aspect * tan_half_v
    
    h_fov_deg = math.degrees(math.atan(tan_half_h) * 2)/2
    v_fov_deg = math.degrees(math.atan(tan_half_v) * 2)/2

    recommended_label.findChildren(QPushButton)[0].setText(f"outer {h_fov_deg:.2f}")
    recommended_label.findChildren(QPushButton)[1].setText(f"inner {h_fov_deg:.2f}")
    recommended_label.findChildren(QPushButton)[2].setText(f"top {v_fov_deg:.2f}")
    recommended_label.findChildren(QPushButton)[3].setText(f"bottom {v_fov_deg:.2f}")

def set_fov(type, botton):
    settings = settings_core.get_settings()
    if settings['stereoscopic']:
        settings_core.update_setting(f"{type} stereo", float(botton.text().removeprefix(type)))
    else:
        settings_core.update_setting(f"{type} mono", float(botton.text().removeprefix(type)))

    change_FOV_on_check(misc_group1)

recommended_label = create_group_horizontal([{
        "type" : "label",
        "text" : "Recommended(click to set):", 
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "button", 
        "text" : "outer", 
        "enabled" : True,
        "func"  : lambda: set_fov("outer",recommended_label.findChildren(QPushButton)[0])
    },
    {
        "type" : "button", 
        "text" : "inner", 
        "enabled" : True,
        "func"  : lambda: set_fov("inner",recommended_label.findChildren(QPushButton)[1])
    },    {
        "type" : "button", 
        "text" : "top", 
        "enabled" : True,
        "func"  : lambda: set_fov("top",recommended_label.findChildren(QPushButton)[2])
    },
    {
        "type" : "button", 
        "text" : "bottom", 
        "enabled" : True,
        "func"  : lambda: set_fov("bottom",recommended_label.findChildren(QPushButton)[3])
    },
    {
        "type" : "doublespinbox",
        "text" : "for FOV =",
        "min":-999999999,
        "max":999999999,
        "default": settings_core.get_settings()['fov'],
        "steps" : 0.01,
        "func"  : lambda: calculate_vr_fov()
    }])

layout_main.addWidget(recommended_label)

calculate_vr_fov()
#/////////////////////////////////////////////////////

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
layout_main.addWidget(fov_group)

change_FOV_on_check(misc_group1)

layout_main.addWidget(create_label({
    "text" : "---------Offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world x", offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world y", offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world z", offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world yaw", offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world pitch", offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset world roll", offsets_world.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_main.addWidget(offsets_world)

offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local x", offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local y", offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local z", offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local yaw", offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local pitch", offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset local roll", offsets_local.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_main.addWidget(offsets_local)
#main/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#driver/////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
        pass

def get_activateMultipleDrivers_true():
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
            return False
        
        if data["steamvr"].get("activateMultipleDrivers") is True:
            return True
        
        return False

    except Exception as e:
        return False

set_activateMultipleDrivers_true()

def install_driver():
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    source_folder = os.path.join(script_dir, "assets", "driver to copy")
    

    destination_folder = settings_core.get_settings()['drivers path']
    
    if not os.path.exists(source_folder):
        update_install_and_config_label(True)
        return

    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        update_install_and_config_label(False)
    except Exception as e:
        #print(e)
        update_install_and_config_label(True)

def remove_driver():
    folder_path = settings_core.get_settings()['drivers path'] + '/glassvrdriver'

    if not os.path.exists(folder_path):
            return

    try:
        shutil.rmtree(folder_path)
        update_install_and_config_label(False)
        # install_buttons.findChildren(QPushButton)[1].setText("uninstalled successfully")
        # time.sleep(3)
        # install_buttons.findChildren(QPushButton)[1].setText("uninstall")

    except:
        update_install_and_config_label(True)

tab_driver = QWidget()
layout_driver = QVBoxLayout(tab_driver)
layout_driver.setSpacing(0)

def folder_exist(path: str):
    return os.path.isdir(path)

def driver_path_changed():
    set_activateMultipleDrivers_true()
    settings_core.update_setting('drivers path',driver_path.findChild(QLineEdit).text())
    update_install_and_config_label()

def config_path_changed():
    set_activateMultipleDrivers_true()
    settings_core.update_setting('vrsettings path',vr_config_path.findChild(QLineEdit).text())
    update_install_and_config_label()

driver_path = create_lineedit({
    "text" : "steamvr drivers folder path",
    "default" : settings_core.get_settings()['drivers path'],
    "func" : lambda: driver_path_changed()
})
layout_driver.addWidget(driver_path)
vr_config_path = create_lineedit({
    "text" : "steam config folder path",
    "default" : settings_core.get_settings()['vrsettings path'],
    "func" : lambda: config_path_changed()
})
layout_driver.addWidget(vr_config_path)

install_label = create_label({
    "text" : "driver is not installed, click to install to install!", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(install_label)

config_label = create_label({
    "text" : "config", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_driver.addWidget(config_label)

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

def update_install_and_config_label(failed = False):
    install_leb =  install_label.findChild(QLabel)
    config_leb =  config_label.findChild(QLabel)

    if failed:
        install_leb.setText("action failed, close steam completely and try again")
        install_buttons.findChildren(QPushButton)[0].setText("install")
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            install_leb.setText("driver is installed!")
            install_buttons.findChildren(QPushButton)[0].setText("reinstall")
            install_buttons.findChildren(QPushButton)[1].setEnabled(True)
        else:
            install_leb.setText("driver is not installed, click to install to install!")
            install_buttons.findChildren(QPushButton)[0].setText("install")
            install_buttons.findChildren(QPushButton)[1].setEnabled(False)

    #//////////////////////////////////////////////////////////////////////////////////////////////

    if get_activateMultipleDrivers_true():
        config_leb.setText("steamvr.vrsettings has activateMultipleDrivers : true, all good :)")
    else:
        if folder_exist(settings_core.get_settings()['drivers path'] + "/glassvrdriver"):
            config_leb.setText("steamvr.vrsettings is missing: activateMultipleDrivers : false, set the correct path and click to reinstall to add it!")
        else:
            config_leb.setText("steamvr.vrsettings is missing: activateMultipleDrivers : false, set the correct path and click to install to add it!")

update_install_and_config_label()

layout_driver.addWidget(create_label({
    "text" : "---------Config---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
layout_driver.addWidget(create_button({
        "text" : "reset config(ui won't update)",
        "enabled" : True,
        "func"  : lambda: settings_core.reset_settings()
    }))
config = create_group_horizontal([{
        "type" : "button", 
        "text" : "open config location", 
        "enabled" : True,
        "func"  : lambda: os.startfile(settings_core.get_path())#.removesuffix("\settings.json"))
    },
    {"type" : "label",
     "text" :settings_core.get_path().removesuffix("\settings.json"),
     "alignment" : Qt.AlignmentFlag.AlignCenter
    }])
layout_driver.addWidget(config)

#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.RequestException:
        return "NO INTERNET???"
    
def list_mac_addresses():
    interfaces = psutil.net_if_addrs()
    for interface_name, snics in interfaces.items():
        for snic in snics:
            if snic.family in (psutil.AF_LINK, -1):
                # print(f"Interface: {interface_name}")
                # print(f"  MAC Address: {snic.address}")
                #get first mac address
                return snic.address

dialog = 0
def click():
    global dialog

    match dialog:
        case 0:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "OUCH!!!!!!!!!!!", ":)", 0)
            ctypes.windll.user32.MessageBoxW(0, "why???????????????", ":)", 0)
        case 1:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "STOP!!!!", ":)", 0)
        case 2:
            ctypes.windll.user32.MessageBoxW(0, "if i'll show you something cool, will you stop clicking?", ":)", 0)
            dialog += 1
            webbrowser.open("https://danixmir.itch.io/hyperlost")
            ctypes.windll.user32.MessageBoxW(0, "its a game i made!", ":>", 0)
        case 3:
            response = ctypes.windll.user32.MessageBoxW(0, "do you like it?", ":)", 4)
            if response == 6:
                dialog += 1
                ctypes.windll.user32.MessageBoxW(0, "thank you!!!", ":)", 0)
            else:
                system = platform.system()
                if system == "Windows":
                    os.system("shutdown /p")#"shutdown /p" #"shutdown /s /t"
                elif system == "Linux" or system == "Darwin":
                    os.system("sudo shutdown -h now")
        case 4:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "AHH!!!!!!!!!!!!!!!!!!!!!!!!", ":)", 0)
        case 5:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you promised you'll stop", ":)", 0)
        case 6:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i feel betrayed", ":)", 0)
        case 7:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 8:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "go do something else!!!!!!!!", ":)", 0)
        case 9:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "can you stop??????????", ":)", 0)
        case 10:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "plz stop", ":)", 0)
        case 11:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i have nothing more to show you", ":)", 0)
        case 12:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "(ignores)", ":)", 0)
        case 13:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i know where you live", ":)", 0)
        case 14:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "ip: " + get_public_ip() + "\nmac: " + list_mac_addresses(), ":)", 0)
        case 15:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "now will you stop?", ":)", 0)
        case 16:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i don't understand", ":)", 0)
        case 17:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "since when you were the one in control?", ":)", 0)
        case 18:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "hehe, that was a reference", ":)", 0)
        case 19:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "seriously stop", ":)", 0)
        case 20:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you don't know what you're doing", ":)", 0)
        case 21:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "YOU WILL KILL US BOTH", ":)", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "or not", ":)", 0)
        case 22:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "this is the last straw", ":)", 0)
        case 23:
            dialog += 1
            os.startfile("C:\Windows\System32")
            ctypes.windll.user32.MessageBoxW(0, "I'M GONNA DO IT", ":)", 0)
        case 24:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "wow", ":)", 0)
        case 25:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "i give up", ":)", 0)
        case 26:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 27:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 28:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "...", ":)", 0)
        case 29:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "so.....?", ":)", 0)
        case 30:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "error", "Alert", 0)
        case 31:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "click one more time i dare you", ":)", 0)
        case 32:
            dialog += 1
            for n in range(2147483647):
                time.sleep(0.01)
                webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        case 34:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "you know what, you win", ":)", 0)
        case 35:
            dialog += 1
            ctypes.windll.user32.MessageBoxW(0, "the next dialog is the last, check the source code if you don't believe me", ":)", 0)
        case _:
            ctypes.windll.user32.MessageBoxW(0, "gg", ":)", 0)

tab_credits = QWidget()
layout_credits = QVBoxLayout(tab_credits)
layout_credits.setSpacing(0)

def create_credits():
    create_group = QWidget()
    layout_credits1 = QVBoxLayout(create_group)

    label = QLabel("DaniXmir")
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)


    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # image_path = os.path.join(script_dir, "assets", "fix.png")
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    image_path = os.path.join(script_dir, "assets", "fix")


    image_button = QPushButton()
    image = QPixmap(image_path)
    scaled_pixmap = image.scaled(
        100, 100, 
        Qt.AspectRatioMode.KeepAspectRatio, 
        Qt.TransformationMode.FastTransformation
    )
    image_button.setIcon(QIcon(scaled_pixmap))
    image_button.setIconSize(QSize(100, 100))
    image_button.setStyleSheet("QPushButton { border: none; background: none; }")
    image_button.clicked.connect(lambda: click())
    layout_credits1.addWidget(image_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

    group_links = QWidget()
    layout_link = QHBoxLayout(group_links)
    
    link = '<a href=https://github.com/DaniXmir/GlassVr> https://github.com/DaniXmir/GlassVr </a>'
    label1 = QLabel("project github:" + link)
    label1.setTextFormat(Qt.TextFormat.RichText)
    label1.setOpenExternalLinks(True)
    label1.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_link.addWidget(label1)
    #layout_credits1.addWidget(label)

    link = '<a href=https://discord.gg/jyvWdKBpPj> https://discord.gg/jyvWdKBpPj </a>'
    label2 = QLabel("discord server:" + link)
    label2.setTextFormat(Qt.TextFormat.RichText)
    label2.setOpenExternalLinks(True)
    label2.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_link.addWidget(label2)
    #layout_credits1.addWidget(label)

    layout_credits1.addWidget(group_links)

    return create_group


layout_credits.addWidget(create_credits())
#credits/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_controllers = QWidget()
layout_controllers = QVBoxLayout(tab_controllers)
layout_controllers.setSpacing(0)

#/////////////
tab_enable = QWidget()
layout_enable = QHBoxLayout(tab_enable)

check_cr = create_checkbox(
    {
        "text" : "enable left controller", 
        "default" : settings_core.get_settings()['enable cl'], 
        "func" : lambda: settings_core.update_setting("enable cl",check_cr.findChild(QCheckBox).isChecked())
    })
layout_enable.addWidget(check_cr)

label3 = create_label({
    "text" : "<- left (enable) right ->", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_enable.addWidget(label3)

check_cl = create_checkbox(
    {
        "text" : "enable right controller", 
        "default" : settings_core.get_settings()['enable cr'], 
        "func" : lambda: settings_core.update_setting("enable cr",check_cl.findChild(QCheckBox).isChecked())
    })
layout_enable.addWidget(check_cl)
layout_controllers.addWidget(tab_enable)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cr modes//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crpos_specific_widget(layout, combo):
    settings_core.update_setting(f'crpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        case "keyboard":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "doublespinbox", 
                    "text" :"camera depth modifier", 
                    "min":-999999999, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['camera z'], 
                    "steps" : 0.001,
                    "func"  : lambda: settings_core.update_setting("camera z", t.findChildren(QDoubleSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

def create_crpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right position mode",
            "default": settings.get(f'crpos mode', "redirect"),
            "items": ["redirect", "hand tracking"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_crpos_widget())
#pos///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crrot_specific_widget(layout, combo):
    settings_core.update_setting(f'crrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    #settings = settings_core.get_settings()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['crrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("crrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "button",
                    "enabled" : True,
                    "text" :"apply recommendet offsets", 
                    "func"  : lambda: apply_hand_offsets("cr")
                }])
            layout.addWidget(t)

        case "gyro":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"controller index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings().get(f'cr gyro index',0), 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("cr gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

def create_crrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "right rotation mode",
            "default": settings.get(f'crrot mode', "redirect"),
            "items": ["redirect", "hand tracking", "gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    crrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_crrot_widget())
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cr modes////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cl modes////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def clpos_specific_widget(layout, combo):
    settings_core.update_setting(f'clpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)
        case "keyboard":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clpos index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clpos index", t.findChildren(QSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "doublespinbox", 
                    "text" :"camera depth modifier", 
                    "min":-999999999, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['camera z'], 
                    "steps" : 0.001,
                    "func"  : lambda: settings_core.update_setting("camera z", t.findChildren(QDoubleSpinBox)[0].value())
                }])
            
            layout.addWidget(t)

def create_clpos_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left position mode",
            "default": settings.get(f'clpos mode', "redirect"),
            "items": ["redirect", "hand tracking"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clpos_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_clpos_widget())
#pos//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#rot//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def clrot_specific_widget(layout, combo):
    settings_core.update_setting(f'clrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()

    match mode:
        case "redirect":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "mouse":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"test1", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                },{
                    "type" : "spinbox", 
                    "text" :"test2", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings()['clrot index'], 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("clrot index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

        case "hand tracking":
            t = create_group_horizontal([{
                    "type" : "button",
                    "enabled" : True,
                    "text" :"apply recommendet offsets", 
                    "func"  : lambda: apply_hand_offsets("cl")
                }])
            layout.addWidget(t)

        case "gyro":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"controller index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings_core.get_settings().get(f'cl gyro index',0), 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting("cl gyro index", t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

def create_clrot_widget():
    settings = settings_core.get_settings()

    tab_extra = QWidget()
    layout_extra = QHBoxLayout(tab_extra)

    combo_extra = create_combobox({
            "type" : "combobox",
            "text": "left rotation mode",
            "default": settings.get(f'clrot mode', "redirect"),
            "items": ["redirect", "hand tracking", "gyro"],#, "keyboard"],# add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))
        })
    
    layout_extra.addWidget(combo_extra)
    clrot_specific_widget(layout_extra, combo_extra.findChild(QComboBox))

    return tab_extra

layout_controllers.addWidget(create_clrot_widget())
#rot///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#cl modes/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def apply_hand_offsets(device):
    if device == "cr":
        settings_core.update_setting(f"{device} offset world yaw", 2.560)
        cr_offsets_world.findChildren(QDoubleSpinBox)[3].setValue(2.560)

        settings_core.update_setting(f"{device} offset world pitch", -0.280)
        cr_offsets_world.findChildren(QDoubleSpinBox)[4].setValue(-0.280)

        settings_core.update_setting(f"{device} offset world roll", 2.060)
        cr_offsets_world.findChildren(QDoubleSpinBox)[5].setValue(-0.280)

    else:
        settings_core.update_setting(f"{device} offset world yaw", 3.860)
        cl_offsets_world.findChildren(QDoubleSpinBox)[3].setValue(3.860)

        settings_core.update_setting(f"{device} offset world pitch", 0.190)
        cl_offsets_world.findChildren(QDoubleSpinBox)[4].setValue(0.190)

        settings_core.update_setting(f"{device} offset world roll", 1.990)
        cl_offsets_world.findChildren(QDoubleSpinBox)[5].setValue(1.990)

button_config = [    
    ("a", "a"),
    ("b", "b"),
    ("x", "x"),
    ("y", "y"),
    
    ("d-pad down", "dpdown"),
    ("d-pad left", "dpleft"),
    ("d-pad right", "dpright"),
    ("d-pad up", "dpup"),

    ("left trigger", "lefttrigger"),
    ("left bumper", "leftshoulder"),
    ("right trigger", "righttrigger"),
    ("right bumper", "rightshoulder"),

    ("left joy x", "leftx"),
    ("left joy y", "lefty"),
    ("left stick click", "leftstick"),

    ("right joy x", "rightx"),
    ("right joy y", "righty"),
    ("right stick click", "rightstick"),

    ("paddle 1", "paddle1"),
    ("paddle 2", "paddle2"),
    ("paddle 3", "paddle3"),
    ("paddle 4", "paddle4"),

    ("back", "back"),
    ("start", "start"),
    ("guide", "guide"),
]

buttons_per_row = 9
#combos = []

combo_inputs = ["right a","right b","right grip","right menu","right trigger","right joy button","right joy x","right joy y","right touch button","right touch x","right touch y",
                "right touch modifier",
                "left a","left b","left grip","left menu","left trigger","left joy button","left joy x","left joy y","left touch button","left touch x","left touch y",
                "left touch modifier", "reset gyro", "calibrate gyro", "none", 
                ]

current_mapping_slot = 0 

def refresh_ui_values():
    settings = settings_core.get_settings()
    p_num = current_mapping_slot + 1
    prefix = str(current_mapping_slot)
    
    spinboxes = p_controller_group.findChildren(QSpinBox)
    checkboxes = p_controller_group.findChildren(QCheckBox)
    
    spinboxes[0].setValue(settings.get(f"controller index {p_num}", 0))

    spinboxes[1].setValue(settings.get(f"gyro{p_num} index x", 0))
    spinboxes[2].setValue(settings.get(f"gyro{p_num} index y", 1))
    spinboxes[3].setValue(settings.get(f"gyro{p_num} index z", 2))

    p_controller_group.findChildren(QDoubleSpinBox)[0].setValue(settings.get(f"gyro{p_num} sensitivity", 1))

    checkboxes[0].setChecked(settings.get(f"joy{p_num} invert x", False))
    checkboxes[1].setChecked(settings.get(f"joy{p_num} invert y", False))

    checkboxes[2].setChecked(settings.get(f"gyro{p_num} invert x", False))
    checkboxes[3].setChecked(settings.get(f"gyro{p_num} invert y", False))
    checkboxes[4].setChecked(settings.get(f"gyro{p_num} invert z", False))



    for i, (label, setting_key) in enumerate(button_config):
        full_key = f"{prefix}{setting_key}"
        val = settings.get(full_key, "none")
        

        if i < len(combos):
            combo_widget = combos[i].findChild(QComboBox)
            if combo_widget:
                combo_widget.blockSignals(True)
                combo_widget.setCurrentText(val)
                combo_widget.blockSignals(False)

def set_mapping_slot(new_slot):
    global current_mapping_slot
    current_mapping_slot = new_slot
    refresh_ui_values()

mapping_label = create_group_horizontal([{
        "type" : "label",
        "text" : "press something!", 
        "alignment" : Qt.AlignmentFlag.AlignRight
},{
        "type" : "spinbox", 
        "text" :"Editing Mapping For:", 
        "min": 1, "max": 2, "default": 1, "steps" : 1,
        "func" : lambda: set_mapping_slot(mapping_label.findChildren(QSpinBox)[0].value() - 1)
}])
layout_controllers.addWidget(mapping_label)

p_controller_group = create_group_horizontal([
    {
        "type" : "spinbox", "text" :"Hardware index", "min":0, "max":999999999, "steps":1,"default":0,
        "func" : lambda: settings_core.update_setting(f"controller index {current_mapping_slot+1}", p_controller_group.findChildren(QSpinBox)[0].value())
    },
    {
        "type" : "label",
        "text" : "joystick:", 
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {"type" : "checkbox", "text" :"invert X","default":settings_core.get_settings()[f"joy{current_mapping_slot+1} invert x"], "func" : lambda: settings_core.update_setting(f"joy{current_mapping_slot+1} invert x", p_controller_group.findChildren(QCheckBox)[0].isChecked())},
    {"type" : "checkbox", "text" :"invert Y","default":settings_core.get_settings()[f"joy{current_mapping_slot+1} invert y"], "func" : lambda: settings_core.update_setting(f"joy{current_mapping_slot+1} invert y", p_controller_group.findChildren(QCheckBox)[1].isChecked())},
    {
        "type" : "label",
        "text" : "gyro:", 
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "button", "text" :"calibrate","enabled" : True,
        "func" : lambda: start_calibration(current_mapping_slot + 1)
    },

    {"type" : "checkbox", "text" :"invert X","default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} invert x"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} invert x", p_controller_group.findChildren(QCheckBox)[2].isChecked())},
    {"type" : "checkbox", "text" :"invert Y","default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} invert y"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} invert y", p_controller_group.findChildren(QCheckBox)[3].isChecked())},
    {"type" : "checkbox", "text" :"invert Z","default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} invert z"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} invert z", p_controller_group.findChildren(QCheckBox)[4].isChecked())},

    {"type" : "spinbox", "text" :"sensor X", "min":0, "max":2,"default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} index x"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} index x", p_controller_group.findChildren(QSpinBox)[1].value())},
    {"type" : "spinbox", "text" :"sensor Y", "min":0, "max":2,"default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} index y"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} index y", p_controller_group.findChildren(QSpinBox)[2].value())},
    {"type" : "spinbox", "text" :"sensor Z", "min":0, "max":2,"default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} index z"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} index z", p_controller_group.findChildren(QSpinBox)[3].value())},
    
    {"type" : "doublespinbox", "text" :"sensitivity", "min":-999999999, "max":999999999,"default":settings_core.get_settings()[f"gyro{current_mapping_slot+1} sensitivity"], "func" : lambda: settings_core.update_setting(f"gyro{current_mapping_slot+1} sensitivity", p_controller_group.findChildren(QDoubleSpinBox)[0].value())},
])
layout_controllers.addWidget(p_controller_group)

combos = []
for i, (label, setting_key) in enumerate(button_config):
    if i % buttons_per_row == 0:
        tab_mapping = QWidget()
        layout_mapping = QHBoxLayout(tab_mapping)
        layout_controllers.addWidget(tab_mapping)
    
    combo = create_combobox({
        "text": label,
        "items": combo_inputs,
        "func": lambda sk=setting_key, c_idx=i: settings_core.update_setting(
            f"{current_mapping_slot}{sk}", 
            combos[c_idx].findChild(QComboBox).currentText()
        )
    })
    combos.append(combo)
    layout_mapping.addWidget(combo)

refresh_ui_values()













#//////////////////////////////////////////////////////////
label5 = create_label({
    "text" : "---------Hand Tracking(experimental, restart to take effect)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(label5)

webcam = create_group_horizontal([
    {
        "type" : "checkbox", 
        "text" : "enable, also forward webcam data to open gloves via named pipe(finger, splay, button mapping)",
        "default" : settings_core.get_settings()['opengloves'], 
        "func" : lambda: start_stop_opengloves()
    },
    {
        "type" : "spinbox", 
        "text" :"camera index", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['camera index'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("camera index", webcam.findChildren(QSpinBox)[0].value())
    },
])
layout_controllers.addWidget(webcam)

def start_stop_opengloves():
    enabled = webcam.findChild(QCheckBox).isChecked()
    settings_core.update_setting("opengloves", enabled)

    if enabled:
        start_opengloves()
    else:
        pass

layout_controllers.addWidget(create_label({
    "text" : "---------Right offsets---------",
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cr_offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world x", cr_offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world y", cr_offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world z", cr_offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world yaw", cr_offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world pitch", cr_offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset world roll", cr_offsets_world.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_controllers.addWidget(cr_offsets_world)

cr_offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local x", cr_offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local y", cr_offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local z", cr_offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local yaw", cr_offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local pitch", cr_offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset local roll", cr_offsets_local.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_controllers.addWidget(cr_offsets_local)

layout_controllers.addWidget(create_label({
    "text" : "---------Left offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cl_offsets_world = create_group_horizontal([
    {
        "type" : "label",
        "text":"world",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world x", cl_offsets_world.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world y", cl_offsets_world.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world z", cl_offsets_world.findChildren(QDoubleSpinBox)[2].value())
    },    
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world yaw", cl_offsets_world.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world pitch", cl_offsets_world.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset world roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset world roll", cl_offsets_world.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_controllers.addWidget(cl_offsets_world)

cl_offsets_local = create_group_horizontal([
    {
        "type" : "label",
        "text":"local",
        "alignment" : Qt.AlignmentFlag.AlignCenter
    },
    {
        "type" : "doublespinbox",
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local x", cl_offsets_local.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local y", cl_offsets_local.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local z", cl_offsets_local.findChildren(QDoubleSpinBox)[2].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local yaw", cl_offsets_local.findChildren(QDoubleSpinBox)[3].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local pitch", cl_offsets_local.findChildren(QDoubleSpinBox)[4].value())
    },
    {
        "type" : "doublespinbox",
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset local roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset local roll", cl_offsets_local.findChildren(QDoubleSpinBox)[5].value())
    }
])
layout_controllers.addWidget(cl_offsets_local)
#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_trackers = QWidget()
layout_trackers = QVBoxLayout(tab_trackers)
layout_trackers.setSpacing(0)


def trackerpos_specific_widget(index, layout, combo):
    settings_core.update_setting(f'{index}trackerpos mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            tracker_redirect_group = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index",
                    "min":0,
                    "max":999999999, 
                    "default": settings.get(f'{index}trackerpos index', 0),
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting(f'{index}trackerpos index', tracker_redirect_group.findChildren(QSpinBox)[0].value())
                }
                ])
            layout.addWidget(tracker_redirect_group)

        case "hip emulation":

            t = create_group_spinbox([{
                "text" : "hmd index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker hmd index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker hmd index', t.findChildren(QSpinBox)[0].value())
            },{
                "text" : "left foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker left foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker left foot index', t.findChildren(QSpinBox)[1].value())
            },{
                "text" : "right foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker right foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker right foot index', t.findChildren(QSpinBox)[2].value())
            }])
            layout.addWidget(t)

def trackerrot_specific_widget(index, layout, combo):
    settings_core.update_setting(f'{index}trackerrot mode', combo.currentText()) 

    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget:
            widget.deleteLater()

    mode = combo.currentText()
    settings = settings_core.get_settings()

    match mode:
        case "redirect":
            tracker_redirect_group = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"Redirect Index",
                    "min":0,
                    "max":999999999, 
                    "default": settings.get(f'{index}trackerrot index', 0),
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting(f'{index}trackerrot index', tracker_redirect_group.findChildren(QSpinBox)[0].value())
                }
                ])
            layout.addWidget(tracker_redirect_group)

        case "hip emulation":

            t = create_group_spinbox([{
                "text" : "hmd index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker hmd index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker hmd index', t.findChildren(QSpinBox)[0].value())
            },{
                "text" : "left foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker left foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker left foot index', t.findChildren(QSpinBox)[1].value())
            },{
                "text" : "right foot index",
                "min": 0,
                "max": 999999,
                "steps" : 1,
                "default": settings.get(f'{index}tracker right foot index', 0),
                "func": lambda: settings_core.update_setting(f'{index}tracker right foot index', t.findChildren(QSpinBox)[2].value())
            }])
            layout.addWidget(t)

        case "gyro":
            t = create_group_horizontal([{
                    "type" : "spinbox", 
                    "text" :"controller index", 
                    "min":0, 
                    "max":999999999, 
                    "default": settings.get(f'{index}tracker gyro index',0), 
                    "steps" : 1,
                    "func"  : lambda: settings_core.update_setting(f'{index}tracker gyro index', t.findChildren(QSpinBox)[0].value())
                }])
            layout.addWidget(t)

def create_tracker_widget(index = 0):
    settings = settings_core.get_settings()

    widget_group = QWidget()
    layout_group = QVBoxLayout(widget_group)

    t = create_label({"text" : f"---index {index}---",
                    "alignment" : Qt.AlignmentFlag.AlignCenter
    })
    layout_group.addWidget(t)

    tab_extrapos = QWidget()
    layout_extrapos = QHBoxLayout(tab_extrapos)
    combopos_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} position mode',
            "default": settings.get(f'{index}trackerpos mode', "redirect"),
            "items": ["redirect"],# "hip emulation"], add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: trackerpos_specific_widget(index, layout_extrapos, combopos_extra.findChild(QComboBox))#lambda: settings_core.update_setting(f'{index}tracker mode', combo_extra.findChild(QComboBox).currentText())
        })
    layout_extrapos.addWidget(combopos_extra)
    trackerpos_specific_widget(index, layout_extrapos, combopos_extra.findChild(QComboBox))
    layout_group.addWidget(tab_extrapos)

    tab_extrarot = QWidget()
    layout_extrarot = QHBoxLayout(tab_extrarot)
    comborot_extra = create_combobox({
            "type" : "combobox",
            "text": f'{index} rotation mode',
            "default": settings.get(f'{index}trackerrot mode', "redirect"),
            "items": ["redirect", "gyro"],# "hip emulation"], add later////////////////////////////////////////////////////////////////////////////////////////
            "func": lambda: trackerrot_specific_widget(index, layout_extrarot, comborot_extra.findChild(QComboBox))#lambda: settings_core.update_setting(f'{index}tracker mode', combo_extra.findChild(QComboBox).currentText())
        })
    layout_extrarot.addWidget(comborot_extra)
    trackerrot_specific_widget(index, layout_extrarot, comborot_extra.findChild(QComboBox))
    layout_group.addWidget(tab_extrarot)

    tracker_offsets_world = create_group_horizontal([
        {
            "type" : "label",
            "text":"world",
            "alignment" : Qt.AlignmentFlag.AlignCenter
        },
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world x', 0.0),
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world x', tracker_offsets_world.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world y', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world y', tracker_offsets_world.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world z', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world z', tracker_offsets_world.findChildren(QDoubleSpinBox)[2].value())
        },    
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world yaw', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world yaw', tracker_offsets_world.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world pitch', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world pitch', tracker_offsets_world.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset world roll', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset world roll', tracker_offsets_world.findChildren(QDoubleSpinBox)[5].value())
        }
    ])
    layout_group.addWidget(tracker_offsets_world)

    tracker_offsets_local = create_group_horizontal([
        {
            "type" : "label",
            "text":"local",
            "alignment" : Qt.AlignmentFlag.AlignCenter
        },
        {
            "type" : "doublespinbox",
            "text" : "X", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local x', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local x', tracker_offsets_local.findChildren(QDoubleSpinBox)[0].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Y", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local y', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local y', tracker_offsets_local.findChildren(QDoubleSpinBox)[1].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Z", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local z', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local z', tracker_offsets_local.findChildren(QDoubleSpinBox)[2].value())
        },    
        {
            "type" : "doublespinbox",
            "text" : "Yaw", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local yaw', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local yaw', tracker_offsets_local.findChildren(QDoubleSpinBox)[3].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Pitch", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local pitch', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local pitch', tracker_offsets_local.findChildren(QDoubleSpinBox)[4].value())
        },
        {
            "type" : "doublespinbox",
            "text" : "Roll", 
            "min":-999999999, 
            "max":999999999, 
            "default": settings.get(f'{index}tracker offset local roll', 0.0), 
            "steps" : 0.01,
            "func"  : lambda: settings_core.update_setting(f'{index}tracker offset local roll', tracker_offsets_local.findChildren(QDoubleSpinBox)[5].value())
        }
    ])
    layout_group.addWidget(tracker_offsets_local)
    return widget_group

tab_devices = QWidget()
layout_devices = QVBoxLayout(tab_devices)

devices_arr = []

def create_trackers_display():
    settings_core.update_setting("trackers num", tracker_num.findChild(QSpinBox).value())
    settings = settings_core.get_settings()

    devices_arr.clear()
    if settings['trackers num'] == 0:
        clear_layout(layout_devices)
    else:
        for n in range(settings['trackers num']):
            devices_arr.append(create_tracker_widget(n))

        clear_layout(layout_devices)
        for n in devices_arr:
            layout_devices.addWidget(n)

# layout_trackers.addWidget(create_label({"text" : "---------aaa---------",
#                                         "alignment" : Qt.AlignmentFlag.AlignCenter
# }))

tracker_num = create_spinbox({
        "text" : "tracker number", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['trackers num'], 
        "steps" : 1,
        "func"  : lambda: create_trackers_display()
    })
create_trackers_display()

layout_trackers.addWidget(tracker_num)
layout_trackers.addWidget(tab_devices)
#trackers/////////////////////////////////////////////////////////////////////////////////////////////////////////////

#////////////////////////////////////////////////////
group_widget = QWidget()
group_layout = QVBoxLayout(group_widget)

group_layout.addWidget(first_label)

tracker_title_label1 = create_label({
    "text" : "---------Trackers---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
group_layout.addWidget(tracker_title_label1)

trackers_label1 = create_label({
    "text" : "0 found", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
group_layout.addWidget(trackers_label1)

#////////////////////////////////////////////////////

tabs.addTab(tab_main, "Hmd")
tabs.addTab(tab_controllers, "Controllers")
tabs.addTab(tab_trackers, "Trackers")
tabs.addTab(tab_driver, "Driver")
tabs.addTab(tab_credits, "Credits")

window_layout.addWidget(tabs)
window_layout.addWidget(group_widget)
window.show()
app.exec()