import numpy as np


def rot_matrix_to_yxz_euler(m):
    """Extrinsic yxz: m = Rz(roll) @ Rx(pitch) @ Ry(yaw). Returns degrees."""
    pitch = np.arcsin(np.clip(m[2, 1], -1.0, 1.0))
    if abs(np.cos(pitch)) > 1e-6:
        yaw   = np.arctan2(-m[2, 0], m[2, 2])
        roll  = np.arctan2(-m[0, 1], m[1, 1])
    else:
        # Gimbal lock: set roll=0, solve yaw
        roll = 0.0
        yaw  = np.arctan2(-m[1, 0], m[0, 0])
    return np.degrees([yaw, pitch, roll])
