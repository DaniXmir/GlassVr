//idc anymore, ai is stupid
#ifndef PACKETS_H
#define PACKETS_H

#pragma pack(push, 1)

// position
struct PacketPos {
    double x;
    double y;
    double z;
};

//rotation
struct PacketRot {
    double w;
    double x;
    double y;
    double z;
};

// valve index
struct PacketInputIndex {
    bool a;
    bool b;
    bool system;
    bool joy_btn;
    bool trigger_btn;

    bool a_cap;
    bool b_cap;
    bool system_cap;
    bool joy_cap;
    bool trigger_cap;
    bool touch_cap;
    bool grip_cap;

    double joy_x, joy_y;
    double touch_x, touch_y;
    double trigger;

    double touch_force;
    double grip_pull;
    double grip_force;
};

// steam frame
struct PacketInputFrame {
    bool y_up, y_up_cap;
    bool a_down, a_down_cap;
    bool x_left, x_left_cap;
    bool b_right, b_right_cap;
    bool select, select_cap;

    // both hands
    bool bumper, bumper_cap;
    bool system, system_cap;
    bool trigger_btn, trigger_cap;
    bool grip_btn, grip_cap;
    bool joy_btn, joy_cap;

    double trigger;   // 0..1
    double grip;      // 0..1
    double joy_x;    // -1..1
    double joy_y;    // -1..1
};

// htc vive wand
struct PacketInputVive {
    bool system;
    bool grip_btn;              // click only, no analog value
    bool select;
    bool trigger_btn;
    bool touch_btn;
    bool touch_cap;

    double trigger;         // 0..1
    double touch_x;            // -1..1
    double touch_y;            // -1..1
};

// oculus touch
struct PacketInputTouch {
    bool system;
    bool a_x, a_x_cap;      // X (left) / A (right)
    bool b_y, b_y_cap;  // Y (left) / B (right)
    bool trigger_cap;                     // no trigger click i think
    bool joy_btn, joy_cap;

    double trigger;   // 0..1
    double grip;      // 0..1 (no grip click / touch in the profile)
    double joy_x;      // -1..1
    double joy_y;      // -1..1
};

// skeletal
struct PacketSkeletal {
    double flexions[20];
    double splays[5];
};

// extra, only used with udp
struct PacketExtra {
    bool reset;
};

#pragma pack(pop)

#endif