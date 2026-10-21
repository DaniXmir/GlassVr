# named pipe example script for an Oculus / Meta Touch controller (tag: itc)
# sends position, rotation, input and skeletal data
#
# Pipe names must end in _<tag> (3 letters, case insensitive). The payload is the raw packed struct,
# no tag bytes (the tag bytes are only used for UDP).
#   ..._pos -> PacketPos, ..._rot -> PacketRot, ..._itc -> PacketInputTouch, ..._skl -> PacketSkeletal
import struct
import time
import win32pipe
import win32file
import pywintypes

# the side of the controller to send data to, LEFT/RIGHT
side = "RIGHT"

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')
INPUT_PACKER = struct.Struct('<8?4d')    # PacketInputTouch: 8 bools + 4 doubles
SKELETAL_PACKER = struct.Struct('<25d')  # PacketSkeletal: 20 flexions + 5 splays

PIPE_PREFIX = f"\\\\.\\pipe\\GlassVR_CONTROLLER_{side}"


def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )


while True:
    h_pos = create_pipe(f"{PIPE_PREFIX}_pos")
    h_rot = create_pipe(f"{PIPE_PREFIX}_rot")
    h_input = create_pipe(f"{PIPE_PREFIX}_itc")
    h_skeletal = create_pipe(f"{PIPE_PREFIX}_skl")

    win32pipe.ConnectNamedPipe(h_pos, None)
    win32pipe.ConnectNamedPipe(h_rot, None)
    win32pipe.ConnectNamedPipe(h_input, None)
    win32pipe.ConnectNamedPipe(h_skeletal, None)

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

            buffer_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)
            buffer_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)

            # order must match PacketInputTouch exactly
            buffer_input = INPUT_PACKER.pack(
                system,
                a_x, a_x_cap,
                b_y, b_y_cap,
                trigger_cap,
                joy_btn, joy_cap,
                trigger, grip, joy_x, joy_y
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
