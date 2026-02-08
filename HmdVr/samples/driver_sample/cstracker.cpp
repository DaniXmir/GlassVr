#include "cstracker.h"
#include "settings.h" 
#include "basics.h"
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

    m_bThreadRunning = true;
    m_pPipeThread = new std::thread(&CSampleTracker::PipeThreadThreadEntry, this);

    return VRInitError_None;
}

void CSampleTracker::Deactivate()
{
    m_bThreadRunning = false;
    if (m_hPipe != INVALID_HANDLE_VALUE) {
        CancelIoEx(m_hPipe, NULL);
    }
    if (m_pPipeThread) {
        if (m_pPipeThread->joinable()) m_pPipeThread->join();
        delete m_pPipeThread;
        m_pPipeThread = nullptr;
    }
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
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

vr::DriverPose_t CSampleTracker::GetPose()
{
    UpdateTrackers();

    g_selectedIndex = GetIntFromSettingsByKey(std::to_string(m_nTrackerIndex) + "tracker index");
    std::string device = std::to_string(m_nTrackerIndex) + "tracker";

    vr::DriverPose_t pose = { 0 };
    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = true;
    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    std::string posmode = GetStringFromSettingsByKey(device + "pos mode");
    std::string rotmode = GetStringFromSettingsByKey(device + "rot mode");

    vr::TrackedDevicePose_t rawPoses[vr::k_unMaxTrackedDeviceCount];
    vr::VRServerDriverHost()->GetRawTrackedDevicePoses(0, rawPoses, vr::k_unMaxTrackedDeviceCount);

    //pos here///////////////////////////////////////////////////////
    if (posmode == "redirect") {
        int tracker_pos_idx = GetIntFromSettingsByKey(device + "pos index");

        if (tracker_pos_idx >= 0 && tracker_pos_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_pos_idx].bPoseIsValid)
        {
            auto& m = rawPoses[tracker_pos_idx].mDeviceToAbsoluteTracking;
            vr::HmdQuaternion_t device_rotation = GetRotationFromMatrix(m);

            float offset_local[3] = {
                GetFloatFromSettingsByKey(device + " offset local x"),
                GetFloatFromSettingsByKey(device + " offset local y"),
                GetFloatFromSettingsByKey(device + " offset local z")
            };

            double rotated_local_offset[3];
            RotateVectorByQuat(device_rotation, offset_local, rotated_local_offset);

            float offset_world[3] = {
                GetFloatFromSettingsByKey(device + " offset world x"),
                GetFloatFromSettingsByKey(device + " offset world y"),
                GetFloatFromSettingsByKey(device + " offset world z")
            };

            pose.vecPosition[0] = m.m[0][3] + rotated_local_offset[0] + offset_world[0];
            pose.vecPosition[1] = m.m[1][3] + rotated_local_offset[1] + offset_world[1];
            pose.vecPosition[2] = m.m[2][3] + rotated_local_offset[2] + offset_world[2];

            pose.vecVelocity[0] = rawPoses[tracker_pos_idx].vVelocity.v[0];
            pose.vecVelocity[1] = rawPoses[tracker_pos_idx].vVelocity.v[1];
            pose.vecVelocity[2] = rawPoses[tracker_pos_idx].vVelocity.v[2];
        }
        else {
            pose.vecPosition[0] = 0.0f;
            pose.vecPosition[1] = 0.0f;
            pose.vecPosition[2] = 0.0f;
        }
    }
    else if (posmode == "test") {
        //
    }
    else {
        pose.vecPosition[0] = m_poseDataCache.pos_x;
        pose.vecPosition[1] = m_poseDataCache.pos_y;
        pose.vecPosition[2] = m_poseDataCache.pos_z;
    }

    //rot here///////////////////////////////////////////////////////
    if (rotmode == "redirect") {
        int tracker_rot_idx = GetIntFromSettingsByKey(device + "rot index");

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

            vr::HmdQuaternion_t combined = QuatMul(offset_world_rotation, device_rotation);
            pose.qRotation = QuatMul(combined, offset_local_rotation);

            pose.vecAngularVelocity[0] = rawPoses[tracker_rot_idx].vAngularVelocity.v[0];
            pose.vecAngularVelocity[1] = rawPoses[tracker_rot_idx].vAngularVelocity.v[1];
            pose.vecAngularVelocity[2] = rawPoses[tracker_rot_idx].vAngularVelocity.v[2];
        }
        else {
            pose.qRotation.w = 1.0f;
            pose.qRotation.x = 0.0f;
            pose.qRotation.y = 0.0f;
            pose.qRotation.z = 0.0f;
        }
    }
    else if (rotmode == "test") {
        //
    }
    else {
        pose.qRotation.w = m_poseDataCache.rot_w;
        pose.qRotation.x = m_poseDataCache.rot_x;
        pose.qRotation.y = m_poseDataCache.rot_y;
        pose.qRotation.z = m_poseDataCache.rot_z;
    }

    pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");

    std::lock_guard<std::mutex> lock(m_poseMutex);
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
    return "TRK" + std::to_string(m_nTrackerIndex) + "Serial";
}

void CSampleTracker::UpdateData(const PacketTracker& data)
{
    m_poseDataCache = data;
}

void CSampleTracker::PipeThreadThreadEntry()
{
    std::string pipeName = "\\\\.\\pipe\\GlassVR_Tracker_" + std::to_string(m_nTrackerIndex);

    while (m_bThreadRunning)
    {
        m_hPipe = CreateFileA(pipeName.c_str(), GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);

        if (m_hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        PacketTracker incomingData;
        DWORD bytesRead;
        while (m_bThreadRunning)
        {
            bool bSuccess = ReadFile(m_hPipe, &incomingData, sizeof(PacketTracker), &bytesRead, NULL);

            if (bSuccess && bytesRead == sizeof(PacketTracker)) {
                std::lock_guard<std::mutex> lock(m_poseMutex);
                m_poseDataCache = incomingData;
            }
            else {
                break;
            }
        }
        CloseHandle(m_hPipe);
        m_hPipe = INVALID_HANDLE_VALUE;
    }
}