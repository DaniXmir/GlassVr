# named pipe example script for an HTC Vive wand (tag: ive)
# sends position, rotation, input and skeletal data
#
# Pipe names must end in _<tag> (3 letters, case insensitive). The payload is the raw packed struct,
# no tag bytes (the tag bytes are only used for UDP).
#   ..._pos -> PacketPos, ..._rot -> PacketRot, ..._ive -> PacketInputVive, ..._skl -> PacketSkeletal
import struct
import time
import win32pipe
import win32file
import pywintypes

# the side of the controller to send data to, LEFT/RIGHT
side = "RIGHT"

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')
INPUT_PACKER = struct.Struct('<6?3d')    # PacketInputVive: 6 bools + 3 doubles
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
    h_input = create_pipe(f"{PIPE_PREFIX}_ive")
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
            # the vive wand has no skeletal input of its own. this pipe is optional,
            # it is only here to keep the same structure as the other examples.
            flexions = [0.0] * 20
            splays = [0.0] * 5

            buffer_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)
            buffer_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)

            # order must match PacketInputVive exactly
            buffer_input = INPUT_PACKER.pack(
                system, grip_btn, select, trigger_btn, touch_btn, touch_cap,
                trigger, touch_x, touch_y
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
