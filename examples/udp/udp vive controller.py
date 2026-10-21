# UDP example script for an HTC Vive wand (tag: ive):
# sends position, rotation, input and skeletal data
#
# UDP wire format: [3 ascii bytes tag][packed struct], little endian, no padding
#   pos -> PacketPos, rot -> PacketRot, ive -> PacketInputVive, skl -> PacketSkeletal, ext -> PacketExtra
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
INPUT_PACKER = struct.Struct('<3s6?3d')     # PacketInputVive: 6 bools + 3 doubles
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
        system = False
        # fun fact: og htc vive wands are the only controllers that have clickable grips
        # (/input/grip/click) and a clickable touchpad (/input/trackpad/click).
        # the grip is click only, there is no analog value for it.
        grip_btn = False
        select = False       # the menu button
        trigger_btn = False
        touch_btn = False    # touchpad click

        # capacitive touch///
        touch_cap = False    # finger resting on the touchpad

        # float analog///
        trigger = 0.0   # 0..1
        touch_x = 0.0   # -1..1
        touch_y = 0.0   # -1..1

        # skeletal///
        # the vive wand has no skeletal input of its own, the driver ignores this packet for it.
        # it is only here to keep the same structure as the other examples, you can remove it.
        flexions = [0.0] * 20
        splays = [0.0] * 5

        # extra///
        # UDP only, optional
        reset = False

        # sending///
        # tag 'pos' is for position
        sock.sendto(POS_PACKER.pack(b'pos', pos_x, pos_y, pos_z), (UDP_IP, UDP_PORT))
        # tag 'rot' is for rotation
        sock.sendto(ROT_PACKER.pack(b'rot', rot_w, rot_x, rot_y, rot_z), (UDP_IP, UDP_PORT))
        # tag 'ive' is for vive input, order must match PacketInputVive exactly
        input_packet = INPUT_PACKER.pack(
            b'ive',
            system, grip_btn, select, trigger_btn, touch_btn, touch_cap,
            trigger, touch_x, touch_y
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
