# UDP example script for hmd, trackers and controllers (no input or skeletal):
# sends position and rotation data
#
# UDP wire format: [3 ascii bytes tag][packed struct]
#   pos -> PacketPos (3 doubles), rot -> PacketRot (4 doubles), ext -> PacketExtra (1 bool)
# (little endian, no padding)
import socket
import struct
import time

# IPv4 of the host, the classic way to get yours is to type "ipconfig" in cmd, you can also find it in Task Manager->Performance->Ethernet/Wi-Fi
UDP_IP = "127.0.0.1"
# port (you can select the port for each device in ui)
UDP_PORT = 9000

POS_PACKER = struct.Struct('<3s3d')
ROT_PACKER = struct.Struct('<3s4d')
EXTRA_PACKER = struct.Struct('<3s?')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        # position///
        pos_x = 0.0
        pos_y = 0.0
        pos_z = 0.0

        # rotation///
        rot_w = 1.0
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0

        # extra///
        # UDP only, optional
        reset = False

        # sending///
        # tag 'pos' is for position
        sock.sendto(POS_PACKER.pack(b'pos', pos_x, pos_y, pos_z), (UDP_IP, UDP_PORT))
        # tag 'rot' is for rotation
        sock.sendto(ROT_PACKER.pack(b'rot', rot_w, rot_x, rot_y, rot_z), (UDP_IP, UDP_PORT))
        # tag 'ext' is for extra
        sock.sendto(EXTRA_PACKER.pack(b'ext', reset), (UDP_IP, UDP_PORT))

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    sock.close()
