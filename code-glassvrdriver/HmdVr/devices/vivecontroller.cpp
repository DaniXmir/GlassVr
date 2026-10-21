#include "vivecontroller.h"
#include "controllerinput.h"
#include "controllerdata.h"
#include "settings.h"

using namespace vr;
using namespace controllerinput;

static const char* kControllerType = "vive_controller";
static const char* kRegisteredDeviceType = "htc/vive_controller";
static const char* kModelNumber = "Vive Controller MV";
static const char* kManufacturer = "HTC";
static const char* kRenderModel = "vr_controller_vive_1_5";
static const char* kInputProfilePath = "{htc}/input/vive_controller_profile.json";

CViveControllerDriver::CViveControllerDriver(bool right)
    : ControllerBase(right)
{
}

CViveControllerDriver::~CViveControllerDriver()
{
}

void CViveControllerDriver::SetupProperties(PropertyContainerHandle_t c)
{
    VRProperties()->SetStringProperty(c, Prop_ControllerType_String, kControllerType);
    VRProperties()->SetStringProperty(c, Prop_RegisteredDeviceType_String, kRegisteredDeviceType);
    VRProperties()->SetStringProperty(c, Prop_ModelNumber_String, kModelNumber);
    VRProperties()->SetStringProperty(c, Prop_ManufacturerName_String, kManufacturer);
    VRProperties()->SetStringProperty(c, Prop_RenderModelName_String, kRenderModel);
    VRProperties()->SetStringProperty(c, Prop_InputProfilePath_String, kInputProfilePath);

    VRProperties()->SetInt32Property(c, Prop_ControllerRoleHint_Int32, m_right ? TrackedControllerRole_RightHand : TrackedControllerRole_LeftHand);

    VRProperties()->SetInt32Property(c, Prop_Axis0Type_Int32, k_eControllerAxis_TrackPad);
    VRProperties()->SetInt32Property(c, Prop_Axis1Type_Int32, k_eControllerAxis_Trigger);
}

void CViveControllerDriver::CreateInputComponents(PropertyContainerHandle_t c)
{
    AddClick(c, "/input/application_menu", m_components);
    AddClick(c, "/input/grip", m_components);
    AddClick(c, "/input/system", m_components);

    AddClick(c, "/input/trackpad", m_components);
    AddTouch(c, "/input/trackpad", m_components);
    AddXY(c, "/input/trackpad", m_components);

    AddClick(c, "/input/trigger", m_components);
    AddValue(c, "/input/trigger", m_components);
}

void CViveControllerDriver::UpdateInput(const PacketSkeletal& skeletal)
{
    const bool inputUdp = (GetStringFromSettingsByKey(DeviceKey() + "input mode") == "UDP");
    PacketInputVive input = ControllerDataHub::Get().GetInputVive(m_right, inputUdp);

    VRDriverInput()->UpdateBooleanComponent(m_components[0], input.select, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[1], input.grip_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[2], input.system, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[3], input.touch_btn, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[4], input.touch_cap, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[5], (float)input.touch_x, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[6], (float)input.touch_y, 0);
    VRDriverInput()->UpdateBooleanComponent(m_components[7], input.trigger_btn, 0);
    VRDriverInput()->UpdateScalarComponent(m_components[8], (float)input.trigger, 0);
}