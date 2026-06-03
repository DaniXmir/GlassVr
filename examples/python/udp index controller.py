# UDP example script for controllers:
# sends position, rotation, input and skeletal data
import socket
import struct
import time

#IPv4 of the host, the classic way to get yours is to type "ipconfig" in cmd, you can also find it in Task Manager->Performance->Ethernet/Wi-Fi
UDP_IP = "127.0.0.1"
#port (you can select the port for each device in ui)
UDP_PORT = 9001

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

        #input//
        #boolead(on/off) buttons///
        a = False
        b = False
        system = False
        joy_btn = False
        trigger_btn = False
        
        #capacitive touch///
        # index controllers has capacitive touch on every single button if you have no idea how to implement that in your project just dont 
        # but i do recommend making it so each counterpart will always be in the same state like: a, a_cap = True///
        a_cap = False
        b_cap = False
        system_cap = False
        joy_cap = False
        trigger_cap = False
        touch_cap = False
        grip_cap = False
        
        #float(0.0->1.0) analog///
        joy_x = 0.0
        joy_y = 0.0
        touch_x = 0.0
        touch_y = 0.0
        trigger = 0.0
        touch_force = 0.0

        #the only game i saw that uses pull and force individually is valve's Aperture hand lab demo
        # so just set them to be the same like: grip_pull, grip_force = 1.0
        # also i recommend activating grip_cap if any of these is more then 0.01
        grip_pull = 0.0
        grip_force = 0.0

        #skeletal///
        #not every index is used, just jumps of 4:
        # flexions[0] = 1.0 #thumb
        # flexions[4] = 1.0 #index
        # flexions[8] = 1.0 #middle
        # flexions[12] = 1.0 #ring
        # flexions[16] = 1.0 #pinky
        flexions = [0.0] * 20

        #range ∞ <-> ∞ lol
        splays = [0.0] * 5

        #sending///
        #prefix 'P' is for position
        pos_packet = struct.pack('=cddd', b'P', pos_x, pos_y, pos_z)
        sock.sendto(pos_packet, (UDP_IP, UDP_PORT))
        #prefix 'R' is for rotation
        rot_packet = struct.pack('=cdddd', b'R', rot_w, rot_x, rot_y, rot_z)
        sock.sendto(rot_packet, (UDP_IP, UDP_PORT))
        #prefix 'I' is for input
        input_packet = struct.pack(
            '=c12?8d', 
            b'I', 
            a, b, system, joy_btn, trigger_btn, 
            a_cap, b_cap, system_cap, joy_cap, trigger_cap, touch_cap, grip_cap,
            joy_x, joy_y, touch_x, touch_y, trigger, touch_force, grip_pull, grip_force
        )
        sock.sendto(input_packet, (UDP_IP, UDP_PORT))
        #prefix 'S' is for skeletal
        skeletal_packet = struct.pack('=c25d', b'S', *(flexions + splays))
        sock.sendto(skeletal_packet, (UDP_IP, UDP_PORT))

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    sock.close()