#settings file, driver has its own settings file equivalent
#creates a settings.json in appdata for both driver/ui to read from

#usage:
#import settings as se
#use this to get
#se.get_settings().get("resolution x",1920)
#and this to update
#se.update_setting("resolution y",2560)

import json
import os

#you dont need to change this, update_setting will add it if its not already in the json
default_settings = {
    #old paths
    # "vrsettings path": "C:/Program Files (x86)/Steam/config",
    # "drivers path" : "C:/Program Files (x86)/Steam/steamapps/common/SteamVR/drivers",
    "theme": ";Prism",
    
    "steam path": "C:/Program Files (x86)/Steam",
    "steamvr path" : "C:/Program Files (x86)/Steam/steamapps/common/SteamVR",

    "resolution x" : 1920,
    "resolution y" : 1080,
    "refresh rate" : 120,

    "fullscreen" : False,

    "stereoscopic" : False,
    
    #fov///////////////////////////////////////////////
    "fov" : 90.0,
    "convergence" : 0.0,

    #90
    "outer" : 41.070,
    "inner" : 41.070,
    "top" : 26.120,
    "bottom" : 26.120,

    "prediction time" : 0.011,

    "hmdpos copy serial": "",
    "hmdrot copy serial": "",

    # "hmd redirect invert yaw" : False,
    # "hmd redirect invert pitch" : False,
    # "hmd redirect invert roll" : False,

    "hmdpos mode" : "copy",
    "hmdrot mode" : "copy",

    "hmd offset world x": 0.0,
    "hmd offset world y": 0.0,
    "hmd offset world z": 0.0,
    "hmd offset world yaw": 0.0,
    "hmd offset world pitch": 0.0,
    "hmd offset world roll": 0.0,

    "hmd offset local x": 0.0,
    "hmd offset local y": 0.0,
    "hmd offset local z": 0.0,
    "hmd offset local yaw": 0.0,
    "hmd offset local pitch": 0.0,
    "hmd offset local roll": 0.0,

    "ipd": 0.0,
    "head to eye dist": 0.0,

    "crpos copy serial": "",
    "crrot copy serial": "",

    "crpos mode" : "copy",
    "crrot mode" : "copy",

    "cr offset world x": 0.0,
    "cr offset world y": 0.0,
    "cr offset world z": 0.0,
    "cr offset world yaw": 0.0,
    "cr offset world pitch": 0.0,
    "cr offset world roll": 0.0,

    "cr offset local x": 0.0,
    "cr offset local y": 0.0,
    "cr offset local z": 0.0,
    "cr offset local yaw": 0.0,
    "cr offset local pitch": 0.0,
    "cr offset local roll": 0.0,

    "cr playspace yaw": 0.0,

    "clpos copy serial": "",
    "clrot copy serial": "",

    "clpos mode" : "copy",
    "clrot mode" : "copy",

    "cl offset world x": 0.0,
    "cl offset world y": 0.0,
    "cl offset world z": 0.0,
    "cl offset world yaw": 0.0,
    "cl offset world pitch": 0.0,
    "cl offset world roll": 0.0,

    "cl offset local x": 0.0,
    "cl offset local y": 0.0,
    "cl offset local z": 0.0,
    "cl offset local yaw": 0.0,
    "cl offset local pitch": 0.0,
    "cl offset local roll": 0.0,

    "cl playspace yaw": 0.0,

    "cr_a" : "",
    "cr_b" : "",
    "cr_trigger" : "",
    "cr_grip" : "",
    "cr_menu" : "",

    "cr_joy up" : "",
    "cr_joy down" : "",
    "cr_joy left" : "",
    "cr_joy right" : "",
    "cr_joy click" : "",

    "cr_touch up" : "",
    "cr_touch down" : "",
    "cr_touch left" : "",
    "cr_touch right" : "",
    "cr_touch click" : "",

    "cl_a" : "",
    "cl_b" : "",
    "cl_trigger" : "",
    "cl_grip" : "",
    "cl_menu" : "",

    "cl_joy up" : "",
    "cl_joy down" : "",
    "cl_joy left" : "",
    "cl_joy right" : "",
    "cl_joy click" : "",

    "cl_touch up" : "",
    "cl_touch down" : "",
    "cl_touch left" : "",
    "cl_touch right" : "",
    "cl_touch click" : "",

    "hmd gyro id": "",
    "cl gyro id": "",
    "cr gyro id": "",

    "bluetooth skip correction": False,

    "enable hmd": True,
    "enable cr": False,
    "enable cl": False,

    #hand tracking//////////////////////////////////////
    "hand tracking": False,
    "curl" : True,
    "splay" : True,
    "index=trigger" : False,
    "other=grip" : False,
    "camera index": 0,
    "camera offset x": 0.0,
    "camera offset y": 0.0,
    "camera offset z": 0.0,

    # "markers": False,
    # "markers z" : 0.9,
    # "crpos marker id" : 98,
    # "crrot marker id" : 98,

    # "clpos marker id" : 40,
    # "clrot marker id" : 40,

    "trackers num": 0,

    "bad apple speed" : 10.0,
    "bad apple ui" : True,

    "crinput mode" : "app (named pipe)",
    "crskeletal mode" : "app (named pipe)",

    "clinput mode" : "app (named pipe)",
    "clskeletal mode" : "app (named pipe)",

    "hmd port" : 9000,
    "cr port" : 9001,
    "cl port" : 9002,
    #"0tracker port" : 9003

    #streaming legacy////////////////////////////////////////
    "mirror window" : False,
    "mirror web" : False,
    "mirror web port" : 9999,
    "mirror web bitrate" : 100,
    "mirror web scale" : 1.0,

    #streaming////////////////////////////////////////
    "display mode" : "extended", #"virtual", #"extended",
    "encoder" : "H.265", #"H.265", #"H.264", #"AV1", #"HEVC",
    "client ip" : "127.0.0.1",
    "bitrate" : 100,
    "virtual port" : "9990",

    #arcore playspace sync/////////////////////////////
    "hmd playspace reset method": "Fixed Position",
    "hmd playspace y": 0.0,
    "cr playspace reset method": "Headset",
    "cr playspace z" : -0.25,
    "cl playspace reset method": "Headset",
    "cl playspace z" : -0.25,

    #visualizer////////////////////////////////////////
    "enable visualizer" : True,
    "attach cam" : False,
    "visualizer separate window" : False,

    "enable tracker display" : True,

    "hook overrides" : []
}

def get_path():
    appdata_path = os.getenv('APPDATA')
    folder_name = 'glassvr'
    settings_dir = os.path.join(appdata_path, folder_name)
    file_path = os.path.join(settings_dir, 'settings.json')
    
    try:
        os.makedirs(settings_dir, exist_ok=True)
    except OSError as e:
        pass
        
    return file_path

file_path = get_path()

def reset_settings():
    with open(file_path, 'w') as f:
        json.dump(default_settings, f, indent=4)

last_good_settings = None

def get_settings():
    #this returns the whole dict and not one individual setting
    global last_good_settings
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                current_settings = json.load(f)
        else:
            current_settings = {}

        merged_settings = default_settings.copy()
        merged_settings.update(current_settings)

        if merged_settings != current_settings:
            try:
                with open(file_path, 'w') as f:
                    json.dump(merged_settings, f, indent=4)
            except OSError:
                pass

        last_good_settings = merged_settings
        return merged_settings

    except (json.JSONDecodeError, OSError):
        return last_good_settings if last_good_settings is not None else default_settings.copy()

def update_setting(key, new_value):
    settings = get_settings()

    settings[key] = new_value
    
    try:
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        pass

def update_nested(dict_name, new_data):
    #example: update_nested("a4-53-85-4a-e7-18", {"index_x": 2, "invert_x": True})
    #if the same example is use on update_setting, it will override the dict instead of update it
    settings = get_settings()

    if dict_name not in settings or not isinstance(settings[dict_name], dict):
        settings[dict_name] = {}

    settings[dict_name].update(new_data)

    try:
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        pass