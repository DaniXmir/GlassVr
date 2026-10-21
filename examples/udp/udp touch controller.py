# UDP example script for an Oculus / Meta Touch controller (tag: itc):
# sends position, rotation, input and skeletal data
#
# UDP wire format: [3 ascii bytes tag][packed struct], little endian, no padding
#   pos -> PacketPos, rot -> PacketRot, itc -> PacketInputTouch, skl -> PacketSkeletal, ext -> PacketExtra
# one port per hand: the hand is decided by the port, not by the packet
import socket
import struct
import time

# IPv4 of the host, the classic way to get yours is to type "ipconfig" in cmd, you can also find it in Task Manager->Performance->Ethernet/Wi-Fi
UDP_IP = "127.0.0.1"
# port (you can select the port for each device in ui), default: right = 9001, left = 9002
UDP_PORT = 9001

POS_PACKER = struct.Struct('<3s3d')
ROT_PACKER = struct.Struct('<3s4d')
INPUT_PACKER = struct.Struct('<3s8?4d')     # PacketInputTouch: 8 bools + 4 doubles
SKELETAL_PACKER = struct.Struct('<3s25d')   # PacketSkeletal: 20 flexions + 5 splays
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

        # input//
        # the left hand has X/Y, the right hand has A/B:
        #   a_x = X (left) / A (right)      b_y = Y (left) / B (right)
        system = False
        a_x = False;  a_x_cap = False
        b_y = False;  b_y_cap = False
        joy_btn = False;  joy_cap = False
        trigger_cap = False   # the touch profile has no trigger click, only touch

        # float analog///
        trigger = 0.0   # 0..1
        grip = 0.0      # 0..1 (no grip click / touch in the profile)
        joy_x = 0.0     # -1..1
        joy_y = 0.0     # -1..1

        # skeletal///
        # not every index is used, just jumps of 4:
        # flexions[0] = 1.0 #thumb
        # flexions[4] = 1.0 #index
        # flexions[8] = 1.0 #middle
        # flexions[12] = 1.0 #ring
        # flexions[16] = 1.0 #pinky
        flexions = [0.0] * 20

        # range -inf <-> inf lol
        splays = [0.0] * 5

        # extra///
        # UDP only, optional
        reset = False

        # sending///
        # tag 'pos' is for position
        sock.sendto(POS_PACKER.pack(b'pos', pos_x, pos_y, pos_z), (UDP_IP, UDP_PORT))
        # tag 'rot' is for rotation
        sock.sendto(ROT_PACKER.pack(b'rot', rot_w, rot_x, rot_y, rot_z), (UDP_IP, UDP_PORT))
        # tag 'itc' is for touch input, order must match PacketInputTouch exactly
        input_packet = INPUT_PACKER.pack(
            b'itc',
            system,
            a_x, a_x_cap,
            b_y, b_y_cap,
            trigger_cap,
            joy_btn, joy_cap,
            trigger, grip, joy_x, joy_y
        )
        sock.sendto(input_packet, (UDP_IP, UDP_PORT))
        # tag 'skl' is for skeletal
        sock.sendto(SKELETAL_PACKER.pack(b'skl', *(flexions + splays)), (UDP_IP, UDP_PORT))
        # tag 'ext' is for extra
        sock.sendto(EXTRA_PACKER.pack(b'ext', reset), (UDP_IP, UDP_PORT))

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    sock.close()
