#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include "csampledevicedriver.h"
#include "settings.h" 
#include "basics.h"

#include <math.h>
#include <string>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <limits>
#include <cmath> 
#include <cstring> 
#include <cstdlib>
#include <cstdio>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;
using namespace std;

const float k_fRadFactor = (float)M_PI / 180.0f;

float HeadToEyeDist = 0.0f;
bool Stereoscopic = false;
float ResolutionX = 1920.0f;
float ResolutionY = 1080.0f;
bool FullScreen = false;
float RefreshRate = 90.0f;

void CSampleDeviceDriver::UpdateData(const PacketHmd& data)
{
    m_poseDataCache = data;
}

CSampleDeviceDriver::CSampleDeviceDriver()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

    m_poseDataCache.rot_w = 1.0;

    m_flIPD = vr::VRSettings()->GetFloat(k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float);

    m_poseDataCache.ipd = m_flIPD;
    m_poseDataCache.head_to_eye_dist = 0.0;

    char buf[1024];

    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_SerialNumber_String, buf, sizeof(buf));
    m_sSerialNumber = buf;

    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_ModelNumber_String, buf, sizeof(buf));
    m_sModelNumber = buf;

    m_flSecondsFromVsyncToPhotons = 0.008;
    m_flDisplayFrequency = RefreshRate;
}

CSampleDeviceDriver::~CSampleDeviceDriver()
{
}

EVRInitError CSampleDeviceDriver::Activate(TrackedDeviceIndex_t unObjectId)
{
    Stereoscopic = GetBoolFromSettingsByKey("stereoscopic");
    ResolutionX = GetFloatFromSettingsByKey("resolution x");
    ResolutionY = GetFloatFromSettingsByKey("resolution y");
    FullScreen = GetBoolFromSettingsByKey("fullscreen");
    RefreshRate = GetFloatFromSettingsByKey("refresh rate");
    m_flDisplayFrequency = RefreshRate;

    m_nWindowX = 0;
    m_nWindowY = 0;

    if (Stereoscopic) {
        m_nWindowWidth = (uint32_t)(ResolutionX * 2);
        m_nRenderWidth = (uint32_t)(ResolutionX);
    }
    else {
        m_nWindowWidth = (uint32_t)ResolutionX;
        m_nRenderWidth = (uint32_t)ResolutionX;
    }
    m_nWindowHeight = (uint32_t)ResolutionY;
    m_nRenderHeight = (uint32_t)ResolutionY;

    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_ModelNumber_String, m_sModelNumber.c_str());
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_RenderModelName_String, m_sModelNumber.c_str());
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserIpdMeters_Float, m_flIPD);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, HeadToEyeDist);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons);
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_DisplayDebugMode_Bool, !FullScreen);

    m_bThreadRunning = true;
    m_pPipeThread = new std::thread(&CSampleDeviceDriver::PipeThreadThreadEntry, this);

    return VRInitError_None;
}

void CSampleDeviceDriver::Deactivate()
{
    m_bThreadRunning = false;
    if (m_pPipeThread) {
        m_pPipeThread->join();
        delete m_pPipeThread;
        m_pPipeThread = nullptr;
    }
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
}

void CSampleDeviceDriver::EnterStandby()
{

}

void CSampleDeviceDriver::PowerOff()
{

}

void* CSampleDeviceDriver::GetComponent(const char* pchComponentNameAndVersion)
{
    if (!_stricmp(pchComponentNameAndVersion, vr::IVRDisplayComponent_Version)) {
        return (vr::IVRDisplayComponent*)this;
    }
    return NULL;
}


void CSampleDeviceDriver::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {

        pchResponseBuffer[0] = 0;
    }
}

void CSampleDeviceDriver::GetWindowBounds(int32_t* pnX, int32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnX = m_nWindowX;
    *pnY = m_nWindowY;
    *pnWidth = m_nWindowWidth;
    *pnHeight = m_nWindowHeight;
}

bool CSampleDeviceDriver::IsDisplayOnDesktop()
{
    return !FullScreen;
}

bool CSampleDeviceDriver::IsDisplayRealDisplay()
{
    return false;
}

void CSampleDeviceDriver::GetRecommendedRenderTargetSize(uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnWidth = m_nRenderWidth;
    *pnHeight = m_nRenderHeight;
}

void CSampleDeviceDriver::GetEyeOutputViewport(EVREye eEye, uint32_t* pnX, uint32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnY = m_nWindowY;
    *pnHeight = m_nWindowHeight;

    if (Stereoscopic)
    {
        *pnWidth = m_nWindowWidth / 2;
        if (eEye == Eye_Left)
        {
            *pnX = m_nWindowX;
        }
        else
        {
            *pnX = m_nWindowX + m_nWindowWidth / 2;
        }
    }
    else
    {
        *pnX = m_nWindowX;
        *pnWidth = m_nWindowWidth;
    }
}

void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
{
    float k_fAngleOuterH_Deg = 0.0;
    float k_fAngleInnerH_Deg = 0.0;
    float k_fAngleTopV_Deg = 0.0;
    float k_fAngleBottomV_Deg = 0.0;

    if (Stereoscopic) {
        k_fAngleOuterH_Deg = GetFloatFromSettingsByKey("outer stereo");
        k_fAngleInnerH_Deg = GetFloatFromSettingsByKey("inner stereo");
        k_fAngleTopV_Deg = GetFloatFromSettingsByKey("top stereo");
        k_fAngleBottomV_Deg = GetFloatFromSettingsByKey("bottom stereo");
    }
    else {
        k_fAngleOuterH_Deg = GetFloatFromSettingsByKey("outer mono");
        k_fAngleInnerH_Deg = GetFloatFromSettingsByKey("inner mono");
        k_fAngleTopV_Deg = GetFloatFromSettingsByKey("top mono");
        k_fAngleBottomV_Deg = GetFloatFromSettingsByKey("bottom mono");
    }

    float k_fTangentTopV = std::tan(k_fAngleTopV_Deg * k_fRadFactor);
    float k_fTangentBottomV = std::tan(k_fAngleBottomV_Deg * k_fRadFactor);
    float k_fTangentOuterH = std::tan(k_fAngleOuterH_Deg * k_fRadFactor);
    float k_fTangentInnerH = std::tan(k_fAngleInnerH_Deg * k_fRadFactor);

    *pfTop = -k_fTangentTopV;
    *pfBottom = k_fTangentBottomV;

    if (eEye == vr::Eye_Left)
    {
        *pfLeft = -k_fTangentOuterH;
        *pfRight = k_fTangentInnerH;
    }
    else
    {
        *pfLeft = -k_fTangentInnerH;
        *pfRight = k_fTangentOuterH;
    }
}

vr::HmdMatrix34_t CSampleDeviceDriver::GetEyeToHeadTransform(vr::EVREye eEye)
{
    //test later
    vr::HmdMatrix34_t matrix = {
        1.0f, 0.0f, 0.0f, 0.0f,//x right-left
        0.0f, 1.0f, 0.0f, 0.0f,//y up-down
        0.0f, 0.0f, 1.0f, 0.0f//z forward-back
    };

    float fHalfIPD = m_flIPD / 2.0f;

    if (eEye == vr::Eye_Left)
    {
        matrix.m[0][3] = -fHalfIPD;
    }
    else
    {
        matrix.m[0][3] = fHalfIPD;
    }

    return matrix;
}

vr::DistortionCoordinates_t CSampleDeviceDriver::ComputeDistortion(EVREye eEye, float fU, float fV)
{
    vr::DistortionCoordinates_t coordinates;
    coordinates.rfRed[0] = fU;
    coordinates.rfRed[1] = fV;
    coordinates.rfGreen[0] = fU;
    coordinates.rfGreen[1] = fV;
    coordinates.rfBlue[0] = fU;
    coordinates.rfBlue[1] = fV;
    return coordinates;
}

bool CSampleDeviceDriver::ComputeInverseDistortion(vr::HmdVector2_t* pA, vr::EVREye eEye, uint32_t unElement, float fU, float fV)
{
    pA[unElement].v[0] = fU;
    pA[unElement].v[1] = fV;
    return true;
}

//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
static uint32_t g_foundTrackers[vr::k_unMaxTrackedDeviceCount];
static uint32_t g_trackerCount = 0;
static int g_selectedIndex = 0;//GetIntFromSettingsByKey("hmd index");

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

vr::DriverPose_t CSampleDeviceDriver::GetPose()
{
    UpdateTrackers();

    std::string device = "hmd";

    vr::DriverPose_t pose = { 0 };
    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = true;
    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    bool updateFromServer = GetBoolFromSettingsByKey(device + " update from server");
    if (updateFromServer) {
        pose.vecPosition[0] = m_poseDataCache.pos_x;
        pose.vecPosition[1] = m_poseDataCache.pos_y;
        pose.vecPosition[2] = m_poseDataCache.pos_z;
        if (m_poseDataCache.rot_w == 0 && m_poseDataCache.rot_x == 0) {
            pose.qRotation.w = 1.0;
        }
        else {
            pose.qRotation.w = m_poseDataCache.rot_w;
            pose.qRotation.x = m_poseDataCache.rot_x;
            pose.qRotation.y = m_poseDataCache.rot_y;
            pose.qRotation.z = m_poseDataCache.rot_z;
        }
        return pose;
    }

    int tracker_target_idx = GetIntFromSettingsByKey(device + " index");
    vr::TrackedDevicePose_t rawPoses[vr::k_unMaxTrackedDeviceCount];
    vr::VRServerDriverHost()->GetRawTrackedDevicePoses(0, rawPoses, vr::k_unMaxTrackedDeviceCount);

    if (tracker_target_idx >= 0 && tracker_target_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_target_idx].bPoseIsValid)
    {
        auto& m = rawPoses[tracker_target_idx].mDeviceToAbsoluteTracking;
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

        // Add velocity from raw pose for position prediction
        pose.vecVelocity[0] = rawPoses[tracker_target_idx].vVelocity.v[0];
        pose.vecVelocity[1] = rawPoses[tracker_target_idx].vVelocity.v[1];
        pose.vecVelocity[2] = rawPoses[tracker_target_idx].vVelocity.v[2];

        // Add angular velocity for rotation prediction
        pose.vecAngularVelocity[0] = rawPoses[tracker_target_idx].vAngularVelocity.v[0];
        pose.vecAngularVelocity[1] = rawPoses[tracker_target_idx].vAngularVelocity.v[1];
        pose.vecAngularVelocity[2] = rawPoses[tracker_target_idx].vAngularVelocity.v[2];

        // Enable pose prediction (both position and rotation)
        pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");//0.011; // 11ms prediction (adjust as needed)

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

        return pose;
    }

    pose.vecPosition[0] = m_poseDataCache.pos_x;
    pose.vecPosition[1] = m_poseDataCache.pos_y;
    pose.vecPosition[2] = m_poseDataCache.pos_z;
    pose.qRotation.w = (m_poseDataCache.rot_w == 0) ? 1.0 : m_poseDataCache.rot_w;

    return pose;
}
//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void CSampleDeviceDriver::RunFrame()
{
    g_selectedIndex = GetIntFromSettingsByKey("hmd index");

    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));

        m_flIPD = GetFloatFromSettingsByKey("ipd");//(float)m_poseDataCache.ipd;
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserIpdMeters_Float,
            m_flIPD
        );
        HeadToEyeDist = GetFloatFromSettingsByKey("head to eye dist");//(float)m_poseDataCache.head_to_eye_dist;
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserHeadToEyeDepthMeters_Float,
            HeadToEyeDist
        );
    }
}

void CSampleDeviceDriver::PipeThreadThreadEntry()
{
    while (m_bThreadRunning)
    {
        m_hPipe = CreateFileA(
            "\\\\.\\pipe\\GlassVR_HMD",
            GENERIC_READ,
            0,
            NULL,
            OPEN_EXISTING,
            0,
            NULL);

        if (m_hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
            continue;
        }

        // 2. Read loop
        PacketHmd incomingData;
        DWORD bytesRead;
        while (m_bThreadRunning)
        {
            bool bSuccess = ReadFile(
                m_hPipe,
                &incomingData,
                sizeof(PacketHmd),
                &bytesRead,
                NULL);

            if (bSuccess && bytesRead == sizeof(PacketHmd)) {
                UpdateData(incomingData);
            }
            else {
                break;
            }
        }

        CloseHandle(m_hPipe);
        m_hPipe = INVALID_HANDLE_VALUE;
    }
}