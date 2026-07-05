#ifndef PACKETS_H
#define PACKETS_H

#pragma pack(push, 1)

struct PacketPos {
    double x;
    double y;
    double z;
};

struct PacketRot {
    double w;
    double x;
    double y;
    double z;
};

//struct PacketInputVive {
// fun fact: og htc vive wands are the only controllers that have clickable grips /input/grip/click
// thay are also the only ones to have a clickable touchpad /input/trackpad/click
//};


//struct PacketInputTouch {
// 
//};

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

//struct PacketInputFrame {
// 
//};

struct PacketSkeletal {
    double flexions[20];
    double splays[5];
};

struct PacketExtra {
    bool reset;
};

#pragma pack(pop)

#endif