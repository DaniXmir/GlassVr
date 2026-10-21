#include "touchcontroller.h"
#include "controllerdata.h"
#include "settings.h"

using namespace vr;

static const char* kControllerType = "oculus_touch";
static const char* kRegisteredLeft = "oculus/oculus_touch_left";
static const char* kRegisteredRight = "oculus/oculus_touch_right";
static const char* kManufacturer = "Oculus";
static const char* kInputProfilePath = "{oculus}/input/touch_profile.json";

static const char* kRenderModelLeft = "oculus_cv1_controller_left";
static const char* kRenderModelRight = "oculus_cv1_controller_right";
static const char* kModelNumberLeft = "Oculus Rift CV1 (Left Controller)";
static const char* kModelNumberRight = "Oculus Rift CV1 (Right Controller)";

CTouchControllerDriver::CTouchControllerDriver(bool right)
    : ControllerBase(right)
{
}

CTouchControllerDriver::~CTouchControllerDriver()
{
}

void CTouchControllerDriver::SetupProperties(PropertyContainerHandle_t c)
{
    VRProperties()->SetStringProperty(c, Prop_ControllerType_String, kControllerType);
    VRProperties()->SetStringProperty(c, Prop_RegisteredDeviceType_String, m_right ? kRegisteredRight : kRegisteredLeft);
    VRProperties()->SetStringProperty(c, Prop_ModelNumber_String, m_right ? kModelNumberRight : kModelNumberLeft);
    VRProperties()->SetStringProperty(c, Prop_ManufacturerName_String, kManufacturer);
    VRProperties()->SetStringProperty(c, Prop_RenderModelName_String, m_right ? kRenderModelRight : kRenderModelLeft);
    VRProperties()->SetStringProperty(c, Prop_InputProfilePath_String, kInputProfilePath);

    VRProperties()->SetInt32Property(c, Prop_ControllerRoleHint_Int32, m_right ? TrackedControllerRole_RightHand : TrackedControllerRole_LeftHand);

    VRProperties()->SetInt32Property(c, Prop_Axis0Type_Int32, k_eControllerAxis_Joystick);
    VRProperties()->SetInt32Property(c, Prop_Axis1Type_Int32, k_eControllerAxis_Trigger);
    VRProperties()->SetInt32Property(c, Prop_Axis2Type_Int32, k_eControllerAxis_Trigger);
}

void CTouchControllerDriver::CreateInputComponents(PropertyContainerHandle_t c)
{
    IVRDriverInput* in = VRDriverInput();

    in->CreateBooleanComponent(c, "/input/joystick/click", &m_h.joyClick);
    in->CreateBooleanComponent(c, "/input/joystick/touch", &m_h.joyTouch);
    in->CreateScalarComponent(c, "/input/joystick/x", &m_h.joyX, VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);
    in->CreateScalarComponent(c, "/input/joystick/y", &m_h.joyY, VRScalarType_Absolute, VRScalarUnits_NormalizedTwoSided);

    in->CreateBooleanComponent(c, "/input/trigger/touch", &m_h.triggerTouch);
    in->CreateScalarComponent(c, "/input/trigger/value", &m_h.triggerValue, VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    in->CreateScalarComponent(c, "/input/grip/value", &m_h.gripValue, VRScalarType_Absolute, VRScalarUnits_NormalizedOneSided);
    in->CreateBooleanComponent(c, "/input/thumbrest/touch", &m_h.thumbrest);

    if (!m_right) {
        in->CreateBooleanComponent(c, "/input/x/click", &m_h.topClick);
        in->CreateBooleanComponent(c, "/input/x/touch", &m_h.topTouch);
        in->CreateBooleanComponent(c, "/input/y/click", &m_h.botClick);
        in->CreateBooleanComponent(c, "/input/y/touch", &m_h.botTouch);

        in->CreateBooleanComponent(c, "/input/menu/click", &m_h.sysClick);
        in->CreateBooleanComponent(c, "/input/system/click", &m_h.sysClick2);
    }
    else {
        in->CreateBooleanComponent(c, "/input/a/click", &m_h.topClick);
        in->CreateBooleanComponent(c, "/input/a/touch", &m_h.topTouch);
        in->CreateBooleanComponent(c, "/input/b/click", &m_h.botClick);
        in->CreateBooleanComponent(c, "/input/b/touch", &m_h.botTouch);
        in->CreateBooleanComponent(c, "/input/system/click", &m_h.sysClick);
    }
}

void CTouchControllerDriver::UpdateInput(const PacketSkeletal& skeletal)
{
    const bool inputUdp = (GetStringFromSettingsByKey(DeviceKey() + "input mode") == "UDP");
    PacketInputTouch input = ControllerDataHub::Get().GetInputTouch(m_right, inputUdp);

    IVRDriverInput* in = VRDriverInput();

    in->UpdateBooleanComponent(m_h.joyClick, input.joy_btn, 0);
    in->UpdateBooleanComponent(m_h.joyTouch, input.joy_cap, 0);
    in->UpdateScalarComponent(m_h.joyX, (float)input.joy_x, 0);
    in->UpdateScalarComponent(m_h.joyY, (float)input.joy_y, 0);

    in->UpdateBooleanComponent(m_h.triggerTouch, input.trigger_cap, 0);
    in->UpdateScalarComponent(m_h.triggerValue, (float)input.trigger, 0);
    in->UpdateScalarComponent(m_h.gripValue, (float)input.grip, 0);

    in->UpdateBooleanComponent(m_h.topClick, input.a_x, 0);
    in->UpdateBooleanComponent(m_h.topTouch, input.a_x_cap, 0);
    in->UpdateBooleanComponent(m_h.botClick, input.b_y, 0);
    in->UpdateBooleanComponent(m_h.botTouch, input.b_y_cap, 0);
    in->UpdateBooleanComponent(m_h.sysClick, input.system, 0);
    if (!m_right)
        in->UpdateBooleanComponent(m_h.sysClick2, input.system, 0);
}