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

    "hmdpos index": 0,
    "hmdrot index": 0,

    "hmd redirect invert yaw" : False,
    "hmd redirect invert pitch" : False,
    "hmd redirect invert roll" : False,

    "hmdpos mode" : "redirect",
    "hmdrot mode" : "redirect",

    # "hmdpos update from server" : False,
    # "hmdrot update from server" : False,

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

    "crpos index": 0,
    "crrot index": 0,

    "crpos mode" : "redirect",
    "crrot mode" : "redirect",

    # "crpos update from server" : False,
    # "crrot update from server" : False,

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

    "clpos index": 0,
    "clrot index": 0,

    "clpos mode" : "redirect",
    "clrot mode" : "redirect",

    # "clpos update from server" : False,
    # "clrot update from server" : False,

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

    "0a": "right grip",
    "0b": "right b",
    "0x": "reset gyro",
    "0y": "right a",
    "0dpup": "none",
    "0dpdown": "none",
    "0dpleft": "none",
    "0dpright": "none",
    "0leftshoulder": "right grip",
    "0rightshoulder": "right grip",
    "0lefttrigger": "none",
    "0righttrigger": "none",
    "0leftstick": "right joy button",
    "0rightstick": "none",
    "0leftx": "right joy y",
    "0lefty": "right joy x",
    "0rightx": "none",
    "0righty": "none",
    "0back": "none",
    "0start": "right menu",
    "0guide": "none",
    "0misc1": "none",
    "0touchpad": "none",
    "0paddle1": "right touch modifier",
    "0paddle2": "none",
    "0paddle3": "right trigger",
    "0paddle4": "none",

    "1a": "left a",
    "1b": "left b",
    "1x": "reset gyro",
    "1y": "left grip",
    "1dpup": "none",
    "1dpdown": "none",
    "1dpleft": "none",
    "1dpright": "none",
    "1leftshoulder": "left grip",
    "1rightshoulder": "left grip",
    "1lefttrigger": "none",
    "1righttrigger": "none",
    "1leftstick": "left joy button",
    "1rightstick": "none",
    "1leftx": "left joy y",
    "1lefty": "left joy x",
    "1rightx": "none",
    "1righty": "none",
    "1back": "none",
    "1start": "left menu",
    "1guide": "none",
    "1misc1": "none",
    "1touchpad": "none",
    "1paddle1": "none",
    "1paddle2": "left touch modifier",
    "1paddle3": "none",
    "1paddle4": "left trigger",

    "joy1 invert x": True,
    "joy1 invert y": False,
    "joy2 invert x": False,
    "joy2 invert y": True,

    "hmd gyro index": 0,
    "cl gyro index": 1,
    "cr gyro index": 0,

    "gyro1 invert x": False,
    "gyro1 invert y": False,
    "gyro1 invert z": True,
    "gyro2 invert x": True,
    "gyro2 invert y": False,
    "gyro2 invert z": False,

    "gyro1 index x": 2,
    "gyro1 index y": 1,
    "gyro1 index z": 0,
    "gyro2 index x": 2,
    "gyro2 index y": 1,
    "gyro2 index z": 0,

    "gyro1 sensitivity": 1000.0,
    "gyro2 sensitivity": 1000.0,

    "bluetooth skip correction": False,

    "enable hmd": True,
    "enable cr": False,
    "enable cl": False,

    "opengloves": False,
    "camera z": 0.025,
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