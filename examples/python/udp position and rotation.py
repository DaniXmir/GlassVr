# UDP example script for hmd, trackers and controllers(no input or skeletal):
# sends position and rotation data
import socket
import struct
import time

#IPv4 of the host, the classic way to get yours is to type "ipconfig" in cmd, you can also find it in Task Manager->Performance->Ethernet/Wi-Fi
UDP_IP = "127.0.0.1"
#port (you can select the port for each device in ui)
UDP_PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        #position///
        pos_x = 0.0
        pos_y = 0.0
        pos_z = 0.0
        
        #rotation///
        rot_w = 1.0
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0

        #sending///
        #prefix 'P' is for position
        pos_packet = struct.pack('=cddd', b'P', pos_x, pos_y, pos_z)
        sock.sendto(pos_packet, (UDP_IP, UDP_PORT))
        #prefix 'R' is for rotation
        rot_packet = struct.pack('=cdddd', b'R', rot_w, rot_x, rot_y, rot_z)
        sock.sendto(rot_packet, (UDP_IP, UDP_PORT))

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    sock.close()