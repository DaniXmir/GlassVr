#ifndef UDP_TYPES_H
#define UDP_TYPES_H

#pragma pack(push, 1)

struct Packet {
    // --- 9 DOUBLES (HMD Data) ---
    // Corresponds to: 9d
    double hmd_pos_x;
    double hmd_pos_y;
    double hmd_pos_z;

    double hmd_rot_w;
    double hmd_rot_x;
    double hmd_rot_y;
    double hmd_rot_z;

    double hmd_ipd;
    double hmd_head_to_eye_dist;

    // --- 24 FLOATS (Controller Continuous Values) ---
    // Corresponds to: 24f (12 Right + 12 Left)

    // Right Controller (12 floats)
    float cr_pos_x;
    float cr_pos_y;
    float cr_pos_z;
    float cr_rot_x;
    float cr_rot_y;
    float cr_rot_z;
    float cr_rot_w;
    float cr_joy_x;
    float cr_joy_y;
    float cr_touch_x;
    float cr_touch_y;
    float cr_trigger;

    // Left Controller (12 floats)
    float cl_pos_x;
    float cl_pos_y;
    float cl_pos_z;
    float cl_rot_x;
    float cl_rot_y;
    float cl_rot_z;
    float cl_rot_w;
    float cl_joy_x;
    float cl_joy_y;
    float cl_touch_x;
    float cl_touch_y;
    float cl_trigger;

    // --- 10 BOOLEANS (Controller Button States) ---
    // Corresponds to: 10? (5 Right + 5 Left). Python's '?' maps to C 'bool' or a 1-byte integer.
    // Using bool or uint8_t is common; bool is standard C++ for this purpose.

    // Right Controller (5 bools)
    bool cr_joy;
    bool cr_touch;
    bool cr_a;
    bool cr_b;
    bool cr_grip;
    bool cr_menu;

    // Left Controller (5 bools)
    bool cl_joy;
    bool cl_touch;
    bool cl_a;
    bool cl_b;
    bool cl_grip;
    bool cl_menu;
};

#pragma pack(pop)
#endif