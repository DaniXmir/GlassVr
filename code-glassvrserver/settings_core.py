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
    
    "outer mono" : 45.0,
    "inner mono" : 45.0,
    "top mono" : 30.0,
    "bottom mono" : 30.0,

    "outer stereo" : 38.0,
    "inner stereo" : 54.0,
    "top stereo" : 25.0,
    "bottom stereo" : 23.0,

    "tracker index": 0,

    "ip sending": "127.0.0.1",
    "port sending": 9999,
    "ip receiving": "127.0.0.1",
    "port receiving": 9999,

    "ipd": 0.0,
    "head to eye dist": 0.0,

    "offset x": 0.0,
    "offset y": 0.0,
    "offset z": 0.0,

    "offset yaw": 0.0,
    "offset pitch": 0.0,
    "offset roll": 0.0
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


def get_settings():
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
        
    except (FileNotFoundError):#, json.JSONDecodeError):
        try:
            with open(file_path, 'w') as f:
                json.dump(default_settings, f, indent=4)
        except OSError:
            print(OSError)
        return default_settings
    except Exception:
        print(Exception)
        return default_settings

def update_setting(key, new_value):
    settings = get_settings()

    settings[key] = new_value
    
    try:
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        print(e)