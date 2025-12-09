import socket
import struct
import time
from values import values

PACK_FORMAT = '<9d'
PACKET_SIZE = struct.calcsize(PACK_FORMAT)

v = values()
v.start()

settings = v.get_settings()

UDP_IP = settings['ip address']
UDP_PORT = settings['port']

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Sending VR pose data to {UDP_IP}:{UDP_PORT}. Packet size: {PACKET_SIZE} bytes.")

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
                
                buffer = struct.pack(
                    PACK_FORMAT, 
                    pos_x, pos_y, pos_z, 
                    rot_w, rot_x, rot_y, rot_z,
                    ipd, head_to_eye_dist
                )

                sock.sendto(buffer, (UDP_IP, UDP_PORT))

                print(f"Sent Pos: {pos_x:.2f} {pos_y:.2f} {pos_z:.2f} | Rot: {rot_w:.2f} {rot_x:.2f} {rot_y:.2f} {rot_z:.2f}")
            
                time.sleep(0)
            
            except Exception as e:
                print(f"Error processing/sending data: {e}")
                time.sleep(1.0 / 120.0)

    except KeyboardInterrupt:
        print("\nStopping sender.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()