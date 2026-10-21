#include "framecontroller.h"
#include "settings.h"
#include "controllerinput.h"
#include "controllerdata.h"

#include <string>

using namespace vr;
using namespace controllerinput;

static const char* kControllerType    = "frame_controller";
static const char* kInputProfilePath  = "{frame_controller}/input/frame_controller_profile.json";
static const char* kRenderModelLeft   = "{frame_controller}frame_controller_left";
static const char* kRenderModelRight  = "{frame_controller}frame_controller_right";
static const char* kModelNumberLeft   = "Steam Frame Controller (Left)";
static const char* kModelNumberRight  = "Steam Frame Controller (Right)";


CFrameControllerDriver::CFrameControllerDriver(bool right)
    : ControllerBase(right)
{
}

CFrameControllerDriver::~CFrameControllerDriver()
{
}

void CFrameControllerDriver::SetupProperties(PropertyContainerHandle_t c)
{
    VRProperties()->SetStringProperty(c, Prop_ControllerType_String, kControllerType);
    VRProperties()->SetStringProperty(c, Prop_ModelNumber_String, m_right ? kModelNumberRight : kModelNumberLeft);
    VRProperties()->SetStringProperty(c, Prop_ManufacturerName_String, "Valve");

    VRProperties()->SetStringProperty(c, Prop_RenderModelName_String, m_right ? kRenderModelRight : kRenderModelLeft);
    VRProperties()->SetStringProperty(c, Prop_InputProfilePath_String, kInputProfilePath);

    VRProperties()->SetInt32Property(c, Prop_Axis0Type_Int32, k_eControllerAxis_Joystick);
}

void CFrameControllerDriver::CreateInputComponents(PropertyContainerHandle_t c)
{
    AddButton(c, "/input/bumper", m_components);
    AddTriggerLike(c, "/input/trigger", m_components);
    AddTriggerLike(c, "/input/grip", m_components);
    AddThumbstick(c, "/input/thumbstick", m_components);

    if (!m_right) {
        AddButton(c, "/input/dpad_up", m_components);
        AddButton(c, "/input/dpad_down", m_components);
        AddButton(c, "/input/dpad_left", m_components);
        AddButton(c, "/input/dpad_right", m_components);
        AddButton(c, "/input/view", m_components);
        AddButton(c, "/input/system", m_components);
    }
    else {
        AddButton(c, "/input/a", m_components);
        AddButton(c, "/input/b", m_components);
        AddButton(c, "/input/x", m_components);
        AddButton(c, "/input/y", m_components);
        AddButton(c, "/input/menu", m_components);
        AddButton(c, "/input/system", m_components);
    }
}

void CFrameControllerDriver::UpdateInput(const PacketSkeletal& skeletal)
{
    const bool inputUdp =
        (GetStringFromSettingsByKey(DeviceKey() + "input mode") == "UDP");

    PacketInputFrame input =
        ControllerDataHub::Get().GetInputFrame(m_right, inputUdp);

    VRDriverInput()->UpdateBooleanComponent(m_components[0], input.bumper, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[1], input.bumper_cap, 0);

    VRDriverInput()->UpdateBooleanComponent(m_components[2], input.trigger_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[3], input.trigger_cap, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[4], (float)input.trigger, 0);

    VRDriverInput()->UpdateBooleanComponent(m_components[5], input.grip_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[6], input.grip_cap, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[7], (float)input.grip, 0);

    VRDriverInput()->UpdateBooleanComponent(m_components[8], input.joy_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[9], input.joy_cap, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[10], (float)input.joy_x, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[11], (float)input.joy_y, 0);

    if (!m_right) {
        VRDriverInput()->UpdateBooleanComponent(m_components[12], input.y_up, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[13], input.y_up_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[14], input.a_down, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[15], input.a_down_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[16], input.x_left, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[17], input.x_left_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[18], input.b_right, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[19], input.b_right_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[20], input.select, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[21], input.select_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[22], input.system, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[23], input.system_cap, 0);
    }
    else {
        VRDriverInput()->UpdateBooleanComponent(m_components[12], input.a_down, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[13], input.a_down_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[14], input.b_right, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[15], input.b_right_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[16], input.x_left, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[17], input.x_left_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[18], input.y_up, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[19], input.y_up_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[20], input.select, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[21], input.select_cap, 0);

        VRDriverInput()->UpdateBooleanComponent(m_components[22], input.system, 0);
        VRDriverInput()->UpdateBooleanComponent(m_components[23], input.system_cap, 0);
    }
}