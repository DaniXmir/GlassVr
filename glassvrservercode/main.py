#pyinstaller --noconfirm --onedir --console --collect-binaries "openvr" main.py

import multiprocessing.shared_memory
import struct
import time
from values import values

v = values()
v.start()

SHM_NAME = 'GlassVrSHM'
SHM_SIZE = 72
PACK_FORMAT = '9d'

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

                ipd = settings.get('ipd')
                head_to_eye_dist = settings.get('head to eye dist')

                print(f"Pos: {pos_x:.2f} {pos_y:.2f} {pos_z:.2f} | Rot: {rot_x:.2f} {rot_y:.2f} {rot_z:.2f}")# | IPD: {ipd} | head to eye dist: {head_to_eye_dist}")

                buffer = struct.pack(
                    PACK_FORMAT, 
                    pos_x, pos_y, pos_z, 
                    rot_w, rot_x, rot_y, rot_z,
                    ipd,head_to_eye_dist
                )

                shm.buf[:SHM_SIZE] = buffer
                time.sleep(1.0 / 120.0)
            except Exception as e:
                print(f"Valve plz fix: {e}")
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