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

//Packet m_poseDataCache = { 0 };

void CSampleDeviceDriver::UpdateData(const Packet& data)
{
    m_poseDataCache = data;
}

CSampleDeviceDriver::CSampleDeviceDriver()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

    m_poseDataCache.hmd_rot_w = 1.0;

    m_flIPD = vr::VRSettings()->GetFloat(k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float);

    m_poseDataCache.hmd_ipd = m_flIPD;
    m_poseDataCache.hmd_head_to_eye_dist = 0.0;

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
        m_nRenderWidth = (uint32_t)(ResolutionX * 2);
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

    return VRInitError_None;
}

void CSampleDeviceDriver::Deactivate()
{
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
    *pnWidth = Stereoscopic ? (m_nWindowWidth / 2) : m_nWindowWidth;

    if (eEye == Eye_Left)
    {
        *pnX = m_nWindowX;
    }
    else
    {
        *pnX = Stereoscopic ? (m_nWindowX + m_nWindowWidth / 2) : m_nWindowX;
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

vr::DriverPose_t CSampleDeviceDriver::GetHeadFromEyePose(EVREye eEye)
{
    vr::DriverPose_t pose = { 0 };
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    float fHalfIPD = m_flIPD / 2.0f;

    if (eEye == vr::Eye_Left)
    {
        pose.vecPosition[0] = -fHalfIPD;
    }
    else
    {
        pose.vecPosition[0] = fHalfIPD;
    }

    pose.vecPosition[1] = 0.0f;
    pose.vecPosition[2] = 0.0f;

    return pose;
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

vr::DriverPose_t CSampleDeviceDriver::GetPose()
{
    vr::DriverPose_t pose = { 0 };

    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = true;

    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    pose.vecPosition[0] = m_poseDataCache.hmd_pos_x;
    pose.vecPosition[1] = m_poseDataCache.hmd_pos_y;
    pose.vecPosition[2] = m_poseDataCache.hmd_pos_z;

    pose.qRotation.w = m_poseDataCache.hmd_rot_w;
    pose.qRotation.x = m_poseDataCache.hmd_rot_x;
    pose.qRotation.y = m_poseDataCache.hmd_rot_y;
    pose.qRotation.z = m_poseDataCache.hmd_rot_z;

    return pose;
}

void CSampleDeviceDriver::RunFrame()
{
    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));

        m_flIPD = (float)m_poseDataCache.hmd_ipd;
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserIpdMeters_Float,
            m_flIPD
        );
        HeadToEyeDist = (float)m_poseDataCache.hmd_head_to_eye_dist;
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserHeadToEyeDepthMeters_Float,
            HeadToEyeDist
        );
    }
}