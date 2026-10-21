# UDP example script for a Valve Index controller (tag: idx):
# sends position, rotation, input and skeletal data
#
# UDP wire format: [3 ascii bytes tag][packed struct], little endian, no padding
#   pos -> PacketPos, rot -> PacketRot, idx -> PacketInputIndex, skl -> PacketSkeletal, ext -> PacketExtra
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
INPUT_PACKER = struct.Struct('<3s12?8d')    # PacketInputIndex: 12 bools + 8 doubles
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
        # boolean (on/off) buttons///
        a = False
        b = False
        system = False
        joy_btn = False
        trigger_btn = False

        # capacitive touch///
        # index controllers have capacitive touch on every single button. if you have no idea how to
        # implement that in your project just don't, but i do recommend making it so each counterpart
        # will always be in the same state, like: a, a_cap = True
        a_cap = False
        b_cap = False
        system_cap = False
        joy_cap = False
        trigger_cap = False
        touch_cap = False
        grip_cap = False

        # float (0.0 -> 1.0) analog///
        joy_x = 0.0
        joy_y = 0.0
        touch_x = 0.0
        touch_y = 0.0
        trigger = 0.0
        touch_force = 0.0

        # the only game i saw that uses pull and force individually is valve's Aperture hand lab demo
        # so just set them to be the same, like: grip_pull, grip_force = 1.0
        # also i recommend activating grip_cap if any of these is more than 0.01
        grip_pull = 0.0
        grip_force = 0.0

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
        # tag 'idx' is for index input, order must match PacketInputIndex exactly
        input_packet = INPUT_PACKER.pack(
            b'idx',
            a, b, system, joy_btn, trigger_btn,
            a_cap, b_cap, system_cap, joy_cap, trigger_cap, touch_cap, grip_cap,
            joy_x, joy_y, touch_x, touch_y, trigger, touch_force, grip_pull, grip_force
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
