#include "csampledevicedriver.h"

#include "basics.h"

#include <math.h>

#include <windows.h>

#include <string>

#include <iostream>

#include <algorithm>

using namespace vr;

struct SharedPoseData {
    double pos_x;
    double pos_y;
    double pos_z;
    double rot_w;
    double rot_x;
    double rot_y;
    double rot_z;
};

const wchar_t* SHM_NAME = L"GlassVrSHM";

HANDLE hMapFile = NULL;
SharedPoseData* pSharedData = NULL;
ULONGLONG g_lastAttemptTick = 0;

bool TryConnectSharedMemory() {

    if (pSharedData != NULL) {
        return true;
    }

    hMapFile = OpenFileMappingW(FILE_MAP_READ, FALSE, SHM_NAME);


    if (hMapFile == NULL) {
        return false;
    }

    pSharedData = (SharedPoseData*)MapViewOfFile(hMapFile, FILE_MAP_READ, 0, 0, sizeof(SharedPoseData));


    if (pSharedData == NULL) {
        CloseHandle(hMapFile);
        hMapFile = NULL;

        return false;

    }

    return true;

}

void CleanupSharedMemory() {
    if (pSharedData != NULL) {
        UnmapViewOfFile(pSharedData);

        pSharedData = NULL;

    }

    if (hMapFile != NULL) {
        CloseHandle(hMapFile);

        hMapFile = NULL;

    }

}

double GetValuseFor(std::string key) {

    if (pSharedData == NULL) return 0.0;

    if (key == "position x") return pSharedData->pos_x;
    if (key == "position y") return pSharedData->pos_y;
    if (key == "position z") return pSharedData->pos_z;

    if (key == "rotation w") return pSharedData->rot_w;
    if (key == "rotation x") return pSharedData->rot_x;
    if (key == "rotation y") return pSharedData->rot_y;
    if (key == "rotation z") return pSharedData->rot_z;


    return 0.0;
}

CSampleDeviceDriver::CSampleDeviceDriver()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

    m_flIPD = vr::VRSettings()->GetFloat(k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float);

    char buf[1024];

    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_SerialNumber_String, buf, sizeof(buf));
    m_sSerialNumber = buf;


    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_ModelNumber_String, buf, sizeof(buf));
    m_sModelNumber = buf;

    m_nWindowX = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowX_Int32);
    m_nWindowY = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowY_Int32);
    m_nWindowWidth = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowWidth_Int32);
    m_nWindowHeight = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowHeight_Int32);
    m_nRenderWidth = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_RenderWidth_Int32);
    m_nRenderHeight = vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_RenderHeight_Int32);
    m_flSecondsFromVsyncToPhotons = vr::VRSettings()->GetFloat(k_pch_Sample_Section, k_pch_Sample_SecondsFromVsyncToPhotons_Float);
    m_flDisplayFrequency = vr::VRSettings()->GetFloat(k_pch_Sample_Section, k_pch_Sample_DisplayFrequency_Float);
}

CSampleDeviceDriver::~CSampleDeviceDriver()
{

}

EVRInitError CSampleDeviceDriver::Activate(TrackedDeviceIndex_t unObjectId)
{
    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_ModelNumber_String, m_sModelNumber.c_str());
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_RenderModelName_String, m_sModelNumber.c_str());
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserIpdMeters_Float, m_flIPD);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, 0.f);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons);
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_DisplayDebugMode_Bool, true);

    bool bSetupIconUsingExternalResourceFile = true;

    if (!bSetupIconUsingExternalResourceFile) {
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceOff_String, "{null}/icons/headset_sample_status_off.png");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearching_String, "{null}/icons/headset_sample_status_searching.gif");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearchingAlert_String, "{null}/icons/headset_sample_status_searching_alert.gif");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReady_String, "{null}/icons/headset_sample_status_ready.png");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReadyAlert_String, "{null}/icons/headset_sample_status_ready_alert.png");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceNotReady_String, "{null}/icons/headset_sample_status_error.png");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceStandby_String, "{null}/icons/headset_sample_status_standby.png");
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceAlertLow_String, "{null}/icons/headset_sample_status_ready_low.png");
    }

    TryConnectSharedMemory();

    return VRInitError_None;
}

void CSampleDeviceDriver::Deactivate()
{
    CleanupSharedMemory();
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
}

void CSampleDeviceDriver::EnterStandby()
{

}

void* CSampleDeviceDriver::GetComponent(const char* pchComponentNameAndVersion)
{
    if (!_stricmp(pchComponentNameAndVersion, vr::IVRDisplayComponent_Version)) {
        return (vr::IVRDisplayComponent*)this;
    }
    return NULL;
}

void CSampleDeviceDriver::PowerOff()

{

}

void CSampleDeviceDriver::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {

        pchResponseBuffer[0] = 0;
    }
}

void CSampleDeviceDriver::GetWindowBounds(int32_t* pnX, int32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight)
{
    //fixes a stupid black bar at the buttom
    float offset = 0.022;

    *pnX = m_nWindowX * 1;
    *pnY = m_nWindowY * (1 - offset);

    *pnWidth = m_nWindowWidth * 1;
    *pnHeight = m_nWindowHeight * (1 - offset);
}

bool CSampleDeviceDriver::IsDisplayOnDesktop()
{
    return true;
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
    *pnY = 0;
    *pnX = 0;

    *pnWidth = m_nWindowWidth;
    *pnHeight = m_nWindowHeight;
}

void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
{
    //fov: 90 is pretty good, dont use the actual fov of your glasses, its too zoomed in!!!
    float FovDeg = 90.0f;

    float fAspectRatio = (float)m_nWindowWidth / (float)m_nWindowHeight;

    float fHalfAngleRad = (FovDeg / 2.0f) * (3.14159265f / 180.0f);
    float fTanHalfAngle = tan(fHalfAngleRad);

    *pfLeft = -fTanHalfAngle;
    *pfRight = fTanHalfAngle;

    float fVerticalTan = fTanHalfAngle / fAspectRatio;

    *pfTop = -fVerticalTan;
    *pfBottom = fVerticalTan;
}

DistortionCoordinates_t CSampleDeviceDriver::ComputeDistortion(EVREye eEye, float fU, float fV)
{
    DistortionCoordinates_t coordinates;

    coordinates.rfBlue[0] = fU;
    coordinates.rfBlue[1] = fV;
    coordinates.rfGreen[0] = fU;
    coordinates.rfGreen[1] = fV;
    coordinates.rfRed[0] = fU;
    coordinates.rfRed[1] = fV;

    return coordinates;
}

vr::DriverPose_t CSampleDeviceDriver::GetPose()
{
    vr::DriverPose_t pose = { 0 };

    pose.poseIsValid = true;

    pose.result = vr::TrackingResult_Running_OK;

    pose.deviceIsConnected = true;

    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    if (pSharedData == NULL) {

        ULONGLONG currentTick = GetTickCount64();

        if (currentTick - g_lastAttemptTick > 2000) {

            g_lastAttemptTick = currentTick;

            TryConnectSharedMemory();

        }

    }

    if (pSharedData != NULL) {

        pose.vecPosition[0] = GetValuseFor("position x");
        pose.vecPosition[1] = GetValuseFor("position y");
        pose.vecPosition[2] = GetValuseFor("position z");

        pose.qRotation.w = GetValuseFor("rotation w");
        pose.qRotation.x = GetValuseFor("rotation x");
        pose.qRotation.y = GetValuseFor("rotation y");
        pose.qRotation.z = GetValuseFor("rotation z");
    }

    else {
        pose.vecPosition[0] = 0;
        pose.vecPosition[1] = 0;
        pose.vecPosition[2] = 0;

        pose.qRotation.w = 1;
        pose.qRotation.x = 0;
        pose.qRotation.y = 0;
        pose.qRotation.z = 0;
    }
    return pose;
}

void CSampleDeviceDriver::RunFrame()
{
    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
}