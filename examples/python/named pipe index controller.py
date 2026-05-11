# named pipe example script for controllers:
# sends position, rotation, input and skeletal data
import struct
import time
import win32pipe
import win32file
import pywintypes

#the side of the controller to send data to, LEFT/RIGHT
side = "RIGHT"

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')
INPUT_PACKER = struct.Struct("<12?8d")
SKELETAL_PACKER = struct.Struct("<25d")

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )

while True:
    h_pos = create_pipe(f"\\\\.\\pipe\\GlassVR_CONTROLLER_{side}_Pos")
    h_rot = create_pipe(f"\\\\.\\pipe\\GlassVR_CONTROLLER_{side}_Rot")
    h_input = create_pipe(f"\\\\.\\pipe\\GlassVR_CONTROLLER_{side}_Input")
    h_skeletal = create_pipe(f"\\\\.\\pipe\\GlassVR_CONTROLLER_{side}_Skeletal")
    
    win32pipe.ConnectNamedPipe(h_pos, None)
    win32pipe.ConnectNamedPipe(h_rot, None)
    win32pipe.ConnectNamedPipe(h_input, None)
    win32pipe.ConnectNamedPipe(h_skeletal, None)
    
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
            
            buffer_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)
            buffer_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)
            
            buffer_input = INPUT_PACKER.pack(
                a, b, system, joy_btn, trigger_btn,
                a_cap, b_cap, system_cap, joy_cap, trigger_cap, touch_cap, grip_cap,
                joy_x, joy_y, touch_x, touch_y, trigger, touch_force, grip_pull, grip_force
            )
            
            buffer_skeletal = SKELETAL_PACKER.pack(*(flexions + splays))
            
            win32file.WriteFile(h_pos, buffer_pos)
            win32file.WriteFile(h_rot, buffer_rot)
            win32file.WriteFile(h_input, buffer_input)
            win32file.WriteFile(h_skeletal, buffer_skeletal)
            
            time.sleep(0.001)
    except pywintypes.error:
        pass
    finally:
        for h in [h_pos, h_rot, h_input, h_skeletal]:
            win32pipe.DisconnectNamedPipe(h)
            win32file.CloseHandle(h)
        time.sleep(1)