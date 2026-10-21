#udp skeletal only
import socket
import struct
import time

# IPv4 of the host, the classic way to get yours is to type "ipconfig" in cmd, you can also find it in Task Manager->Performance->Ethernet/Wi-Fi
UDP_IP = "127.0.0.1"
# port (you can select the port for each device in ui), default: right = 9001, left = 9002
UDP_PORT = 9002

SKELETAL_PACKER = struct.Struct('<3s25d')   # PacketSkeletal: 20 flexions + 5 splays

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
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
        reset = False

        sock.sendto(SKELETAL_PACKER.pack(b'skl', *(flexions + splays)), (UDP_IP, UDP_PORT))

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    sock.close()