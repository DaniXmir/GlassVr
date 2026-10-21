#include "indexcontroller.h"
#include "controllerdata.h"
#include "settings.h"

#include <string>

using namespace vr;

CSampleControllerDriver::CSampleControllerDriver(bool right)
    : ControllerBase(right)
{
    for (int i = 0; i < 13; i++) {
        m_HButtons[i] = k_ulInvalidInputComponentHandle;
    }
    for (int i = 0; i < 12; i++) {
        m_HAnalog[i] = k_ulInvalidInputComponentHandle;
    }
}

CSampleControllerDriver::~CSampleControllerDriver()
{
}

void CSampleControllerDriver::SetupProperties(PropertyContainerHandle_t c)
{
    VRProperties()->SetStringProperty(c, Prop_ControllerType_String, "knuckles");
    VRProperties()->SetStringProperty(c, Prop_ModelNumber_String, "Knuckles EV3.0");
    VRProperties()->SetStringProperty(c, Prop_ManufacturerName_String, "Valve");

    VRProperties()->SetStringProperty(c, Prop_RenderModelName_String,
        m_right ? "{indexcontroller}valve_controller_knu_1_0_right" : "{indexcontroller}valve_controller_knu_1_0_left");

    VRProperties()->SetStringProperty(c, Prop_InputProfilePath_String, "{indexcontroller}/input/index_controller_profile.json");

    VRProperties()->SetInt32Property(c, Prop_Axis0Type_Int32, k_eControllerAxis_Joystick);
}

void CSampleControllerDriver::CreateInputComponents(PropertyContainerHandle_t c)
{
    VRDriverInput()->CreateBooleanComponent(c, "/input/a/click", &m_HButtons[0]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/b/click", &m_HButtons[1]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/system/click", &m_HButtons[2]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/thumbstick/click", &m_HButtons[7]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/trigger/click", &m_HButtons[4]);

    VRDriverInput()->CreateBooleanComponent(c, "/input/a/touch", &m_HButtons[9]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/b/touch", &m_HButtons[10]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/system/touch", &m_HButtons[3]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/thumbstick/touch", &m_HButtons[8]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/trigger/touch", &m_HButtons[12]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/trackpad/touch", &m_HButtons[5]);
    VRDriverInput()->CreateBooleanComponent(c, "/input/grip/touch", &m_HButtons[6]);

    VRDriverInput()->CreateScalarComponent(c, "/input/thumbstick/x", &m_HAnalog[0], VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/thumbstick/y", &m_HAnalog[1], VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/trackpad/x", &m_HAnalog[3], VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/trackpad/y", &m_HAnalog[4], VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/trigger/value", &m_HAnalog[2], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/trackpad/force", &m_HAnalog[5], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/grip/value", &m_HAnalog[7], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/grip/force", &m_HAnalog[6], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);

    VRDriverInput()->CreateScalarComponent(c, "/input/finger/index", &m_HAnalog[8], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/finger/middle", &m_HAnalog[9], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/finger/ring", &m_HAnalog[10], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    VRDriverInput()->CreateScalarComponent(c, "/input/finger/pinky", &m_HAnalog[11], VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
}

void CSampleControllerDriver::PushInput(const PacketInputIndex& input, const PacketSkeletal& skeletal)
{
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[0], input.a, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[1], input.b, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[2], input.system, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[7], input.joy_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[4], input.trigger_btn, 0);

    VRDriverInput()->UpdateBooleanComponent(m_HButtons[9], input.a_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[10], input.b_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[3], input.system_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[8], input.joy_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[12], input.trigger_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[5], input.touch_cap, 0);
    VRDriverInput()->UpdateBooleanComponent(m_HButtons[6], input.grip_cap, 0);

    VRDriverInput()->UpdateScalarComponent(m_HAnalog[0], (float)input.joy_x, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[1], (float)input.joy_y, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[3], (float)input.touch_x, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[4], (float)input.touch_y, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[2], (float)input.trigger, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[5], (float)input.touch_force, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[7], (float)input.grip_pull, 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[6], (float)input.grip_force, 0);

    VRDriverInput()->UpdateScalarComponent(m_HAnalog[8], (float)skeletal.flexions[4], 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[9], (float)skeletal.flexions[8], 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[10], (float)skeletal.flexions[12], 0);
    VRDriverInput()->UpdateScalarComponent(m_HAnalog[11], (float)skeletal.flexions[16], 0);
}

void CSampleControllerDriver::UpdateInput(const PacketSkeletal& skeletal)
{
    const bool inputUdp = (GetStringFromSettingsByKey(DeviceKey() + "input mode") == "UDP");
    PacketInputIndex input = ControllerDataHub::Get().GetInputIndex(m_right, inputUdp);
    PushInput(input, skeletal);
}

void CSampleControllerDriver::OnDisable()
{
    PacketInputIndex zeroInput = {};
    PacketSkeletal zeroSkeletal = {};
    PushInput(zeroInput, zeroSkeletal);
}
