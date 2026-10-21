# UDP example script for a Steam Frame controller (tag: ifm):
# sends position, rotation, input and skeletal data
#
# UDP wire format: [3 ascii bytes tag][packed struct], little endian, no padding
#   pos -> PacketPos, rot -> PacketRot, ifm -> PacketInputFrame, skl -> PacketSkeletal, ext -> PacketExtra
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
INPUT_PACKER = struct.Struct('<3s20?4d')    # PacketInputFrame: 20 bools + 4 doubles
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
        # one struct covers both hands, the driver only reads the fields its hand has.
        # every source has a click (bool) and a touch (_cap), keep them consistent:
        # if the click is True, the _cap should be True too.

        # left hand only (dpad + view)///
        y_up = False;     y_up_cap = False
        a_down = False;   a_down_cap = False
        x_left = False;   x_left_cap = False
        b_right = False;  b_right_cap = False
        select = False;   select_cap = False

        # both hands///
        bumper = False;       bumper_cap = False
        system = False;       system_cap = False
        trigger_btn = False;  trigger_cap = False
        grip_btn = False;     grip_cap = False
        joy_btn = False;      joy_cap = False

        # float analog///
        trigger = 0.0   # 0..1
        grip = 0.0      # 0..1
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
        # tag 'ifm' is for steam frame input, order must match PacketInputFrame exactly
        input_packet = INPUT_PACKER.pack(
            b'ifm',
            y_up, y_up_cap,
            a_down, a_down_cap,
            x_left, x_left_cap,
            b_right, b_right_cap,
            select, select_cap,
            bumper, bumper_cap,
            system, system_cap,
            trigger_btn, trigger_cap,
            grip_btn, grip_cap,
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
