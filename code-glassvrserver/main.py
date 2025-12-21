#pyinstaller --noconfirm --windowed --collect-binaries "sdl2dll" --collect-all "sdl2" --collect-binaries "openvr" --collect-all "mediapipe" --collect-all "cv2" --hidden-import "sdl2dll" main.py
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QGridLayout, QCheckBox, QComboBox

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

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

import win32file
import win32api
from typing import List, Dict, Any, Tuple
import cv2
import mediapipe as mp
import time
from sdl2 import *
from sdl2.ext import Resources
import traceback

import ctypes
import keyboard
import webbrowser
import platform
import requests

import settings_core

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('sdl2dll')

app = QApplication([])#sys.argv)

window = QTabWidget()
#window.setWindowTitle("PuffinVR")
window.setWindowTitle("GlassVR")
window.resize(1150, 1100)

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
                case "combobox":
                    group_layout.addWidget(create_combobox(dict))
        return group_widget
    
def create_image(dict = {}):
    image_label = QLabel()
    image = QPixmap("D:/UltimateFolder0/Gallery-Y/projects/GlassVr/code-glassvrserver/fix.png")
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
#core/////////////////////////////////////////////////////////////////////////////////////////////////////////////

# main/////////////////////////////////////////////////////////////////////////////////////////////////////////////
tab_main = QWidget()
layout_main = QVBoxLayout(tab_main)

first_label = create_label({
    "text" : "steamvr is not running :(", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
# layout_main.addWidget(first_label)

check_box_hmd = create_checkbox(
    {
        "text" : "enable hmd", 
        "default" : settings_core.get_settings()['enable hmd'], 
        "func" : lambda: settings_core.update_setting("enable hmd",check_box_hmd.findChild(QCheckBox).isChecked())
    })
layout_main.addWidget(check_box_hmd)

tracker_title_label1 = create_label({
    "text" : "---------Trackers---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(tracker_title_label1)

trackers_label1 = create_label({
    "text" : "0 found", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(trackers_label1)

label3 = create_label({
    "text" : "hmd index", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(label3)

spinbox_hmd_index = QSpinBox()
spinbox_hmd_index.setRange(0, 999999999)
spinbox_hmd_index.setValue(settings_core.get_settings()['hmd index'])
spinbox_hmd_index.setSingleStep(1)
spinbox_hmd_index.valueChanged.connect(lambda: settings_core.update_setting("hmd index", spinbox_hmd_index.value()))

layout_main.addWidget(spinbox_hmd_index)

trackers_arr = []

def is_prosses_running(PROCESS_NAME):
    for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == PROCESS_NAME.lower():
                return True
    
    return False

def check_hardware_key_exists(hardware_name):
    """
    Returns True if 'hardware_name' (e.g., '1') is assigned 
    as an ACTION to any hardware key in the settings.
    """
    settings = settings_core.get_settings()
    
    # .values() gives us the action names (what the hardware is mapped TO)
    return hardware_name in settings.values()

send_dict = {"hmd pos x" : 0.0,"hmd pos y" : 0.0,"hmd pos z" : 0.0,
             "hmd rot x" : 0.0,"hmd rot y" : 0.0,"hmd rot z" : 0.0,"hmd rot w" : 0.0,
             "ipd" : 0.0, "head to eye dist" : 0.0,

             "cr pos x" : 0.0,"cr pos y" : 0.0,"cr pos z" : 0.0,
             "cr rot x" : 0.0,"cr rot y" : 0.0,"cr rot z" : 0.0,"cr rot w" : 0.0,
             "cr joy x" : 0.0, "cr joy y" : 0.0, "cr joy" : False,
             "cr touch x" : 0.0, "cr touch y" : 0.0, "cr touch" : False,
             "cr a" : False, "cr b" : False,
             "cr trigger" : 0.0, "cr grip" : False, "cr menu" : False,
             
             "cl pos x" : 0.0,"cl pos y" : 0.0,"cl pos z" : 0.0,
             "cl rot x" : 0.0,"cl rot y" : 0.0,"cl rot z" : 0.0,"cl rot w" : 0.0,
             "cl joy x" : 0.0, "cl joy y" : 0.0, "cl joy" : False,
             "cl touch x" : 0.0, "cl touch y" : 0.0, "cl touch" : False,
             "cl a" : False, "cl b" : False,
             "cl trigger" : 0.0, "cl grip" : False, "cl menu" : False,
             }

def get_final_transform(device = "hmd"):
    settings = settings_core.get_settings()
    try:
        tracker = trackers_arr[settings_core.get_settings()[f'{device} index']]
        
        pos_x = tracker['pos x'] + settings[f'{device} offset x']
        pos_y = tracker['pos y'] + settings[f'{device} offset y']
        pos_z = tracker['pos z'] + settings[f'{device} offset z']
        
        device_rotation = R.from_matrix(tracker['rotation matrix'])

        offset_angles_rad = [
            settings_core.get_settings()[f'{device} offset roll'],
            settings_core.get_settings()[f'{device} offset yaw'],
            settings_core.get_settings()[f'{device} offset pitch']
        ]
        
        offset_rotation = R.from_euler('ZYX', offset_angles_rad, degrees=False)

        final_rotation = device_rotation * offset_rotation

        quat_final = final_rotation.as_quat()

        rot_x = quat_final[0]
        rot_y = quat_final[1]
        rot_z = quat_final[2]
        rot_w = quat_final[3]
        
        return({"pos x" : pos_x,
                "pos y" : pos_y,
                "pos z" : pos_z,
                
                "rot x" : rot_x,
                "rot y" : rot_y,
                "rot z" : rot_z,
                "rot w" : rot_w
                })
    except:
        try:
            return({"pos x" : settings[f'{device} offset x'],
                    "pos y" : settings[f'{device} offset y'],
                    "pos z" : settings[f'{device} offset z'],
                    
                    "rot x" : 0.0,
                    "rot y" : 0.0,
                    "rot z" : 0.0,
                    "rot w" : 0.0
                    })
        except:
            return({"pos x" : 0.0,
                "pos y" : 0.0,
                "pos z" : 0.0,
                
                "rot x" : 0.0,
                "rot y" : 0.0,
                "rot z" : 0.0,
                "rot w" : 0.0
                })

PACK_FORMAT = '<9d24f12?'
PACKET_SIZE = struct.calcsize(PACK_FORMAT)

def send_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            settings = settings_core.get_settings()
            #hmd////////////////////////////////////////////////////////////////////////////////////////
            hmd_final_transform = get_final_transform("hmd")
            
            hmd_pos_x = hmd_final_transform['pos x']
            hmd_pos_y = hmd_final_transform['pos y']
            hmd_pos_z = hmd_final_transform['pos z']
            
            hmd_rot_x = hmd_final_transform['rot x']
            hmd_rot_y = hmd_final_transform['rot y']
            hmd_rot_z = hmd_final_transform['rot z']
            hmd_rot_w = hmd_final_transform['rot w']
            
            hmd_ipd = settings['ipd']
            hmd_head_to_eye_dist = settings['head to eye dist']
            #hmd////////////////////////////////////////////////////////////////////////////////////////
            
            #right////////////////////////////////////////////////////////////////////////////////////////
            cr_final_transform = get_final_transform("cr")

            cr_pos_x = cr_final_transform['pos x']
            cr_pos_y = cr_final_transform['pos y']
            cr_pos_z = cr_final_transform['pos z']
            
            cr_rot_x = cr_final_transform['rot x']
            cr_rot_y = cr_final_transform['rot y']
            cr_rot_z = cr_final_transform['rot z']
            cr_rot_w = cr_final_transform['rot w']


            #mod = 0.1
            # cr_pos_x = hand_data['r pos x']
            # cr_pos_y = hand_data['r pos y']
            # cr_pos_z = hand_data['r pos z'] * mod
            
            # cr_rot_x = hand_data['r rot x']
            # cr_rot_y = hand_data['r rot y']
            # cr_rot_z = hand_data['r rot z']
            # cr_rot_w = hand_data['r rot w']

            # mod = 0.01
            # z_mod = 0.01
            # final = raw_to_local_transform(hand_data['r pos x'] * mod, hand_data['r pos y'] * mod, hand_data['r pos z'] * z_mod,
            #                hand_data['r rot x'], hand_data['r rot y'], hand_data['r rot z'], hand_data['r rot w'],
            #                hmd_pos_x, hmd_pos_y, hmd_pos_z,
            #                hmd_rot_x, hmd_rot_y, hmd_rot_z, hmd_rot_w)
            
            # cr_pos_x = final['pos_x'] + settings['cr offset x']
            # cr_pos_y = final['pos_y'] + settings['cr offset y']
            # cr_pos_z = final['pos_z'] + settings['cr offset z']
            
            # cr_rot_x = final['rot_x']
            # cr_rot_y = final['rot_y']
            # cr_rot_z = final['rot_z']
            # cr_rot_w = final['rot_w']
            # print("x=" + str(cr_pos_x) + " y=" + str(cr_pos_y) + " z=" + str(cr_pos_z))

            cr_trigger = get_mapped_action('right trigger')
            cr_touch = get_mapped_action('right touch button')
            cr_a = get_mapped_action('right a')
            cr_b = get_mapped_action('right b')
            cr_grip = get_mapped_action('right grip')
            cr_menu = get_mapped_action('right menu')

            if check_hardware_key_exists('right touch modifier'):
                if get_mapped_action('right touch modifier'):
                    cr_joy_x = 0.0
                    cr_joy_y = 0.0
                    cr_touch_x = get_mapped_action('right joy x')
                    cr_touch_y = -get_mapped_action('right joy y')

                    cr_touch = get_mapped_action('right joy button')
                else:
                    cr_joy_x = get_mapped_action('right joy x')
                    cr_joy_y = -get_mapped_action('right joy y')
                    cr_touch_x = 0.0
                    cr_touch_y = 0.0

                    cr_joy = get_mapped_action('right joy button')
            else:
                cr_joy_x = get_mapped_action('right joy x')
                cr_joy_y = -get_mapped_action('right joy y')

                cr_touch_x = get_mapped_action('right touch x')
                cr_touch_y = -get_mapped_action('right touch y')

            #right////////////////////////////////////////////////////////////////////////////////////////
            #left////////////////////////////////////////////////////////////////////////////////////////
            cl_final_transform = get_final_transform("cl")
            
            cl_pos_x = cl_final_transform['pos x']
            cl_pos_y = cl_final_transform['pos y']
            cl_pos_z = cl_final_transform['pos z']

            cl_rot_x = cl_final_transform['rot x']
            cl_rot_y = cl_final_transform['rot y']
            cl_rot_z = cl_final_transform['rot z']
            cl_rot_w = cl_final_transform['rot w']

            cl_trigger = get_mapped_action('left trigger')
            cl_touch = get_mapped_action('left touch button')
            cl_a = get_mapped_action('left a')
            cl_b = get_mapped_action('left b')
            cl_grip = get_mapped_action('left grip')
            cl_menu = get_mapped_action('left menu')

            if check_hardware_key_exists('left touch modifier'):
                if get_mapped_action('left touch modifier'):
                    cl_joy_x = 0.0
                    cl_joy_y = 0.0
                    cl_touch_x = get_mapped_action('left joy x')
                    cl_touch_y = -get_mapped_action('left joy y')

                    cl_touch = get_mapped_action('left joy button')

                else:
                    cl_joy_x = get_mapped_action('left joy x')
                    cl_joy_y = -get_mapped_action('left joy y')
                    cl_touch_x = 0.0
                    cl_touch_y = 0.0

                    cl_joy = get_mapped_action('left joy button')
            else:
                cl_joy_x = get_mapped_action('left joy x')
                cl_joy_y = -get_mapped_action('left joy y')

                cl_touch_x = get_mapped_action('left touch x')
                cl_touch_y = -get_mapped_action('left touch y')
            #left////////////////////////////////////////////////////////////////////////////////////////

            buffer = struct.pack(
            PACK_FORMAT, 

            hmd_pos_x, hmd_pos_y, hmd_pos_z, 
            hmd_rot_w, hmd_rot_x, hmd_rot_y, hmd_rot_z,
            hmd_ipd, hmd_head_to_eye_dist,
            
            cr_pos_x, cr_pos_y, cr_pos_z, cr_rot_x, cr_rot_y, cr_rot_z, cr_rot_w,
            cr_joy_x, cr_joy_y, cr_touch_x, cr_touch_y,
            cr_trigger,

            cl_pos_x, cl_pos_y, cl_pos_z, cl_rot_x, cl_rot_y, cl_rot_z, cl_rot_w,
            cl_joy_x, cl_joy_y, cl_touch_x, cl_touch_y,
            cl_trigger,
            
            cr_joy, cr_touch, cr_a, cr_b, cr_grip, cr_menu,
            
            cl_joy, cl_touch, cl_a, cl_b, cl_grip, cl_menu
            )
            
            sock.sendto(buffer, (settings['ip sending'], settings['port receiving']))

            time.sleep(0.0001)
        except Exception as e:
            print(e)
            time.sleep(0.0001)

def start_send_udp():
    t = threading.Thread(target=send_udp, daemon=True)
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

def start_update_vrlabel():
    t = threading.Thread(target=update_vrlabel, daemon=True)
    t.start()
    return t


def start_vr_utility():
    global trackers_arr

    try:
        vr.init(vr.VRApplication_Utility)
        vr_system = vr.VRSystem()

        
        while True:
            try:
                trackers = get_trackers(vr_system)

                # trackers = [{"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},

                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},

                #             {"index" : 2, "class" : "test", "model" : "a", "render" : "vive", "role" : "idk"},
                #             {"index" : 2, "class" : "test", "model" : "a", "render" : "vive", "role" : "idk"},
                #             {"index" : 2, "class" : "test", "model" : "a", "render" : "vive", "role" : "idk"},
                #             {"index" : 2, "class" : "test", "model" : "a", "render" : "vive", "role" : "idk"},
                #             {"index" : 2, "class" : "test", "model" : "a", "render" : "vive", "role" : "idk"},

                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"},
                #             {"index" : 0, "class" : "GENERIC CONTROLLER", "model" : "VIVE TRACKER+++", "render" : "vive", "role" : "OPTOUT"}]

                #print connected
                count = 0
                line = 0
                text = ""
                
                for n in trackers:
                    if line == 5:
                        line = 0
                        text += "\n"

                    text += "[" + str(count) + " "
                    if n['class'] == 2:
                        text += "{controller "
                    if n['class'] == 3:
                        text += "tracker "
                    text += n['model'] + " "
                    text += n['role'] + "] "

                    count += 1

                    line += 1

                trackers_label1.findChild(QLabel).setText(text)
                trackers_label2.findChild(QLabel).setText(text)


                found = "---------" + str(len(trackers)) + " Trackers Found---------"

                tracker_title_label1.findChild(QLabel).setText(found)
                tracker_title_label2.findChild(QLabel).setText(found)

                #print connected

                #keep the first argument as 2, do not change it
                poses = vr_system.getDeviceToAbsoluteTrackingPose(
                    2, 0.0, vr.k_unMaxTrackedDeviceCount
                )

                trackers_transforms = []
                for n in trackers:
                    pose = poses[n['index']]
                    
                    if pose.bDeviceIsConnected and pose.bPoseIsValid:
                        dict = {}

                        m = pose.mDeviceToAbsoluteTracking
                        
                        dict.update({"pos x" : m[0][3]})
                        dict.update({"pos y" : m[1][3]})
                        dict.update({"pos z" : m[2][3]})

                        rotation_matrix = np.array([
                            [m[0][0], m[0][1], m[0][2]],
                            [m[1][0], m[1][1], m[1][2]],
                            [m[2][0], m[2][1], m[2][2]]
                        ])
                        dict.update({"rotation matrix" : rotation_matrix})
                        
                        trackers_transforms.append(dict)
                        
                trackers_arr = trackers_transforms
                time.sleep(0.0001)
            except:
                time.sleep(1)
                start_vr_utility()

    except:
        time.sleep(1)
        start_vr_utility()

def end_vr_utility():
    vr.shutdown()

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
                
                role_hint = "unknown"

                match vr_system.getControllerRoleForTrackedDeviceIndex(i):
                    case vr.TrackedControllerRole_Invalid:
                        role_hint = "Unknown"
                    case vr.TrackedControllerRole_LeftHand:
                        role_hint = "Left Hand"
                    case vr.TrackedControllerRole_RightHand:
                        role_hint = "Right Hand"
                    case vr.TrackedControllerRole_OptOut:
                        role_hint = "OptOut"
                    case vr.TrackedControllerRole_Treadmill:
                        role_hint = "Treadmill"
                    case vr.TrackedControllerRole_Stylus:
                        role_hint = "Stylus"
                    case vr.TrackedControllerRole_Max:
                        role_hint = "Max"

                # if 'right' in render_model_name.lower():
                #     role_hint = "right"
                # elif 'left' in render_model_name.lower():
                #     role_hint = "left"
                # else:
                #     role_enum = vr_system.getControllerRoleForTrackedDeviceIndex(i)
                #     if role_enum == vr.TrackedControllerRole_LeftHand:
                #         role_hint = "left"
                #     elif role_enum == vr.TrackedControllerRole_RightHand:
                #         role_hint = "right"
                #     elif role_enum == vr.TrackedControllerRole_OptOut:
                #         role_hint = "OptOut"
                #     elif role_enum == vr.TrackedControllerRole_Treadmill:
                #         role_hint = "treadmill"
# TrackedControllerRole_Invalid = ENUM_VALUE_TYPE(0)
# TrackedControllerRole_LeftHand = ENUM_VALUE_TYPE(1)
# TrackedControllerRole_RightHand = ENUM_VALUE_TYPE(2)
# TrackedControllerRole_OptOut = ENUM_VALUE_TYPE(3)
# TrackedControllerRole_Treadmill = ENUM_VALUE_TYPE(4)
# TrackedControllerRole_Stylus = ENUM_VALUE_TYPE(5)
# TrackedControllerRole_Max = ENUM_VALUE_TYPE(5)

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

SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER)

#controller_input_method = "controller"
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
        "lefttrigger": 0.0, "righttrigger": 0.0
    }

controller_1_dict = get_default_state()
controller_2_dict = get_default_state()

def get_mapped_action(action_name):
    settings = settings_core.get_settings()

    hardware_keys = []
    for hw_key, assigned_action in settings.items():
        if assigned_action == action_name:
            hardware_keys.append(hw_key)
    
    if not hardware_keys:
        if any(word in action_name for word in ['x', 'y', 'trigger']):
            return 0.0
        return False
    
    analog_values = []
    digital_values = []
    
    for hardware_key in hardware_keys:
        if hardware_key not in controller_1_dict:
            continue
            
        val1 = controller_1_dict[hardware_key]
        val2 = controller_2_dict[hardware_key]
        
        if isinstance(val1, float):
            analog_values.append(val1)
            analog_values.append(val2)
        else:
            digital_values.append(val1)
            digital_values.append(val2)
    
    if analog_values:
        return max(analog_values, key=abs)
    
    return any(digital_values)

def update_controller_mapping():
    global controller_1_dict, controller_2_dict, controller_arr
    
    while True:
        try:
            event = SDL_Event()
            while SDL_PollEvent(event):
                if event.type == SDL_CONTROLLERDEVICEADDED:
                    new_controller = SDL_GameControllerOpen(event.cdevice.which)
                    if new_controller:
                        controller_arr.append(new_controller)
                        print(f"Controller Added: {SDL_GameControllerName(new_controller).decode('utf-8')}")
                elif event.type == SDL_CONTROLLERDEVICEREMOVED:
                    instance_id = event.cdevice.which
                    for c in controller_arr:
                        if SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(c)) == instance_id:
                            SDL_GameControllerClose(c)
                            controller_arr.remove(c)
                            print("Controller Removed.")
                            break

            settings = settings_core.get_settings()
            idx1 = settings.get("controller index 1", 0)
            idx2 = settings.get("controller index 2", 1)

            if 0 <= idx1 < len(controller_arr):
                c1 = controller_arr[idx1]
                def b1(btn): return bool(SDL_GameControllerGetButton(c1, btn))
                def a1(ax):
                    v = SDL_GameControllerGetAxis(c1, ax) / 32767.0
                    if abs(v) < DEADZONE: return 0.0
                    return (v - (DEADZONE if v > 0 else -DEADZONE)) / (1.0 - DEADZONE)

                controller_1_dict.update({
                    "a": b1(SDL_CONTROLLER_BUTTON_A), "b": b1(SDL_CONTROLLER_BUTTON_B),
                    "x": b1(SDL_CONTROLLER_BUTTON_X), "y": b1(SDL_CONTROLLER_BUTTON_Y),
                    "back": b1(SDL_CONTROLLER_BUTTON_BACK), "start": b1(SDL_CONTROLLER_BUTTON_START),
                    "guide": b1(SDL_CONTROLLER_BUTTON_GUIDE), "misc1": b1(SDL_CONTROLLER_BUTTON_MISC1),
                    "leftshoulder": b1(SDL_CONTROLLER_BUTTON_LEFTSHOULDER), "rightshoulder": b1(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER),
                    "leftstick": b1(SDL_CONTROLLER_BUTTON_LEFTSTICK), "rightstick": b1(SDL_CONTROLLER_BUTTON_RIGHTSTICK),
                    "dpup": b1(SDL_CONTROLLER_BUTTON_DPAD_UP), "dpdown": b1(SDL_CONTROLLER_BUTTON_DPAD_DOWN),
                    "dpleft": b1(SDL_CONTROLLER_BUTTON_DPAD_LEFT), "dpright": b1(SDL_CONTROLLER_BUTTON_DPAD_RIGHT),
                    "paddle1": b1(SDL_CONTROLLER_BUTTON_PADDLE1), "paddle2": b1(SDL_CONTROLLER_BUTTON_PADDLE2),
                    "paddle3": b1(SDL_CONTROLLER_BUTTON_PADDLE3), "paddle4": b1(SDL_CONTROLLER_BUTTON_PADDLE4),
                    "touchpad": b1(SDL_CONTROLLER_BUTTON_TOUCHPAD),
                    "leftx": a1(SDL_CONTROLLER_AXIS_LEFTX), "lefty": a1(SDL_CONTROLLER_AXIS_LEFTY),
                    "rightx": a1(SDL_CONTROLLER_AXIS_RIGHTX), "righty": a1(SDL_CONTROLLER_AXIS_RIGHTY),
                    "lefttrigger": a1(SDL_CONTROLLER_AXIS_TRIGGERLEFT), "righttrigger": a1(SDL_CONTROLLER_AXIS_TRIGGERRIGHT),
                })
            else:
                controller_1_dict.update(get_default_state())

            if 0 <= idx2 < len(controller_arr):
                c2 = controller_arr[idx2]
                def b2(btn): return bool(SDL_GameControllerGetButton(c2, btn))
                def a2(ax):
                    v = SDL_GameControllerGetAxis(c2, ax) / 32767.0
                    if abs(v) < DEADZONE: return 0.0
                    return (v - (DEADZONE if v > 0 else -DEADZONE)) / (1.0 - DEADZONE)

                controller_2_dict.update({
                    "a": b2(SDL_CONTROLLER_BUTTON_A), "b": b2(SDL_CONTROLLER_BUTTON_B),
                    "x": b2(SDL_CONTROLLER_BUTTON_X), "y": b2(SDL_CONTROLLER_BUTTON_Y),
                    "back": b2(SDL_CONTROLLER_BUTTON_BACK), "start": b2(SDL_CONTROLLER_BUTTON_START),
                    "guide": b2(SDL_CONTROLLER_BUTTON_GUIDE), "misc1": b2(SDL_CONTROLLER_BUTTON_MISC1),
                    "leftshoulder": b2(SDL_CONTROLLER_BUTTON_LEFTSHOULDER), "rightshoulder": b2(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER),
                    "leftstick": b2(SDL_CONTROLLER_BUTTON_LEFTSTICK), "rightstick": b2(SDL_CONTROLLER_BUTTON_RIGHTSTICK),
                    "dpup": b2(SDL_CONTROLLER_BUTTON_DPAD_UP), "dpdown": b2(SDL_CONTROLLER_BUTTON_DPAD_DOWN),
                    "dpleft": b2(SDL_CONTROLLER_BUTTON_DPAD_LEFT), "dpright": b2(SDL_CONTROLLER_BUTTON_DPAD_RIGHT),
                    "paddle1": b2(SDL_CONTROLLER_BUTTON_PADDLE1), "paddle2": b2(SDL_CONTROLLER_BUTTON_PADDLE2),
                    "paddle3": b2(SDL_CONTROLLER_BUTTON_PADDLE3), "paddle4": b2(SDL_CONTROLLER_BUTTON_PADDLE4),
                    "touchpad": b2(SDL_CONTROLLER_BUTTON_TOUCHPAD),
                    "leftx": a2(SDL_CONTROLLER_AXIS_LEFTX), "lefty": a2(SDL_CONTROLLER_AXIS_LEFTY),
                    "rightx": a2(SDL_CONTROLLER_AXIS_RIGHTX), "righty": a2(SDL_CONTROLLER_AXIS_RIGHTY),
                    "lefttrigger": a2(SDL_CONTROLLER_AXIS_TRIGGERLEFT), "righttrigger": a2(SDL_CONTROLLER_AXIS_TRIGGERRIGHT),
                })
            else:
                controller_2_dict.update(get_default_state())

            time.sleep(0.0001)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

def start_controller_mapping():
    t = threading.Thread(target=update_controller_mapping, daemon=True)
    t.start()
    return t
#camera//////////////////////////////////////////////////////////////////////////////////////////////////
SHOW_FEED = True
RESOLUTION_X = 500
RESOLUTION_Y = 500
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

def map_to_glove(hand_label, hand_landmarks, hand_prefix):
    global right_hand_smoothed_flexion, left_hand_smoothed_flexion
    global right_hand_smoothed_splay, left_hand_smoothed_splay
    
    is_right = (hand_label.lower() == "right")
    flex_buf = right_hand_smoothed_flexion if is_right else left_hand_smoothed_flexion
    splay_buf = right_hand_smoothed_splay if is_right else left_hand_smoothed_splay
    
    L = {lm['id']: lm for lm in hand_landmarks}
    
    # Flexion Calculation
    for finger_i, mp_ids in enumerate(MP_LANDMARK_IDS):
        for joint_i in range(3):
            p1_id = mp_ids[joint_i-1] if joint_i > 0 else (0 if finger_i == 0 else mp_ids[0]-1)
            p2_id, p3_id = mp_ids[joint_i], mp_ids[joint_i+1]
            angle = get_angle(get_vector(L[p2_id], L[p1_id]), get_vector(L[p2_id], L[p3_id]))
            val = 1.0 - normalize_value(angle, FLEXION_MIN_ANGLE, FLEXION_MAX_ANGLE)
            idx = finger_i * 4 + joint_i
            flex_buf[idx] = (SMOOTHING_FACTOR * val) + ((1 - SMOOTHING_FACTOR) * flex_buf[idx])
        flex_buf[finger_i * 4 + 3] = flex_buf[finger_i * 4 + 2]
    
    # Splay Calculation
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
    for prefix, full_name in [("r", "right"), ("l", "left")]:
        hand_data[f"{prefix} a_button"] = get_mapped_action(f'{full_name} a')
        hand_data[f"{prefix} b_button"] = get_mapped_action(f'{full_name} b')
        hand_data[f"{prefix} grab"] = get_mapped_action(f'{full_name} grip')
        hand_data[f"{prefix} menu"] = get_mapped_action(f'{full_name} menu')
        hand_data[f"{prefix} calibrate"] = get_mapped_action(f'{full_name} touch modifier')
        
        t_val = get_mapped_action(f'{full_name} trigger')
        hand_data[f"{prefix} trigger_value"] = t_val
        hand_data[f"{prefix} trigger_button"] = (t_val == 1.0)
        
        hand_data[f"{prefix} joy_x"] = get_mapped_action(f'{full_name} joy x')
        hand_data[f"{prefix} joy_y"] = -get_mapped_action(f'{full_name} joy y')
        hand_data[f"{prefix} joy_button"] = get_mapped_action(f'{full_name} joy button')

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
            print("Camera initialization timeout")
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
        print(f"Camera loop error: {e}")
        camera_running = False
    
    finally:
        with caps_lock:
            for cap in caps.values():
                cap.release()
            caps.clear()
        cv2.destroyAllWindows()
        if hands:
            hands.close()

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
                print(f"Failed to open camera at index {idx}")
                return False
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_X)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_Y)
            caps[idx] = cap
            return True
        
        except Exception as e:
            print(f"Error creating camera: {e}")
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
                print("Tracking Started Successfully.")
            else:
                camera_running = False
                print("Camera initialization timeout.")
        else:
            print("Failed to initialize camera.")
#camera//////////////////////////////////////////////////////////////////////////////////////////////////
if __name__ == '__main__':
    if settings_core.get_settings()['opengloves']:
        start_opengloves()

    start_controller_mapping()

    start_send_udp()
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

fov_label = create_label({
    "text" : "---------FOV(using Mono)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_main.addWidget(fov_label)

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
position_offsets = create_group_doublespinbox([
    {
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset x", position_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset y", position_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset z", position_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

rotation_offsets = create_group_doublespinbox([
    {
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset yaw", rotation_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset pitch", rotation_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['hmd offset roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("hmd offset roll", rotation_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

layout_main.addWidget(position_offsets)
layout_main.addWidget(rotation_offsets)
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
    #copy driver to steamvr/drivers
    source_folder = 'driver to copy'
    destination_folder = settings_core.get_settings()['drivers path']
    
    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

        # install_buttons.findChildren(QPushButton)[0].setText("installed successfully")
        # time.sleep(3)
        # install_buttons.findChildren(QPushButton)[0].setText("install")

    except Exception as e:
        pass
        # print(e)

    update_install_and_config_label()

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
        pass
        # print(e)

    update_install_and_config_label()

tab_driver = QWidget()
layout_driver = QVBoxLayout(tab_driver)

layout_driver.addWidget(create_label({
    "text" : "---------Driver(everything in this tab requires restarting steamvr to apply)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

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

def update_install_and_config_label():
    install_leb =  install_label.findChild(QLabel)
    config_leb =  config_label.findChild(QLabel)

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
    "text" : "---------Network---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
layout_driver.addWidget(create_label({
    "text" : "sending", 
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
layout_driver.addWidget(network)

layout_driver.addWidget(create_label({
    "text" : "receiving", 
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
    "text" : "---------Config---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))
layout_driver.addWidget(create_button({
        "text" : "reset config(ui won't update, click each time the server updates)", 
        "enabled" : True,
        "func"  : lambda: settings_core.reset_settings()
    }))
config = create_group_horizontal([{
        "type" : "button", 
        "text" : "open config location", 
        "enabled" : True,
        "func"  : lambda: os.startfile(settings_core.get_path().removesuffix("\settings.json"))
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
        return "Could not retrieve public IP"
    
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

def create_credits():
    create_group = QWidget()
    layout_credits1 = QVBoxLayout(create_group)

    label = QLabel("DaniXmir")
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    layout_credits1.addWidget(label)

    image_button = QPushButton()
    image = QPixmap("D:/UltimateFolder0/Gallery-Y/projects/GlassVr/code-glassvrserver/fix.png")
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

    link = '<a href=https://discord.gg/WbEqvHKs> https://discord.gg/WbEqvHKs </a>'
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
#/////////////

tracker_title_label2 = create_label({
    "text" : "---------Trackers---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(tracker_title_label2)

trackers_label2 = create_label({
    "text" : "0 found", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(trackers_label2)

#/////////////
tab_index = QWidget()
layout_index = QHBoxLayout(tab_index)

spinbox_cl_index = QSpinBox()
spinbox_cl_index.setRange(0, 999999999)
spinbox_cl_index.setValue(settings_core.get_settings()['cl index'])
spinbox_cl_index.setSingleStep(1)
spinbox_cl_index.valueChanged.connect(lambda: settings_core.update_setting("cl index", spinbox_cl_index.value()))

layout_index.addWidget(spinbox_cl_index)

label3 = create_label({
    "text" : "<- left (index) right ->", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_index.addWidget(label3)

spinbox_cr_index = QSpinBox()
spinbox_cr_index.setRange(0, 999999999)
spinbox_cr_index.setValue(settings_core.get_settings()['cr index'])
spinbox_cr_index.setSingleStep(1)
spinbox_cr_index.valueChanged.connect(lambda: settings_core.update_setting("cr index", spinbox_cr_index.value()))

layout_index.addWidget(spinbox_cr_index)
layout_controllers.addWidget(tab_index)
#/////////////

label6 = create_label({
    "text" : "---------Mapping---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(label6)

index2 = create_group_horizontal([
    {
        "type" : "spinbox", 
        "text" :"physical controller1", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['controller index 1'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("controller index 1", index2.findChildren(QSpinBox)[0].value())
    },
    {
        "type" : "spinbox", 
        "text" :"physical controller2", 
        "min":0, 
        "max":999999999, 
        "default":settings_core.get_settings()['controller index 2'], 
        "steps" : 1,
        "func"  : lambda: settings_core.update_setting("controller index 2", index2.findChildren(QSpinBox)[1].value())
    },
])
layout_controllers.addWidget(index2)
#//////////////////////////////////////////////////////////

combo_inputs = ["right a","right b","right grip","right menu","right trigger","right joy button","right joy x","right joy y","right touch button","right touch x","right touch y",
                "right touch modifier",
                "left a","left b","left grip","left menu","left trigger","left joy button","left joy x","left joy y","left touch button","left touch x","left touch y",
                "left touch modifier"
                ]

tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)
# --- ROW 1: Triggers & Bumpers ---
tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)
combo1 = create_combobox({
    "text" : "left trigger",
    "default" : settings_core.get_settings().get('lefttrigger', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("lefttrigger", combo1.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo1)

combo2 = create_combobox({
    "text" : "left bumper",
    "default" : settings_core.get_settings().get('leftshoulder', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("leftshoulder", combo2.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo2)

combo3 = create_combobox({
    "text" : "right trigger",
    "default" : settings_core.get_settings().get('righttrigger', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("righttrigger", combo3.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo3)

combo4 = create_combobox({
    "text" : "right bumper",
    "default" : settings_core.get_settings().get('rightshoulder', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("rightshoulder", combo4.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo4)

combo5 = create_combobox({
    "text" : "paddle 2",
    "default" : settings_core.get_settings().get('paddle2', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("paddle2", combo5.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo5)
layout_controllers.addWidget(tab_mapping)

# --- ROW 2: Face Buttons ---
tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)

combo6 = create_combobox({
    "text" : "a",
    "default" : settings_core.get_settings().get('a', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("a", combo6.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo6)

combo7 = create_combobox({
    "text" : "b",
    "default" : settings_core.get_settings().get('b', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("b", combo7.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo7)

combo8 = create_combobox({
    "text" : "x",
    "default" : settings_core.get_settings().get('x', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("x", combo8.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo8)

combo9 = create_combobox({
    "text" : "y",
    "default" : settings_core.get_settings().get('y', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("y", combo9.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo9)

combo10 = create_combobox({
    "text" : "paddle 4",
    "default" : settings_core.get_settings().get('paddle4', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("paddle4", combo10.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo10)
layout_controllers.addWidget(tab_mapping)

# --- ROW 3: D-Pad ---
tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)

combo11 = create_combobox({
    "text" : "d-pad down",
    "default" : settings_core.get_settings().get('dpdown', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("dpdown", combo11.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo11)

combo12 = create_combobox({
    "text" : "d-pad left",
    "default" : settings_core.get_settings().get('dpleft', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("dpleft", combo12.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo12)

combo13 = create_combobox({
    "text" : "d-pad right",
    "default" : settings_core.get_settings().get('dpright', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("dpright", combo13.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo13)

combo14 = create_combobox({
    "text" : "d-pad up",
    "default" : settings_core.get_settings().get('dpup', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("dpup", combo14.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo14)

combo15 = create_combobox({
    "text" : "paddle 1",
    "default" : settings_core.get_settings().get('paddle1', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("paddle1", combo15.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo15)
layout_controllers.addWidget(tab_mapping)

# --- ROW 4: Joysticks ---
tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)

combo16 = create_combobox({
    "text" : "left joy x",
    "default" : settings_core.get_settings().get('leftx', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("leftx", combo16.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo16)

combo17 = create_combobox({
    "text" : "left joy y",
    "default" : settings_core.get_settings().get('lefty', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("lefty", combo17.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo17)

combo18 = create_combobox({
    "text" : "right joy x",
    "default" : settings_core.get_settings().get('rightx', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("rightx", combo18.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo18)

combo19 = create_combobox({
    "text" : "right joy y",
    "default" : settings_core.get_settings().get('righty', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("righty", combo19.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo19)

combo20 = create_combobox({
    "text" : "paddle 3",
    "default" : settings_core.get_settings().get('paddle3', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("paddle3", combo20.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo20)
layout_controllers.addWidget(tab_mapping)

# --- ROW 5: Utility Buttons ---
tab_mapping = QWidget()
layout_mapping = QHBoxLayout(tab_mapping)

combo21 = create_combobox({
    "text" : "left stick click",
    "default" : settings_core.get_settings().get('leftstick', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("leftstick", combo21.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo21)

combo22 = create_combobox({
    "text" : "right stick click",
    "default" : settings_core.get_settings().get('rightstick', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("rightstick", combo22.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo22)

combo23 = create_combobox({
    "text" : "back",
    "default" : settings_core.get_settings().get('back', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("back", combo23.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo23)

combo24 = create_combobox({
    "text" : "start",
    "default" : settings_core.get_settings().get('start', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("start", combo24.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo24)

combo25 = create_combobox({
    "text" : "guide",
    "default" : settings_core.get_settings().get('guide', ""),
    "items": combo_inputs,
    "func" : lambda: settings_core.update_setting("guide", combo25.findChild(QComboBox).currentText())
})
layout_mapping.addWidget(combo25)
layout_controllers.addWidget(tab_mapping)
#//////////////////////////////////////////////////////////

label5 = create_label({
    "text" : "---------Opengloves(experimental, restart to take effect)---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
})
layout_controllers.addWidget(label5)

webcam = create_group_horizontal([
    {
        "type" : "checkbox", 
        "text" : "forward webcam data to open gloves", 
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
    new_value = webcam.findChild(QCheckBox).isChecked()
    settings_core.update_setting("opengloves",new_value)
    if new_value:
        start_opengloves()
    else:
        pass

layout_controllers.addWidget(create_label({
    "text" : "---------Right offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cr_position_offsets = create_group_doublespinbox([
    {
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset x", cr_position_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset y", cr_position_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset z", cr_position_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

cr_rotation_offsets = create_group_doublespinbox([
    {
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset yaw", cr_rotation_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset pitch", cr_rotation_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cr offset roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cr offset roll", cr_rotation_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

layout_controllers.addWidget(cr_position_offsets)
layout_controllers.addWidget(cr_rotation_offsets)

layout_controllers.addWidget(create_label({
    "text" : "---------Left offsets---------", 
    "alignment" : Qt.AlignmentFlag.AlignCenter
}))

cl_position_offsets = create_group_doublespinbox([
    {
        "text" : "X", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset x'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset x", cl_position_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Y", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset y'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset y", cl_position_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Z", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset z'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset z", cl_position_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

cl_rotation_offsets = create_group_doublespinbox([
    {
        "text" : "Yaw", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset yaw'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset yaw", cl_rotation_offsets.findChildren(QDoubleSpinBox)[0].value())
    },
    {
        "text" : "Pitch", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset pitch'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset pitch", cl_rotation_offsets.findChildren(QDoubleSpinBox)[1].value())
    },
    {
        "text" : "Roll", 
        "min":-999999999, 
        "max":999999999, 
        "default":settings_core.get_settings()['cl offset roll'], 
        "steps" : 0.01,
        "func"  : lambda: settings_core.update_setting("cl offset roll", cl_rotation_offsets.findChildren(QDoubleSpinBox)[2].value())
    }
])

layout_controllers.addWidget(cl_position_offsets)
layout_controllers.addWidget(cl_rotation_offsets)
#controllers/////////////////////////////////////////////////////////////////////////////////////////////////////////////

window.addTab(tab_main, "Hmd")
window.addTab(tab_controllers, "Controllers")
window.addTab(tab_driver, "Driver")
window.addTab(tab_credits, "Credits")

window.show()
app.exec()