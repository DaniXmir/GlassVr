# named pipe example script for hmd:
# sends position and rotation data
import struct
import time
import win32pipe
import win32file
import pywintypes

POS_PACKER = struct.Struct('<3d')
ROT_PACKER = struct.Struct('<4d')

def create_pipe(pipe_name):
    return win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 1024, 1024, 0, None
    )

while True:
    h_pos = create_pipe(r'\\.\pipe\GlassVR_HMD_Pos')
    h_rot = create_pipe(r'\\.\pipe\GlassVR_HMD_Rot')
    
    win32pipe.ConnectNamedPipe(h_pos, None)
    win32pipe.ConnectNamedPipe(h_rot, None)
    
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
            
            buffer_pos = POS_PACKER.pack(pos_x, pos_y, pos_z)
            buffer_rot = ROT_PACKER.pack(rot_w, rot_x, rot_y, rot_z)
            
            win32file.WriteFile(h_pos, buffer_pos)
            win32file.WriteFile(h_rot, buffer_rot)
            
            time.sleep(0.001)
    except pywintypes.error:
        pass
    finally:
        for h in [h_pos, h_rot]:
            win32pipe.DisconnectNamedPipe(h)
            win32file.CloseHandle(h)
        time.sleep(1)