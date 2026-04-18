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
    "fov" : 90.0,
    "convergence" : 0.0,

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

    #hand tracking///////////////////////////
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
        return default_settings

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