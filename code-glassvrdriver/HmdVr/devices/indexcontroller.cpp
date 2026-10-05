//TODO: add vive/oculus/frame compatibility
#include "indexcontroller.h"
#include "settings.h"
#include "globals.h"
#include <math.h>
#include <string>

#define DEG_TO_RAD(x) ((x) * (3.14159265358979f / 180.f))

using namespace vr;

static HmdQuaternion_t HmdQuaternion_Init(double w, double x, double y, double z)
{
    HmdQuaternion_t quat;
    quat.w = w;
    quat.x = x;
    quat.y = y;
    quat.z = z;
    return quat;
}

CSampleControllerDriver::CSampleControllerDriver()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;
    m_compHaptic = vr::k_ulInvalidInputComponentHandle;
    m_HSkeletal = vr::k_ulInvalidInputComponentHandle;

    for (int i = 0; i < 13; i++) {
        m_HButtons[i] = vr::k_ulInvalidInputComponentHandle;
    }
    for (int i = 0; i < 12; i++) {
        m_HAnalog[i] = vr::k_ulInvalidInputComponentHandle;
    }

    right = 0;
}

void CSampleControllerDriver::SetControllerIndex(int32_t CtrlIndex)
{
    right = CtrlIndex;
}

CSampleControllerDriver::~CSampleControllerDriver()
{
}

vr::EVRInitError CSampleControllerDriver::Activate(vr::TrackedDeviceIndex_t unObjectId)
{
    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ControllerType_String, "knuckles");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ModelNumber_String, "Knuckles EV3.0");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ManufacturerName_String, "Valve");
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, vr::Prop_WillDriftInYaw_Bool, false);
    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_DeviceClass_Int32, vr::TrackedDeviceClass_Controller);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_RenderModelName_String,
        right ? "{indexcontroller}valve_controller_knu_1_0_right" : "{indexcontroller}valve_controller_knu_1_0_left");

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_SerialNumber_String, GetSerialNumber().c_str());
    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_ControllerRoleHint_Int32,
        right ? vr::TrackedControllerRole_RightHand : vr::TrackedControllerRole_LeftHand);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_InputProfilePath_String, "{indexcontroller}/input/index_controller_profile.json");

    //buttons etc
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/a/click", &m_HButtons[0]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/b/click", &m_HButtons[1]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/click", &m_HButtons[2]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/thumbstick/click", &m_HButtons[7]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trigger/click", &m_HButtons[4]);

    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/a/touch", &m_HButtons[9]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/b/touch", &m_HButtons[10]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/touch", &m_HButtons[3]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/thumbstick/touch", &m_HButtons[8]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trigger/touch", &m_HButtons[12]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trackpad/touch", &m_HButtons[5]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/grip/touch", &m_HButtons[6]);

    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/thumbstick/x", &m_HAnalog[0], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/thumbstick/y", &m_HAnalog[1], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/x", &m_HAnalog[3], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/y", &m_HAnalog[4], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trigger/value", &m_HAnalog[2], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/force", &m_HAnalog[5], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/grip/value", &m_HAnalog[7], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/grip/force", &m_HAnalog[6], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);

    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/index", &m_HAnalog[8], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/middle", &m_HAnalog[9], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/ring", &m_HAnalog[10], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/pinky", &m_HAnalog[11], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    //buttons etc

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_Axis0Type_Int32, vr::k_eControllerAxis_Joystick);

    if (right == false) {
        vr::VRDriverInput()->CreateSkeletonComponent(
            m_ulPropertyContainer,
            "/input/skeleton/left",
            "/skeleton/hand/left",
            "/pose/raw",
            vr::VRSkeletalTracking_Full,
            nullptr,
            0U,
            &m_HSkeletal
        );
    }
    else {
        vr::VRDriverInput()->CreateSkeletonComponent(
            m_ulPropertyContainer,
            "/input/skeleton/right",
            "/skeleton/hand/right",
            "/pose/raw",
            vr::VRSkeletalTracking_Full,
            nullptr,
            0U,
            &m_HSkeletal
        );
    }

    vr::VRDriverInput()->CreateHapticComponent(m_ulPropertyContainer, "/output/haptic", &m_compHaptic);

    //connections
    if (right) {
        m_comm.AddUDP(GetIntFromSettingsByKey("cr port"));
    }
    else {
        m_comm.AddUDP(GetIntFromSettingsByKey("cl port"));
    }

    std::string side = right ? "RIGHT" : "LEFT";
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_CONTROLLER_" + side + "_Pos");
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_CONTROLLER_" + side + "_Rot");
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_CONTROLLER_" + side + "_Input");
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_CONTROLLER_" + side + "_Skeletal");
    //connections

    return VRInitError_None;
}

void CSampleControllerDriver::Deactivate()
{
    m_comm.StopAll();
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
}

void CSampleControllerDriver::EnterStandby()
{
}

void* CSampleControllerDriver::GetComponent(const char* pchComponentNameAndVersion)
{
    return NULL;
}

void CSampleControllerDriver::PowerOff()
{
}

void CSampleControllerDriver::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {
        pchResponseBuffer[0] = 0;
    }
}

//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
static uint32_t g_foundTrackers[vr::k_unMaxTrackedDeviceCount];
static uint32_t g_trackerCount = 0;
static int g_selectedIndex = 0;

static void UpdateTrackers() {
    g_trackerCount = 0;
    for (uint32_t i = 0; i < vr::k_unMaxTrackedDeviceCount; i++) {
        g_foundTrackers[g_trackerCount] = i;
        g_trackerCount++;
    }
}

static vr::HmdQuaternion_t GetRotationFromMatrix(const vr::HmdMatrix34_t& matrix) {
    vr::HmdQuaternion_t q;
    q.w = sqrt(fmax(0, 1 + matrix.m[0][0] + matrix.m[1][1] + matrix.m[2][2])) / 2;
    q.x = sqrt(fmax(0, 1 + matrix.m[0][0] - matrix.m[1][1] - matrix.m[2][2])) / 2;
    q.y = sqrt(fmax(0, 1 - matrix.m[0][0] + matrix.m[1][1] - matrix.m[2][2])) / 2;
    q.z = sqrt(fmax(0, 1 - matrix.m[0][0] - matrix.m[1][1] + matrix.m[2][2])) / 2;
    q.x = _copysign(q.x, matrix.m[2][1] - matrix.m[1][2]);
    q.y = _copysign(q.y, matrix.m[0][2] - matrix.m[2][0]);
    q.z = _copysign(q.z, matrix.m[1][0] - matrix.m[0][1]);
    return q;
}

static void RotateVectorByQuat(const vr::HmdQuaternion_t& q, const float vIn[3], double vOut[3]) {
    float x = q.x, y = q.y, z = q.z, w = q.w;
    float vx = vIn[0], vy = vIn[1], vz = vIn[2];

    vOut[0] = vx * (1 - 2 * y * y - 2 * z * z) + vy * (2 * x * y - 2 * w * z) + vz * (2 * x * z + 2 * w * y);
    vOut[1] = vx * (2 * x * y + 2 * w * z) + vy * (1 - 2 * x * x - 2 * z * z) + vz * (2 * y * z - 2 * w * x);
    vOut[2] = vx * (2 * x * z - 2 * w * y) + vy * (2 * y * z + 2 * w * x) + vz * (1 - 2 * x * x - 2 * y * y);
}

static vr::HmdQuaternion_t QuatMul(const vr::HmdQuaternion_t& q, const vr::HmdQuaternion_t& r) {
    vr::HmdQuaternion_t res;
    res.w = q.w * r.w - q.x * r.x - q.y * r.y - q.z * r.z;
    res.x = q.w * r.x + q.x * r.w + q.y * r.z - q.z * r.y;
    res.y = q.w * r.y - q.x * r.z + q.y * r.w + q.z * r.x;
    res.z = q.w * r.z + q.x * r.y - q.y * r.x + q.z * r.w;
    return res;
}

static vr::HmdQuaternion_t EulerToQuatZYX(float roll, float yaw, float pitch) {
    float cr = cos(roll * 0.5f);  float sr = sin(roll * 0.5f);
    float cy = cos(yaw * 0.5f);   float sy = sin(yaw * 0.5f);
    float cp = cos(pitch * 0.5f); float sp = sin(pitch * 0.5f);

    vr::HmdQuaternion_t q;
    q.w = cr * cy * cp + sr * sy * sp;
    q.x = cr * cy * sp - sr * sy * cp;
    q.y = cr * sy * cp + sr * cy * sp;
    q.z = sr * cy * cp - cr * sy * sp;
    return q;
}

static int GetTrackerIndexBySerial(const std::string& targetSerial) {
    if (targetSerial.empty()) return -1;

    for (uint32_t i = 0; i < vr::k_unMaxTrackedDeviceCount; i++) {
        vr::PropertyContainerHandle_t container = vr::VRProperties()->TrackedDeviceToPropertyContainer(i);
        if (container == vr::k_ulInvalidPropertyContainer) continue;

        char serialBuf[256];
        vr::ETrackedPropertyError err;
        vr::VRProperties()->GetStringProperty(container, vr::Prop_SerialNumber_String, serialBuf, sizeof(serialBuf), &err);

        if (err == vr::TrackedProp_Success && targetSerial == serialBuf) {
            return (int)i;
        }
    }
    return -1;
}

vr::DriverPose_t CSampleControllerDriver::GetPose()
{
    UpdateTrackers();
    std::string device = right ? "cr" : "cl";

    vr::DriverPose_t pose = { 0 };
    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = right ? GetBoolFromSettingsByKey("enable cr") : GetBoolFromSettingsByKey("enable cl");
    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    std::string posmode = GetStringFromSettingsByKey(device + "pos mode");
    std::string rotmode = GetStringFromSettingsByKey(device + "rot mode");

    vr::TrackedDevicePose_t rawPoses[vr::k_unMaxTrackedDeviceCount];
    vr::VRServerDriverHost()->GetRawTrackedDevicePoses(0, rawPoses, vr::k_unMaxTrackedDeviceCount);

    //connections
    udp_pos = m_comm.GetUdpPos();
    udp_rot = m_comm.GetUdpRot();

    pipe_pos = m_comm.GetPipePos();
    pipe_rot = m_comm.GetPipeRot();
    //connections

    float raw_px = 0.0f, raw_py = 0.0f, raw_pz = 0.0f;
    float raw_rx = 0.0f, raw_ry = 0.0f, raw_rz = 0.0f, raw_rw = 1.0f;

    //pos here///////////////////////////////////////////////////////
    if (posmode == "copy") {
        std::string targetSerial = GetStringFromSettingsByKey(device + "pos copy serial");
        int tracker_pos_idx = GetTrackerIndexBySerial(targetSerial);

        if (tracker_pos_idx >= 0 && tracker_pos_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_pos_idx].bPoseIsValid)
        {
            auto& m = rawPoses[tracker_pos_idx].mDeviceToAbsoluteTracking;

            raw_px = m.m[0][3];
            raw_py = m.m[1][3];
            raw_pz = m.m[2][3];

            pose.vecVelocity[0] = rawPoses[tracker_pos_idx].vVelocity.v[0];
            pose.vecVelocity[1] = rawPoses[tracker_pos_idx].vVelocity.v[1];
            pose.vecVelocity[2] = rawPoses[tracker_pos_idx].vVelocity.v[2];
        }
    }
    else if (posmode == "offsets") {
    }
    else if (posmode == "test") {
        //
    }
    else if (posmode == "UDP") {
        raw_px = udp_pos.x;
        raw_py = udp_pos.y;
        raw_pz = udp_pos.z;
    }
    else {
        raw_px = pipe_pos.x;
        raw_py = pipe_pos.y;
        raw_pz = pipe_pos.z;
    }

    //rot here///////////////////////////////////////////////////////
    if (rotmode == "copy") {
        std::string targetRotSerial = GetStringFromSettingsByKey(device + "rot copy serial");
        int tracker_rot_idx = GetTrackerIndexBySerial(targetRotSerial);

        if (tracker_rot_idx >= 0 && tracker_rot_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_rot_idx].bPoseIsValid)
        {
            auto& m = rawPoses[tracker_rot_idx].mDeviceToAbsoluteTracking;
            vr::HmdQuaternion_t device_rotation = GetRotationFromMatrix(m);

            vr::HmdQuaternion_t offset_local_rotation = EulerToQuatZYX(
                GetFloatFromSettingsByKey(device + " offset local roll"),
                GetFloatFromSettingsByKey(device + " offset local yaw"),
                GetFloatFromSettingsByKey(device + " offset local pitch")
            );

            vr::HmdQuaternion_t offset_world_rotation = EulerToQuatZYX(
                GetFloatFromSettingsByKey(device + " offset world roll"),
                GetFloatFromSettingsByKey(device + " offset world yaw"),
                GetFloatFromSettingsByKey(device + " offset world pitch")
            );

            raw_rx = (float)device_rotation.x;
            raw_ry = (float)device_rotation.y;
            raw_rz = (float)device_rotation.z;
            raw_rw = (float)device_rotation.w;

            pose.vecAngularVelocity[0] = rawPoses[tracker_rot_idx].vAngularVelocity.v[0];
            pose.vecAngularVelocity[1] = rawPoses[tracker_rot_idx].vAngularVelocity.v[1];
            pose.vecAngularVelocity[2] = rawPoses[tracker_rot_idx].vAngularVelocity.v[2];
        }
    }
    else if (rotmode == "offsets") {
    }
    else if (rotmode == "test") {
        //
    }
    else if (rotmode == "UDP") {
        raw_rx = udp_rot.x;
        raw_ry = udp_rot.y;
        raw_rz = udp_rot.z;
        raw_rw = udp_rot.w;
    }
    else {
        raw_rx = pipe_rot.x;
        raw_ry = pipe_rot.y;
        raw_rz = pipe_rot.z;
        raw_rw = pipe_rot.w;
    }

    Transform FinalTransform = GetNewTransform(device, raw_px, raw_py, raw_pz, raw_rx, raw_ry, raw_rz, raw_rw);

    pose.vecPosition[0] = FinalTransform.pos_x;
    pose.vecPosition[1] = FinalTransform.pos_y;
    pose.vecPosition[2] = FinalTransform.pos_z;

    pose.qRotation.w = FinalTransform.rot_w;
    pose.qRotation.x = FinalTransform.rot_x;
    pose.qRotation.y = FinalTransform.rot_y;
    pose.qRotation.z = FinalTransform.rot_z;

    pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");

    return pose;
}
//pos here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void CSampleControllerDriver::UpdateSkeletalInput(PacketSkeletal& packet)
{
    vr::VRBoneTransform_t boneTransforms[31];

    MyFingerCurls curls = {
        (float)packet.flexions[0],//thumb
        (float)packet.flexions[4],//index
        (float)packet.flexions[8],//middle
        (float)packet.flexions[12],//ring
        (float)packet.flexions[16]//pinky
    };

    MyFingerSplays splays = {
        (float)packet.splays[0],
        (float)packet.splays[1],
        (float)packet.splays[2],
        (float)packet.splays[3],
        (float)packet.splays[4]
    };

    vr::ETrackedControllerRole role = (right == 1)
        ? vr::TrackedControllerRole_RightHand
        : vr::TrackedControllerRole_LeftHand;

    m_handSimulation.ComputeSkeletonTransforms(role, curls, splays, boneTransforms);

    vr::VRDriverInput()->UpdateSkeletonComponent(
        m_HSkeletal, vr::VRSkeletalMotionRange_WithController, boneTransforms, 31);
    vr::VRDriverInput()->UpdateSkeletonComponent(
        m_HSkeletal, vr::VRSkeletalMotionRange_WithoutController, boneTransforms, 31);
}

void CSampleControllerDriver::RunFrame()
{
    std::string device = right ? "cr" : "cl";
    std::string InputMode = GetStringFromSettingsByKey(device + "input mode");
    std::string SkeletalMode = GetStringFromSettingsByKey(device + "skeletal mode");

    PacketInputIndex input = {};
    PacketSkeletal skeletal = {};

    if (InputMode == "UDP") {
        input = m_comm.GetUdpInput();
    }
    else {
        input = m_comm.GetPipeInput();
    }

    if (SkeletalMode == "UDP") {
        skeletal = m_comm.GetUdpSkeletal();
    }
    else {
        skeletal = m_comm.GetPipeSkeletal();
    }

    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[0], input.a, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[1], input.b, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[2], input.system, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[7], input.joy_btn, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[4], input.trigger_btn, 0);

    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[9], input.a_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[10], input.b_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[3], input.system_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[8], input.joy_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[12], input.trigger_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[5], input.touch_cap, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[6], input.grip_cap, 0);

    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[0], input.joy_x, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[1], input.joy_y, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[3], input.touch_x, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[4], input.touch_y, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[2], input.trigger, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[5], input.touch_force, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[7], input.grip_pull, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[6], input.grip_force, 0);

    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[8], (float)skeletal.flexions[4], 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[9], (float)skeletal.flexions[8], 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[10], (float)skeletal.flexions[12], 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[11], (float)skeletal.flexions[16], 0);

    UpdateSkeletalInput(skeletal);

    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        if (right) g_selectedIndex = GetIntFromSettingsByKey("cr index");
        else       g_selectedIndex = GetIntFromSettingsByKey("cl index");
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
}

void CSampleControllerDriver::ProcessEvent(const vr::VREvent_t& vrEvent)
{
    switch (vrEvent.eventType) {
    case vr::VREvent_Input_HapticVibration:
        if (vrEvent.data.hapticVibration.componentHandle == m_compHaptic) {
        }
        break;
    }
}

std::string CSampleControllerDriver::GetSerialNumber() const
{
    switch (right) {
    case false:
        return "GlassVRConLeft";
    case true:
        return "GlassVRConRight";
    default:
        return "GlassVRCon";
    }
}