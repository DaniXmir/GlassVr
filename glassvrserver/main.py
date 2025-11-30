#pyinstaller --noconfirm --onedir --console --collect-binaries "openvr" main.py

import multiprocessing.shared_memory
import struct
import time
import math
import json
from values import values

v = values()
v.start()

SHM_NAME = 'GlassVrSHM'
SHM_SIZE = 56
PACK_FORMAT = '7d'

def main():
    try:
        shm = multiprocessing.shared_memory.SharedMemory(create=True, size=SHM_SIZE, name=SHM_NAME)
    except FileExistsError:
        shm = multiprocessing.shared_memory.SharedMemory(name=SHM_NAME)
    except Exception:
        return

    try:
        while True:
            try:
                settings = v.get_settings()
                idx = settings['index']
                data = v.get_device_position(idx)
                
                pos_x = data['position x']
                pos_y = data['position y']
                pos_z = data['position z']
                rot_w = data['rotation w']
                rot_x = data['rotation x']
                rot_y = data['rotation y']
                rot_z = data['rotation z']

                print("Position: x_" + str(pos_x),"y_" + str(pos_y),"z_" + str(pos_z),"Rotation: w_" + str(rot_w),"x_" + str(rot_x),"y_" + str(rot_y),"z_" + str(rot_z))

                buffer = struct.pack(
                    PACK_FORMAT, 
                    pos_x, pos_y, pos_z, 
                    rot_w, rot_x, rot_y, rot_z
                )

                shm.buf[:SHM_SIZE] = buffer
                time.sleep(1.0 / 120.0)
            except:
                time.sleep(1.0 / 120.0)

    except KeyboardInterrupt:
        pass
    finally:
        shm.close()
        try:
            shm.unlink()
        except:
            pass

if __name__ == "__main__":
    main()