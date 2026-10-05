#include "tracker.h"
#include "settings.h" 
#include "basics.h"
#include "globals.h"
#include <math.h>

using namespace vr;

CSampleTracker::CSampleTracker()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;
    m_nTrackerIndex = 0;
}

void CSampleTracker::SetTrackerIndex(int32_t TrackerIndex)
{
    m_nTrackerIndex = TrackerIndex;
}

CSampleTracker::~CSampleTracker()
{
}

vr::EVRInitError CSampleTracker::Activate(vr::TrackedDeviceIndex_t unObjectId)
{
    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, Prop_DeviceClass_Int32, TrackedDeviceClass_GenericTracker);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ModelNumber_String, "Vive Tracker");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ManufacturerName_String, "HTC");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_RenderModelName_String, "{htc}vr_tracker_vive_1_0");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ControllerType_String, "vive_tracker");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_TrackingSystemName_String, "VR Tracker");

    std::string Serial = GetSerialNumber();
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_SerialNumber_String, Serial.c_str());

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, Prop_ControllerRoleHint_Int32, TrackedControllerRole_OptOut);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_InputProfilePath_String, "{htc}/input/vive_tracker_profile.json");

    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/click", &m_hSystemButton);

    //connections
    m_comm.AddUDP(GetIntFromSettingsByKey(std::to_string(m_nTrackerIndex) + "tracker port"));

    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_TRACKER_" + std::to_string(m_nTrackerIndex) + "_Pos");
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_TRACKER_" + std::to_string(m_nTrackerIndex) + "_Rot");
    //connections

    return VRInitError_None;
}

void CSampleTracker::Deactivate()
{
    m_comm.StopAll();
}

void CSampleTracker::EnterStandby() {}

void* CSampleTracker::GetComponent(const char* pchComponentNameAndVersion)
{
    return NULL;
}

void CSampleTracker::PowerOff() {}

void CSampleTracker::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) pchResponseBuffer[0] = 0;
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

vr::DriverPose_t CSampleTracker::GetPose()
{
    UpdateTrackers();

    g_selectedIndex = GetIntFromSettingsByKey(std::to_string(m_nTrackerIndex) + "tracker index");
    std::string device = std::to_string(m_nTrackerIndex) + "tracker";

    vr::DriverPose_t pose = { 0 };

    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    //pose.deviceIsConnected = true;
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

    bool trackerEnabled = (m_nTrackerIndex < GetIntFromSettingsByKey("trackers num"));

    //enable state (trackers num) + bad apple///////////////////////////
    if (rotmode == "bad apple") {
        pose.deviceIsConnected = trackerEnabled && (pipe_rot.x != 0.0);
    }
    else {
        pose.deviceIsConnected = trackerEnabled;
    }

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
//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void CSampleTracker::RunFrame()
{
#if defined(_WINDOWS)
    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
#endif
}

void CSampleTracker::ProcessEvent(const vr::VREvent_t& vrEvent)
{

}

std::string CSampleTracker::GetSerialNumber() const
{
    return "GlassVRTrk" + std::to_string(m_nTrackerIndex);
}