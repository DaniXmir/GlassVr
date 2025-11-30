#include "csampledevicedriver.h"

#include "basics.h"

#include <math.h>

#include <windows.h>

#include <string>

#include <iostream>

#include <algorithm>

#include <cmath>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;

struct SharedPoseData {
    double pos_x;
    double pos_y;
    double pos_z;

    double rot_w;
    double rot_x;
    double rot_y;
    double rot_z;

    double ipd;

    double head_to_eye_dist; //(center of head)->(eye)--->(screen)
};

float HeadToEyeDist = 0.0;

//if both screen can be accessed
bool dual = true;

//fov scale
float FovModifier = 2.0;

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

    if (key == "ipd") return pSharedData->ipd;
    if (key == "head to eye dist") return pSharedData->head_to_eye_dist;

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

    m_nWindowX = 0;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowX_Int32);
    m_nWindowY = 0;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowY_Int32);

    if (dual) {
        m_nWindowWidth = 1920 * 2;
        m_nRenderWidth = 1920 * 2;
    }
    else {
        m_nWindowWidth = 1920;
        m_nRenderWidth = 1920;
    }
    m_nWindowHeight = 1080;
    m_nRenderHeight = 1080;

    //m_nWindowWidth = 1920 * 2;// *offset;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowWidth_Int32);
    //    m_nWindowHeight = 1080;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_WindowHeight_Int32);

    //m_nRenderWidth = 1920 * 2;// *offset;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_RenderWidth_Int32);
    //    m_nRenderHeight = 1080;//vr::VRSettings()->GetInt32(k_pch_Sample_Section, k_pch_Sample_RenderHeight_Int32);

    m_flSecondsFromVsyncToPhotons = 0.008;//vr::VRSettings()->GetFloat(k_pch_Sample_Section, k_pch_Sample_SecondsFromVsyncToPhotons_Float);
    m_flDisplayFrequency = 120.0;//vr::VRSettings()->GetFloat(k_pch_Sample_Section, k_pch_Sample_DisplayFrequency_Float);
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
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, HeadToEyeDist);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons);
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_DisplayDebugMode_Bool, true);//LOW FPS!!! DO NOT ENABLE!!!, FOR DEBUGING(window mode) SET TO true FOR REALESE(fullscreen) SET TO false

    //bool bSetupIconUsingExternalResourceFile = false;

    //if (!bSetupIconUsingExternalResourceFile) {
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceOff_String, "{null}/icons/headset_sample_status_off.png");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearching_String, "{null}/icons/headset_sample_status_searching.gif");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearchingAlert_String, "{null}/icons/headset_sample_status_searching_alert.gif");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReady_String, "{null}/icons/headset_sample_status_ready.png");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReadyAlert_String, "{null}/icons/headset_sample_status_ready_alert.png");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceNotReady_String, "{null}/icons/headset_sample_status_error.png");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceStandby_String, "{null}/icons/headset_sample_status_standby.png");
    //    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceAlertLow_String, "{null}/icons/headset_sample_status_ready_low.png");
    //}

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
    *pnX = m_nWindowX;
    *pnY = m_nWindowY;

    *pnWidth = m_nWindowWidth;
    *pnHeight = m_nWindowHeight;
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
    //*pnX = 0;
    //*pnY = 0;
    //*pnWidth = m_nWindowWidth;
    //*pnHeight = m_nWindowHeight;

    if (dual) {
        *pnY = 0;
        *pnWidth = m_nWindowWidth / 2;
        *pnHeight = m_nWindowHeight;

        if (eEye == Eye_Left) {
            *pnX = 0;
        }
        else {
            *pnX = m_nWindowWidth / 2;
        }
    }
    else {
        const EVREye RENDER_EYE = EVREye::Eye_Right;

        if (eEye == RENDER_EYE) {
            *pnX = 0;
            *pnY = 0;
            *pnWidth = m_nWindowWidth;
            *pnHeight = m_nWindowHeight;
        }
        else {
            *pnX = 0;
            *pnY = 0;
            *pnWidth = 0;
            *pnHeight = 0;
        }
    }
}

//void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
//{
//    ////fov: 90 is pretty good, dont use the actual fov of your glasses, its too zoomed in!!!
//    //float FovDeg = 90.0f;
//
//    //float fAspectRatio = (float)m_nWindowWidth / (float)m_nWindowHeight;
//
//    //float fHalfAngleRad = (FovDeg / 2.0f) * (3.14159265f / 180.0f);
//    //float fTanHalfAngle = tan(fHalfAngleRad);
//
//    //*pfLeft = -fTanHalfAngle;
//    //*pfRight = fTanHalfAngle;
//
//    //float fVerticalTan = fTanHalfAngle / fAspectRatio;
//
//    //*pfTop = -fVerticalTan;
//    //*pfBottom = fVerticalTan;
//}



//void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
//{
//    *pfLeft = -1.0;
//    *pfRight = 1.0;
//    *pfTop = -1.0;
//    *pfBottom = 1.0;
//}


//asymmetrical best///////////////////////////////////////////////////////////////////////
//constexpr float k_fAngleOuterH_Deg = 18.0f;
//constexpr float k_fAngleInnerH_Deg = 25.0f;
//constexpr float k_fAngleTopV_Deg = 12.0f;
//constexpr float k_fAngleBottomV_Deg = 11.0f;

//constexpr float k_fAngleOuterH_Deg = 30.0;
//constexpr float k_fAngleInnerH_Deg = 30.0;
//constexpr float k_fAngleTopV_Deg = 30.0;
//constexpr float k_fAngleBottomV_Deg = 30.0;

//thank you genimi, now why is my youtube homepage filled with DIY vr headsets and trackers? i used incognito!!!
float k_fAngleOuterH_Deg = 18.0f * FovModifier;
float k_fAngleInnerH_Deg = 25.0f * FovModifier;
float k_fAngleTopV_Deg = 12.0f * FovModifier;
float k_fAngleBottomV_Deg = 11.0f * FovModifier;

constexpr float k_fRadFactor = (float)M_PI / 180.0f;

const float k_fTangentOuterH = std::tan(k_fAngleOuterH_Deg * k_fRadFactor);
const float k_fTangentInnerH = std::tan(k_fAngleInnerH_Deg * k_fRadFactor);
const float k_fTangentTopV = std::tan(k_fAngleTopV_Deg * k_fRadFactor);
const float k_fTangentBottomV = std::tan(k_fAngleBottomV_Deg * k_fRadFactor);

void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
{
    *pfRight = k_fTangentOuterH;
    *pfLeft = -k_fTangentInnerH;

    *pfTop = -k_fTangentTopV;
    *pfBottom = k_fTangentBottomV;
}
//asymmetrical best///////////////////////////////////////////////////////////////////////


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

        m_flIPD = GetValuseFor("ipd");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserIpdMeters_Float,
            m_flIPD
        );

        HeadToEyeDist = GetValuseFor("head to eye dist");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserHeadToEyeDepthMeters_Float,
            HeadToEyeDist
        );

    }
}