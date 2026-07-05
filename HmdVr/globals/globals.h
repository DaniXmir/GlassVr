#pragma once
#include <string>

struct Transform {
    float pos_x, pos_y, pos_z;
    float rot_x, rot_y, rot_z, rot_w;
};

Transform GetNewTransform(
    const std::string& device = "hmd",
    float px = 0.0f, float py = 0.0f, float pz = 0.0f,
    float rx = 0.0f, float ry = 0.0f, float rz = 0.0f, float rw = 1.0f
);

Transform OffsetTransform(
    float px = 0.0f, float py = 0.0f, float pz = 0.0f, float rx = 0.0f, float ry = 0.0f, float rz = 0.0f, float rw = 0.0f,
    float lpx = 0.0f, float lpy = 0.0f, float lpz = 0.0f, float lry = 0.0f, float lrp = 0.0f, float lrr = 0.0f,
    float wpx = 0.0f, float wpy = 0.0f, float wpz = 0.0f, float wry = 0.0f, float wrp = 0.0f, float wrr = 0.0f
);