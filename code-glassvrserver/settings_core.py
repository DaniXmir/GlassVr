import json
import os

default_settings = {
    "vrsettings path": "C:/Program Files (x86)/Steam/config",
    "drivers path" : "C:/Program Files (x86)/Steam/steamapps/common/SteamVR/drivers",
    "resolution x" : 1920,
    "resolution y" : 1080,
    "refresh rate" : 120,

    "fullscreen" : False,

    "stereoscopic" : False,
    
    #fov///////////////////////////

    "fov" : 90,

    #90
    "outer mono" : 41.070,
    "inner mono" : 41.070,
    "top mono" : 26.120,
    "bottom mono" : 26.120,

    #90
    "outer stereo" : 41.070,
    "inner stereo" : 41.070,
    "top stereo" : 26.120,
    "bottom stereo" : 26.120,

    # "ip sending": "127.0.0.1",
    # "port sending": 9999,
    # "ip receiving": "127.0.0.1",
    # "port receiving": 9999,

    "prediction time" : 0.011,

    "hmd index": 0,
    "hmd update from server" : False,

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

    "cr index": 0,
    "cr update from server" : False,

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

    "cl index": 0,
    "cl update from server" : False,

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

    "controller index 1" : 0,
    "controller index 2" : 1,

    "a": "right a",
    "b": "right b",
    "x": "left grip",
    "y": "right grip",
    "dpup": "left grip",
    "dpdown": "left a",
    "dpleft": "left b",
    "dpright": "right grip",
    "leftshoulder": "left touch modifier",
    "rightshoulder": "right touch modifier",
    "lefttrigger": "left trigger",
    "righttrigger": "right trigger",
    "leftstick": "left joy button",
    "rightstick": "right joy button",
    "leftx": "left joy x",
    "lefty": "left joy y",
    "rightx": "right joy x",
    "righty": "right joy y",
    "back": "left menu",
    "start": "right menu",
    "guide": "right a",
    "misc1": "",
    "touchpad": "",
    "paddle1": "right grip",
    "paddle2": "left grip",
    "paddle3": "right grip",
    "paddle4": "left grip",

    "enable hmd": True,
    "enable cr": False,
    "enable cl": False,

    "opengloves": False,
    "camera index": 0,

    "trackers num": 0,
}

##################################################################################################
def get_path():
    appdata_path = os.getenv('APPDATA')
    folder_name = 'glassvr'
    settings_dir = os.path.join(appdata_path, folder_name)
    file_path = os.path.join(settings_dir, 'settings.json')
    
    try:
        os.makedirs(settings_dir, exist_ok=True)
    except OSError as e:
        #print(e)
        pass
        
    return file_path

file_path = get_path()
#file_path = 'settings.json'
##################################################################################################

def reset_settings():
    with open(file_path, 'w') as f:
        json.dump(default_settings, f, indent=4)

def get_settings():
    try:
        if not os.path.exists(file_path):
            reset_settings()
            return default_settings

        with open(file_path, 'r') as f:
            current_settings = json.load(f)

        missing_keys = [key for key in default_settings if key not in current_settings]

        if missing_keys:
            updated_settings = default_settings.copy()
            updated_settings.update(current_settings)
            
            with open(file_path, 'w') as f:
                json.dump(updated_settings, f, indent=4)
            
            return updated_settings
        
        return current_settings
        
    except (json.JSONDecodeError, OSError) as e:
        #print(e)
        return default_settings

def update_setting(key, new_value):
    settings = get_settings()

    settings[key] = new_value
    
    try:
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        pass
        #print(e)