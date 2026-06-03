#include "globals.h"
#include "settings.h"
#include <cmath>
#include <algorithm>


static void MultiplyQuat(float q1[4], float q2[4], float out[4]) {
    out[0] = q1[3] * q2[0] + q1[0] * q2[3] + q1[1] * q2[2] - q1[2] * q2[1];//x
    out[1] = q1[3] * q2[1] - q1[0] * q2[2] + q1[1] * q2[3] + q1[2] * q2[0];//y
    out[2] = q1[3] * q2[2] + q1[0] * q2[1] - q1[1] * q2[0] + q1[2] * q2[3];//z
    out[3] = q1[3] * q2[3] - q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2];//w
}

static void RotateVector(float q[4], float v[3], float out[3]) {
    float q_vec[3] = { q[0], q[1], q[2] };
    float cross1[3] = {
        q_vec[1] * v[2] - q_vec[2] * v[1],
        q_vec[2] * v[0] - q_vec[0] * v[2],
        q_vec[0] * v[1] - q_vec[1] * v[0]
    };
    for (int i = 0; i < 3; i++) cross1[i] *= 2.0f;

    float cross2[3] = {
        q_vec[1] * cross1[2] - q_vec[2] * cross1[1],
        q_vec[2] * cross1[0] - q_vec[0] * cross1[2],
        q_vec[0] * cross1[1] - q_vec[1] * cross1[0]
    };

    for (int i = 0; i < 3; i++) {
        out[i] = v[i] + (q[3] * cross1[i]) + cross2[i];
    }
}

static void EulerToQuat(float rollZ, float yawY, float pitchX, float q[4]) {
    float cz = cosf(rollZ * 0.5f); float sz = sinf(rollZ * 0.5f);
    float cy = cosf(yawY * 0.5f);  float sy = sinf(yawY * 0.5f);
    float cx = cosf(pitchX * 0.5f); float sx = sinf(pitchX * 0.5f);

    q[0] = sx * cy * cz - cx * sy * sz;//x
    q[1] = cx * sy * cz + sx * cy * sz;//y
    q[2] = cx * cy * sz - sx * sy * cz;//z
    q[3] = cx * cy * cz + sx * sy * sz;//w
}
////////////////////////////////////////////////////////////////////////////////////////
Transform GetNewTransform(const std::string& device, float px, float py, float pz, float rx, float ry, float rz, float rw) {
    try {
        float device_quat[4] = { rx, ry, rz, rw };
        float q_local_off[4], q_world_off[4], q_playspace[4];

        float ps_yaw = GetFloatFromSettingsByKey(device + " playspace yaw");
        EulerToQuat(0, ps_yaw, 0, q_playspace);

        EulerToQuat(
            GetFloatFromSettingsByKey(device + " offset local roll"),
            GetFloatFromSettingsByKey(device + " offset local yaw"),
            GetFloatFromSettingsByKey(device + " offset local pitch"),
            q_local_off
        );

        EulerToQuat(
            GetFloatFromSettingsByKey(device + " offset world roll"),
            GetFloatFromSettingsByKey(device + " offset world yaw"),
            GetFloatFromSettingsByKey(device + " offset world pitch"),
            q_world_off
        );

        float offset_local[3] = {
            GetFloatFromSettingsByKey(device + " offset local x"),
            GetFloatFromSettingsByKey(device + " offset local y"),
            GetFloatFromSettingsByKey(device + " offset local z")
        };

        float offset_world[3] = {
            GetFloatFromSettingsByKey(device + " offset world x"),
            GetFloatFromSettingsByKey(device + " offset world y"),
            GetFloatFromSettingsByKey(device + " offset world z")
        };

        float rotated_local[3];
        RotateVector(device_quat, offset_local, rotated_local);

        float mid_px = px + rotated_local[0] + offset_world[0];
        float mid_py = py + rotated_local[1] + offset_world[1];
        float mid_pz = pz + rotated_local[2] + offset_world[2];

        float final_pos[3] = { mid_px, mid_py, mid_pz };
        float final_px, final_py, final_pz;

        float rotated_pos[3];
        RotateVector(q_playspace, final_pos, rotated_pos);
        final_px = rotated_pos[0];
        final_py = rotated_pos[1];
        final_pz = rotated_pos[2];

        float temp_q[4], mid_q[4], final_q[4];

        MultiplyQuat(q_world_off, device_quat, temp_q);
        MultiplyQuat(temp_q, q_local_off, mid_q);
        MultiplyQuat(q_playspace, mid_q, final_q);

        return {
            final_px, final_py, final_pz,
            final_q[0], final_q[1], final_q[2], final_q[3]
        };
    }
    catch (...) {
        return { px, py, pz, rx, ry, rz, rw };
    }
}
////////////////////////////////////////////////////////////////////////////////////////