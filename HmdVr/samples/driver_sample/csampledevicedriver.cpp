////code modified from: https://github.com/r57zone/OpenVR-driver-for-DIY

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include "csampledevicedriver.h"

#include "basics.h"
#include <math.h>

#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

#include <windows.h>

#include <string>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <cctype>
#include <cmath>
#include <cstring> 
#include <cstdlib>
#include <cstdio>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;

struct PoseData {
    double pos_x;
    double pos_y;
    double pos_z;

    double rot_w;
    double rot_x;
    double rot_y;
    double rot_z;

    double ipd;

    double head_to_eye_dist; // (center of head)->(eye)--->(screen)
};

const size_t UDP_PACKET_SIZE = sizeof(PoseData);

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
const std::string SettingsFileName = "settings.json";
const std::string AppFolderName = "glassvr";

// Global cache for settings content
static std::string g_settingsContent;


std::string GetFullSettingsPath() {
    char* appDataPath = nullptr;
    size_t len;
    std::string fullPath;

    if (_dupenv_s(&appDataPath, &len, "APPDATA") == 0 && appDataPath != nullptr) {

        // %APPDATA%\\glassvr\\driver settings.json
        fullPath = std::string(appDataPath) + "\\" + AppFolderName + "\\" + SettingsFileName;

        free(appDataPath);

    }
    else {
        std::cerr << "CRITICAL ERROR: Failed to retrieve APPDATA path. Defaulting to current directory." << std::endl;
        fullPath = SettingsFileName; // Fallback
    }

    return fullPath;
}

// Simple trim function (removes leading/trailing whitespace and quotes)
// Essential for cleaning the value string from JSON extraction
std::string trim_value(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r\"");
    if (std::string::npos == start) {
        return "";
    }
    size_t end = str.find_last_not_of(" \t\n\r\"");
    return str.substr(start, (end - start + 1));
}


// --- 1. GetSettings() ---
const std::string& GetSettings() {
    if (!g_settingsContent.empty()) {
        return g_settingsContent;
    }

    const std::string FullSettingsPath = GetFullSettingsPath();
    if (FullSettingsPath.empty()) {
        g_settingsContent = "";
        return g_settingsContent;
    }

    std::ifstream file(FullSettingsPath);

    if (file.is_open()) {
        std::cout << "Loading settings from file: " << FullSettingsPath << std::endl;

        g_settingsContent.assign(
            (std::istreambuf_iterator<char>(file)),
            (std::istreambuf_iterator<char>())
        );
        file.close();
    }
    else {
        std::cerr << "Settings file not found at " << FullSettingsPath << ". Returning empty content." << std::endl;
        g_settingsContent = "";
    }

    return g_settingsContent;
}


// --- Generic Value Extraction Function (Internal Helper) ---
std::string GetValueStringFromContent_JSONLike(const std::string& key) {
    const std::string& content = GetSettings();
    if (content.empty()) {
        return "";
    }

    // 1. Construct the search key: "key" (JSON standard)
    std::string searchKey = "\"" + key + "\"";

    // 2. Find the position of the key
    size_t keyPos = content.find(searchKey);
    if (keyPos == std::string::npos) {
        // Key not found
        return "";
    }

    // 3. Find the colon (':') which must follow the key
    size_t colonPos = content.find(':', keyPos + searchKey.length());
    if (colonPos == std::string::npos) {
        std::cerr << "Colon separator not found after key: " << key << std::endl;
        return "";
    }

    // 4. Find the beginning of the value (after the colon and any whitespace)
    size_t valueStartPos = content.find_first_not_of(" \t\n\r", colonPos + 1);
    if (valueStartPos == std::string::npos) {
        return "";
    }

    // 5. Find the end of the value (comma ',' or closing brace '}')
    // Note: This relies on the file being clean/unformatted JSON.
    size_t commaPos = content.find(',', valueStartPos);
    size_t bracePos = content.find('}', valueStartPos);

    // Get the earliest valid JSON terminator
    size_t valueEndPos = std::min(commaPos, bracePos);

    if (valueEndPos == std::string::npos) {
        valueEndPos = content.length();
    }

    // Extract the raw value string
    std::string rawValue = content.substr(valueStartPos, valueEndPos - valueStartPos);

    // Trim whitespace and quotation marks
    return trim_value(rawValue);
}


// --- 2. GetStringFromSettingsByKey(const std::string& key) ---
std::string GetStringFromSettingsByKey(const std::string& key) {
    std::string result = GetValueStringFromContent_JSONLike(key);
    if (result.empty()) {
        std::cerr << "Warning: Key '" << key << "' not found or value empty in settings." << std::endl;
    }
    return result;
}

// --- GetIntFromSettingsByKey(const std::string& key) ---
int GetIntFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) {
        return 0;
    }

    try {
        return std::stoi(valueStr);
    }
    catch (const std::exception& e) {
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to int: " << e.what() << std::endl;
        return 0;
    }
}

// --- 3. GetFloatFromSettingsByKey(const std::string& key) ---
float GetFloatFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) {
        return std::numeric_limits<float>::quiet_NaN();
    }

    try {
        return std::stof(valueStr);
    }
    catch (const std::exception& e) {
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to float: " << e.what() << std::endl;
        return std::numeric_limits<float>::quiet_NaN();
    }
}

// --- 4. GetBoolFromSettingsByKey(const std::string& key) ---
bool GetBoolFromSettingsByKey(const std::string& key) {
    std::string normalizedContent = GetValueStringFromContent_JSONLike(key);

    std::transform(normalizedContent.begin(), normalizedContent.end(), normalizedContent.begin(), ::tolower);

    if (normalizedContent == "true" || normalizedContent == "1") {
        return true;
    }
    else {
        return false;
    }
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
float HeadToEyeDist = 0.0;
bool Stereoscopic = GetBoolFromSettingsByKey("stereoscopic");
float ResolutionX = GetFloatFromSettingsByKey("resolution x");
float ResolutionY = GetFloatFromSettingsByKey("resolution y");
bool FullScreen = GetBoolFromSettingsByKey("fullscreen");
float RefreshRate = GetFloatFromSettingsByKey("refresh rate");

PoseData g_PoseDataInstance = { 0 };
PoseData* pSharedData = &g_PoseDataInstance;


SOCKET g_udpSocket = INVALID_SOCKET;


std::string IpAddress = "127.0.0.1";
int UdpPort = 9999;

ULONGLONG g_lastAttemptTick = 0;

bool TryConnectUDP() {
    IpAddress = GetStringFromSettingsByKey("ip receiving");
    UdpPort = GetFloatFromSettingsByKey("port receiving");

    if (g_udpSocket != INVALID_SOCKET) {
        return true;
    }
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        return false;
    }
    g_udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (g_udpSocket == INVALID_SOCKET) {
        WSACleanup();
        return false;
    }
    sockaddr_in service;
    service.sin_family = AF_INET;

    // *** MODIFIED IP BINDING LOGIC ***
    if (IpAddress.c_str() == NULL || strcmp(IpAddress.c_str(), "0.0.0.0") == 0) {
        // Use INADDR_ANY (default behavior)
        service.sin_addr.s_addr = htonl(INADDR_ANY);
    }
    else {
        // Use a specific IP address
        if (inet_pton(AF_INET, IpAddress.c_str(), &(service.sin_addr)) != 1) {
            closesocket(g_udpSocket);
            g_udpSocket = INVALID_SOCKET;
            WSACleanup();
            return false;
        }
    }
    // *** END MODIFIED IP BINDING LOGIC ***

    service.sin_port = htons(UdpPort);
    if (bind(g_udpSocket, (SOCKADDR*)&service, sizeof(service)) == SOCKET_ERROR) {
        closesocket(g_udpSocket);
        g_udpSocket = INVALID_SOCKET;
        WSACleanup();
        return false;
    }
    u_long nonBlocking = 1;
    if (ioctlsocket(g_udpSocket, FIONBIO, &nonBlocking) != 0) {
    }
    return true;
}

void CleanupUDP() {
    if (g_udpSocket != INVALID_SOCKET) {
        closesocket(g_udpSocket);
        g_udpSocket = INVALID_SOCKET;
    }
    WSACleanup();
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

    if (pSharedData != NULL) {
        memset(pSharedData, 0, sizeof(PoseData));
        pSharedData->rot_w = 1.0;
    }


    m_flIPD = vr::VRSettings()->GetFloat(k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float);

    if (pSharedData != NULL) {
        pSharedData->ipd = m_flIPD;
        pSharedData->head_to_eye_dist = 0.0;
    }

    char buf[1024];

    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_SerialNumber_String, buf, sizeof(buf));
    m_sSerialNumber = buf;


    vr::VRSettings()->GetString(k_pch_Sample_Section, k_pch_Sample_ModelNumber_String, buf, sizeof(buf));
    m_sModelNumber = buf;

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

    m_flSecondsFromVsyncToPhotons = 0.008;
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
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, RefreshRate);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons);
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_DisplayDebugMode_Bool, !FullScreen);//true = window mode, false = fullscreen

    TryConnectUDP();

    return VRInitError_None;
}

void CSampleDeviceDriver::Deactivate()
{
    CleanupUDP();
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
    if (Stereoscopic) {
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

constexpr float k_fRadFactor = (float)M_PI / 180.0f;

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
    pose.qDriverFromHeadRotation.w = 1.0;

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

    if (pSharedData != NULL) {
        // Position comes directly from the UDP data
        pose.vecPosition[0] = GetValuseFor("position x");
        pose.vecPosition[1] = GetValuseFor("position y");
        pose.vecPosition[2] = GetValuseFor("position z");

        // Rotation (Quaternion) comes directly from the UDP data
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
    if (g_udpSocket == INVALID_SOCKET) {
        ULONGLONG currentTick = GetTickCount64();
        if (currentTick - g_lastAttemptTick > 2000) {
            g_lastAttemptTick = currentTick;
            TryConnectUDP();
        }
    }

    if (g_udpSocket != INVALID_SOCKET) {
        char buffer[UDP_PACKET_SIZE];
        sockaddr_in senderAddr;
        int senderAddrSize = sizeof(senderAddr);
        int bytesReceived = 0;
        int packetsProcessed = 0;

        do {
            bytesReceived = recvfrom(
                g_udpSocket,
                buffer,
                UDP_PACKET_SIZE,
                0,
                (SOCKADDR*)&senderAddr,
                &senderAddrSize
            );

            if (bytesReceived > 0) {
                if (bytesReceived == UDP_PACKET_SIZE) {
                    if (pSharedData != NULL) {
                        memcpy(pSharedData, buffer, UDP_PACKET_SIZE);
                        packetsProcessed++;
                    }
                }
            }
            else if (bytesReceived == SOCKET_ERROR) {
                if (WSAGetLastError() == WSAEWOULDBLOCK) {
                    break;
                }
                else {
                    break;
                }
            }
        } while (bytesReceived > 0);
    }

    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));

        m_flIPD = (float)GetValuseFor("ipd");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserIpdMeters_Float,
            m_flIPD
        );

        HeadToEyeDist = (float)GetValuseFor("head to eye dist");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserHeadToEyeDepthMeters_Float,
            HeadToEyeDist
        );
    }
}