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
    #96
    "outer mono" : 45.0,
    "inner mono" : 45.0,
    "top mono" : 30.0,
    "bottom mono" : 30.0,

    #96
    "outer stereo" : 38.0,
    "inner stereo" : 54.0,
    "top stereo" : 25.0,
    "bottom stereo" : 23.0,

    #60
    # "outer stereo" : 25.0,
    # "inner stereo" : 35.0,
    # "top stereo" : 20.0,
    # "bottom stereo" : 18.0,

    #70
    # "outer stereo" : 30.0,
    # "inner stereo" : 40.0,
    # "top stereo" : 22.0,
    # "bottom stereo" : 20.0

    #80
    # "outer stereo" : 34.0,
    # "inner stereo" : 46.0,
    # "top stereo" : 24.0,
    # "bottom stereo" : 22.0

    "ip sending": "127.0.0.1",
    "port sending": 9999,
    "ip receiving": "127.0.0.1",
    "port receiving": 9999,

    "hmd index": 0,

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
}

##################################################################################################
def get_path():
    """
    Constructs and returns the full file path for settings.json 
    inside the 'glassvr' folder within the user's %APPDATA% directory.
    """
    appdata_path = os.getenv('APPDATA')
    folder_name = 'glassvr'
    settings_dir = os.path.join(appdata_path, folder_name)
    file_path = os.path.join(settings_dir, 'settings.json')
    
    try:
        os.makedirs(settings_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {settings_dir}: {e}")
        
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

        # Check if any keys from default_settings are missing in current_settings
        missing_keys = [key for key in default_settings if key not in current_settings]

        if missing_keys:
            # Merge defaults into current: 
            # This keeps user values for existing keys but adds missing defaults
            updated_settings = default_settings.copy()
            updated_settings.update(current_settings)
            
            # Save the updated dictionary back to the file
            with open(file_path, 'w') as f:
                json.dump(updated_settings, f, indent=4)
            
            return updated_settings
        
        return current_settings
        
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading settings, falling back to defaults: {e}")
        return default_settings

def update_setting(key, new_value):
    settings = get_settings()

    settings[key] = new_value
    
    try:
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        print(e)