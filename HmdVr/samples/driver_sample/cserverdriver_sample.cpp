////thanks https://github.com/r57zone/OpenVR-driver-for-DIY and https://github.com/spayne/soft_knuckles


//m to open legacy hmd monitor
#include "cserverdriver_sample.h"
#include "settings.h" 

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

#include <windows.h>
#include <iostream>
#include <cstring>
#include <cstdlib>

using namespace vr;

Packet ReceivedPacket = { 0.0 };
const size_t UDP_PACKET_SIZE = sizeof(Packet);

SOCKET g_udpSocket = INVALID_SOCKET;
std::string IpAddress = "127.0.0.1";
int UdpPort = 9999;
ULONGLONG g_lastAttemptTick = 0;

bool TryConnectUDP() {
    IpAddress = GetStringFromSettingsByKey("ip receiving");
    UdpPort = GetIntFromSettingsByKey("port receiving");

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

    if (IpAddress.empty() || strcmp(IpAddress.c_str(), "0.0.0.0") == 0) {
        service.sin_addr.s_addr = htonl(INADDR_ANY);
    }
    else {
        if (inet_pton(AF_INET, IpAddress.c_str(), &(service.sin_addr)) != 1) {
            closesocket(g_udpSocket);
            g_udpSocket = INVALID_SOCKET;
            WSACleanup();
            return false;
        }
    }

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

void UpdatePoseDataFromUDP()
{
    if (g_udpSocket == INVALID_SOCKET) {
        ULONGLONG currentTick = GetTickCount64();
        if (currentTick - g_lastAttemptTick > 2000) {
            g_lastAttemptTick = currentTick;
            TryConnectUDP();
        }
        return;
    }

    char buffer[UDP_PACKET_SIZE];
    sockaddr_in senderAddr;
    int senderAddrSize = sizeof(senderAddr);
    int bytesReceived = 0;

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
                memcpy(&ReceivedPacket, buffer, UDP_PACKET_SIZE);
            }
        }
        else if (bytesReceived == SOCKET_ERROR) {
            if (WSAGetLastError() == WSAEWOULDBLOCK) {
                break;
            }
            else {
                std::cerr << "UDP Receive Error: " << WSAGetLastError() << std::endl;
                break;
            }
        }
    } while (bytesReceived > 0);
}

bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
bool enable_left = GetBoolFromSettingsByKey("enable cl");
bool enable_right = GetBoolFromSettingsByKey("enable cr");

bool TryConnectUDP();
void CleanupUDP();
void UpdatePoseDataFromUDP();


EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
{
    GetStringFromSettingsByKey("ip receiving");


    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);

    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
    enable_left = GetBoolFromSettingsByKey("enable cl");
    enable_right = GetBoolFromSettingsByKey("enable cr");

    ReceivedPacket.hmd_rot_w = 1.0;

    TryConnectUDP();

    if (enable_hmd == true) {
        m_pNullHmdLatest = new CSampleDeviceDriver();
        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pNullHmdLatest->GetSerialNumber().c_str(), vr::TrackedDeviceClass_HMD, m_pNullHmdLatest);
    }

    if (enable_left == true) {
        m_pController = new CSampleControllerDriver();
        m_pController->SetControllerIndex(false);
        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController);
    }

    if (enable_right == true) {
        m_pController2 = new CSampleControllerDriver();
        m_pController2->SetControllerIndex(true);
        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController2->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController2);
    }

    return VRInitError_None;
}

void CServerDriver_Sample::Cleanup()
{
    CleanupUDP();
    if (enable_hmd == true) {
        delete m_pNullHmdLatest;
        m_pNullHmdLatest = NULL;
    }

    if (enable_left == true) {
        delete m_pController;
        m_pController = NULL;
    }

    if (enable_right == true) {
        delete m_pController2;
        m_pController2 = NULL;
    }
}

void CServerDriver_Sample::RunFrame()
{
    UpdatePoseDataFromUDP();

    if (m_pNullHmdLatest && enable_hmd == true) {
        m_pNullHmdLatest->UpdateData(ReceivedPacket);
        m_pNullHmdLatest->RunFrame();
    }

    if (m_pController && enable_left == true) {
        m_pController->UpdateData(ReceivedPacket);
        m_pController->RunFrame();
    }

    if (m_pController2 && enable_right == true) {
        m_pController2->UpdateData(ReceivedPacket);
        m_pController2->RunFrame();
    }
}