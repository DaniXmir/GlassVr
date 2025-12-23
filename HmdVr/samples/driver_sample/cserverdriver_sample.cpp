////thanks https://github.com/r57zone/OpenVR-driver-for-DIY


//m to open legacy hmd monitor
//#include "cserverdriver_sample.h"
//#include "settings.h" 
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include <winsock2.h>
//#include <ws2tcpip.h>
//#pragma comment(lib, "ws2_32.lib")
//
//#include <windows.h>
//#include <iostream>
//#include <cstring>
//#include <cstdlib>
//
//using namespace vr;
//
//Packet ReceivedPacket = { 0.0 };
//const size_t UDP_PACKET_SIZE = sizeof(Packet);
//
//SOCKET g_udpSocket = INVALID_SOCKET;
//std::string IpAddress = "127.0.0.1";
//int UdpPort = 9999;
//ULONGLONG g_lastAttemptTick = 0;
//
//bool TryConnectUDP() {
//    IpAddress = GetStringFromSettingsByKey("ip receiving");
//    UdpPort = GetIntFromSettingsByKey("port receiving");
//
//    if (g_udpSocket != INVALID_SOCKET) {
//        return true;
//    }
//    WSADATA wsaData;
//    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
//        return false;
//    }
//    g_udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
//    if (g_udpSocket == INVALID_SOCKET) {
//        WSACleanup();
//        return false;
//    }
//    sockaddr_in service;
//    service.sin_family = AF_INET;
//
//    if (IpAddress.empty() || strcmp(IpAddress.c_str(), "0.0.0.0") == 0) {
//        service.sin_addr.s_addr = htonl(INADDR_ANY);
//    }
//    else {
//        if (inet_pton(AF_INET, IpAddress.c_str(), &(service.sin_addr)) != 1) {
//            closesocket(g_udpSocket);
//            g_udpSocket = INVALID_SOCKET;
//            WSACleanup();
//            return false;
//        }
//    }
//
//    service.sin_port = htons(UdpPort);
//    if (bind(g_udpSocket, (SOCKADDR*)&service, sizeof(service)) == SOCKET_ERROR) {
//        closesocket(g_udpSocket);
//        g_udpSocket = INVALID_SOCKET;
//        WSACleanup();
//        return false;
//    }
//    u_long nonBlocking = 1;
//    if (ioctlsocket(g_udpSocket, FIONBIO, &nonBlocking) != 0) {
//    }
//    return true;
//}
//
//void CleanupUDP() {
//    if (g_udpSocket != INVALID_SOCKET) {
//        closesocket(g_udpSocket);
//        g_udpSocket = INVALID_SOCKET;
//    }
//    WSACleanup();
//}
//
//void UpdatePoseDataFromUDP()
//{
//    if (g_udpSocket == INVALID_SOCKET) {
//        ULONGLONG currentTick = GetTickCount64();
//        if (currentTick - g_lastAttemptTick > 2000) {
//            g_lastAttemptTick = currentTick;
//            TryConnectUDP();
//        }
//        return;
//    }
//
//    char buffer[UDP_PACKET_SIZE];
//    sockaddr_in senderAddr;
//    int senderAddrSize = sizeof(senderAddr);
//    int bytesReceived = 0;
//
//    do {
//        bytesReceived = recvfrom(
//            g_udpSocket,
//            buffer,
//            UDP_PACKET_SIZE,
//            0,
//            (SOCKADDR*)&senderAddr,
//            &senderAddrSize
//        );
//
//        if (bytesReceived > 0) {
//            if (bytesReceived == UDP_PACKET_SIZE) {
//                memcpy(&ReceivedPacket, buffer, UDP_PACKET_SIZE);
//            }
//        }
//        else if (bytesReceived == SOCKET_ERROR) {
//            if (WSAGetLastError() == WSAEWOULDBLOCK) {
//                break;
//            }
//            else {
//                std::cerr << "UDP Receive Error: " << WSAGetLastError() << std::endl;
//                break;
//            }
//        }
//    } while (bytesReceived > 0);
//}
//
//bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//bool enable_left = GetBoolFromSettingsByKey("enable cl");
//bool enable_right = GetBoolFromSettingsByKey("enable cr");
//
//bool TryConnectUDP();
//void CleanupUDP();
//void UpdatePoseDataFromUDP();
//
//
//EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
//{
//    GetStringFromSettingsByKey("ip receiving");
//
//
//    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);
//
//    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//    enable_left = GetBoolFromSettingsByKey("enable cl");
//    enable_right = GetBoolFromSettingsByKey("enable cr");
//
//    ReceivedPacket.hmd_rot_w = 1.0;
//
//    TryConnectUDP();
//
//    if (enable_hmd == true) {
//        m_pNullHmdLatest = new CSampleDeviceDriver();
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pNullHmdLatest->GetSerialNumber().c_str(), vr::TrackedDeviceClass_HMD, m_pNullHmdLatest);
//    }
//
//    if (enable_left == true) {
//        m_pController = new CSampleControllerDriver();
//        m_pController->SetControllerIndex(false);
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController);
//    }
//
//    if (enable_right == true) {
//        m_pController2 = new CSampleControllerDriver();
//        m_pController2->SetControllerIndex(true);
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController2->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController2);
//    }
//    ///////////////////////////////////////
//    //m_tracker = new CSampleTracker();
//    //m_tracker->SetTrackerIndex(1);
//    //vr::VRServerDriverHost()->TrackedDeviceAdded(m_tracker->GetSerialNumber().c_str(), vr::TrackedDeviceClass_GenericTracker, m_tracker);
//    ///////////////////////////////////////
//    return VRInitError_None;
//}
//
//void CServerDriver_Sample::Cleanup()
//{
//    CleanupUDP();
//    if (enable_hmd == true) {
//        delete m_pNullHmdLatest;
//        m_pNullHmdLatest = NULL;
//    }
//
//    if (enable_left == true) {
//        delete m_pController;
//        m_pController = NULL;
//    }
//
//    if (enable_right == true) {
//        delete m_pController2;
//        m_pController2 = NULL;
//    }
//    ///////////////////////////////////////
//    //delete m_tracker;
//    //m_tracker = NULL;
//    ///////////////////////////////////////
//}
//
//void CServerDriver_Sample::RunFrame()
//{
//    UpdatePoseDataFromUDP();
//
//    if (m_pNullHmdLatest && enable_hmd == true) {
//        m_pNullHmdLatest->UpdateData(ReceivedPacket);
//        m_pNullHmdLatest->RunFrame();
//    }
//
//    if (m_pController && enable_left == true) {
//        m_pController->UpdateData(ReceivedPacket);
//        m_pController->RunFrame();
//    }
//
//    if (m_pController2 && enable_right == true) {
//        m_pController2->UpdateData(ReceivedPacket);
//        m_pController2->RunFrame();
//    }
//    ///////////////////////////////////////
//    //if (m_tracker);
//    //    m_tracker->RunFrame();
//    ///////////////////////////////////////
//}






































//#include "cserverdriver_sample.h"
//#include "settings.h" 
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include <winsock2.h>
//#include <ws2tcpip.h>
//#pragma comment(lib, "ws2_32.lib")
//
//#include <windows.h>
//#include <iostream>
//#include <cstring>
//#include <cstdlib>
//#include <thread>
//#include <atomic>
//#include <mutex>
//
//using namespace vr;
//
//Packet ReceivedPacket = { 0.0 };
//const size_t UDP_PACKET_SIZE = sizeof(Packet);
//
//SOCKET g_udpSocket = INVALID_SOCKET;
//std::string IpAddress = "127.0.0.1";
//int UdpPort = 9999;
//ULONGLONG g_lastAttemptTick = 0;
//
//// Thread management
//std::thread g_udpThread;
//std::thread g_updateThread;
//std::atomic<bool> g_threadRunning(false);
//std::mutex g_packetMutex;
//
//// Device pointers for update thread
//CSampleDeviceDriver* g_pHmd = nullptr;
//CSampleControllerDriver* g_pControllerLeft = nullptr;
//CSampleControllerDriver* g_pControllerRight = nullptr;
//bool g_enableHmd = false;
//bool g_enableLeft = false;
//bool g_enableRight = false;
//
//bool TryConnectUDP() {
//    IpAddress = GetStringFromSettingsByKey("ip receiving");
//    UdpPort = GetIntFromSettingsByKey("port receiving");
//
//    if (g_udpSocket != INVALID_SOCKET) {
//        return true;
//    }
//    WSADATA wsaData;
//    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
//        return false;
//    }
//    g_udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
//    if (g_udpSocket == INVALID_SOCKET) {
//        WSACleanup();
//        return false;
//    }
//    sockaddr_in service;
//    service.sin_family = AF_INET;
//
//    if (IpAddress.empty() || strcmp(IpAddress.c_str(), "0.0.0.0") == 0) {
//        service.sin_addr.s_addr = htonl(INADDR_ANY);
//    }
//    else {
//        if (inet_pton(AF_INET, IpAddress.c_str(), &(service.sin_addr)) != 1) {
//            closesocket(g_udpSocket);
//            g_udpSocket = INVALID_SOCKET;
//            WSACleanup();
//            return false;
//        }
//    }
//
//    service.sin_port = htons(UdpPort);
//    if (bind(g_udpSocket, (SOCKADDR*)&service, sizeof(service)) == SOCKET_ERROR) {
//        closesocket(g_udpSocket);
//        g_udpSocket = INVALID_SOCKET;
//        WSACleanup();
//        return false;
//    }
//
//    // Set socket timeout instead of non-blocking for cleaner thread shutdown
//    DWORD timeout = 1000; // 1 second timeout
//    setsockopt(g_udpSocket, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));
//
//    return true;
//}
//
//void CleanupUDP() {
//    if (g_udpSocket != INVALID_SOCKET) {
//        closesocket(g_udpSocket);
//        g_udpSocket = INVALID_SOCKET;
//    }
//    WSACleanup();
//}
//
//void UDPReceiveThread()
//{
//    char buffer[UDP_PACKET_SIZE];
//    sockaddr_in senderAddr;
//    int senderAddrSize = sizeof(senderAddr);
//    Packet tempPacket;
//
//    while (g_threadRunning) {
//        if (g_udpSocket == INVALID_SOCKET) {
//            ULONGLONG currentTick = GetTickCount64();
//            if (currentTick - g_lastAttemptTick > 2000) {
//                g_lastAttemptTick = currentTick;
//                TryConnectUDP();
//            }
//            Sleep(100);
//            continue;
//        }
//
//        int bytesReceived = recvfrom(
//            g_udpSocket,
//            buffer,
//            UDP_PACKET_SIZE,
//            0,
//            (SOCKADDR*)&senderAddr,
//            &senderAddrSize
//        );
//
//        if (bytesReceived > 0) {
//            if (bytesReceived == UDP_PACKET_SIZE) {
//                memcpy(&tempPacket, buffer, UDP_PACKET_SIZE);
//
//                // Lock and update the shared packet
//                {
//                    std::lock_guard<std::mutex> lock(g_packetMutex);
//                    ReceivedPacket = tempPacket;
//                }
//            }
//        }
//        else if (bytesReceived == SOCKET_ERROR) {
//            int error = WSAGetLastError();
//            if (error == WSAETIMEDOUT) {
//                // Timeout is expected, continue
//                continue;
//            }
//            else {
//                std::cerr << "UDP Receive Error: " << error << std::endl;
//                // Connection might be lost, try to reconnect
//                closesocket(g_udpSocket);
//                g_udpSocket = INVALID_SOCKET;
//            }
//        }
//    }
//}
//
//void UpdateDataThread()
//{
//    while (g_threadRunning) {
//        // Get the latest packet (thread-safe)
//        Packet currentPacket;
//        {
//            std::lock_guard<std::mutex> lock(g_packetMutex);
//            currentPacket = ReceivedPacket;
//        }
//
//        // Update devices with the latest packet
//        if (g_pHmd && g_enableHmd) {
//            g_pHmd->UpdateData(currentPacket);
//        }
//
//        if (g_pControllerLeft && g_enableLeft) {
//            g_pControllerLeft->UpdateData(currentPacket);
//        }
//
//        if (g_pControllerRight && g_enableRight) {
//            g_pControllerRight->UpdateData(currentPacket);
//        }
//
//        // Sleep briefly to avoid spinning at 100% CPU
//        // Adjust this value based on your tracking update rate
//        Sleep(0.001); // ~1000 Hz update rate
//    }
//}
//
//Packet GetCurrentPacket()
//{
//    std::lock_guard<std::mutex> lock(g_packetMutex);
//    return ReceivedPacket;
//}
//
//bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//bool enable_left = GetBoolFromSettingsByKey("enable cl");
//bool enable_right = GetBoolFromSettingsByKey("enable cr");
//
//bool TryConnectUDP();
//void CleanupUDP();
//void UDPReceiveThread();
//void UpdateDataThread();
//Packet GetCurrentPacket();
//
//
//EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
//{
//    GetStringFromSettingsByKey("ip receiving");
//
//    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);
//
//    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//    enable_left = GetBoolFromSettingsByKey("enable cl");
//    enable_right = GetBoolFromSettingsByKey("enable cr");
//
//    // Store in globals for thread access
//    g_enableHmd = enable_hmd;
//    g_enableLeft = enable_left;
//    g_enableRight = enable_right;
//
//    ReceivedPacket.hmd_rot_w = 1.0;
//
//    TryConnectUDP();
//
//    if (enable_hmd == true) {
//        m_pNullHmdLatest = new CSampleDeviceDriver();
//        g_pHmd = m_pNullHmdLatest;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pNullHmdLatest->GetSerialNumber().c_str(), vr::TrackedDeviceClass_HMD, m_pNullHmdLatest);
//    }
//
//    if (enable_left == true) {
//        m_pController = new CSampleControllerDriver();
//        m_pController->SetControllerIndex(false);
//        g_pControllerLeft = m_pController;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController);
//    }
//
//    if (enable_right == true) {
//        m_pController2 = new CSampleControllerDriver();
//        m_pController2->SetControllerIndex(true);
//        g_pControllerRight = m_pController2;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController2->GetSerialNumber().c_str(), vr::TrackedDeviceClass_Controller, m_pController2);
//    }
//
//    // Start threads after devices are created
//    g_threadRunning = true;
//    g_udpThread = std::thread(UDPReceiveThread);
//    g_updateThread = std::thread(UpdateDataThread);
//
//    ///////////////////////////////////////
//    //m_tracker = new CSampleTracker();
//    //m_tracker->SetTrackerIndex(1);
//    //vr::VRServerDriverHost()->TrackedDeviceAdded(m_tracker->GetSerialNumber().c_str(), vr::TrackedDeviceClass_GenericTracker, m_tracker);
//    ///////////////////////////////////////
//    return VRInitError_None;
//}
//
//void CServerDriver_Sample::Cleanup()
//{
//    // Stop threads
//    g_threadRunning = false;
//
//    if (g_updateThread.joinable()) {
//        g_updateThread.join();
//    }
//
//    if (g_udpThread.joinable()) {
//        g_udpThread.join();
//    }
//
//    // Clear global pointers
//    g_pHmd = nullptr;
//    g_pControllerLeft = nullptr;
//    g_pControllerRight = nullptr;
//
//    CleanupUDP();
//
//    if (enable_hmd == true) {
//        delete m_pNullHmdLatest;
//        m_pNullHmdLatest = NULL;
//    }
//
//    if (enable_left == true) {
//        delete m_pController;
//        m_pController = NULL;
//    }
//
//    if (enable_right == true) {
//        delete m_pController2;
//        m_pController2 = NULL;
//    }
//    ///////////////////////////////////////
//    //delete m_tracker;
//    //m_tracker = NULL;
//    ///////////////////////////////////////
//}
//
//void CServerDriver_Sample::RunFrame()
//{
//    // Just call RunFrame() on devices - UpdateData is now handled in separate thread
//    if (m_pNullHmdLatest && enable_hmd == true) {
//        m_pNullHmdLatest->RunFrame();
//    }
//
//    if (m_pController && enable_left == true) {
//        m_pController->RunFrame();
//    }
//
//    if (m_pController2 && enable_right == true) {
//        m_pController2->RunFrame();
//    }
//    ///////////////////////////////////////
//    //if (m_tracker);
//    //    m_tracker->RunFrame();
//    ///////////////////////////////////////
//}

















































//#include "cserverdriver_sample.h"
//#include "settings.h" 
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include <windows.h>
//#include <iostream>
//#include <cstring>
//
//using namespace vr;
//
//HANDLE g_hPipe = INVALID_HANDLE_VALUE;
//Packet ReceivedPacket = { 0 };
//const char* g_pipeName = "\\\\.\\pipe\\GlassVR";
//ULONGLONG g_lastPipeAttempt = 0;
//
//bool TryConnectPipe() {
//    if (g_hPipe != INVALID_HANDLE_VALUE) {
//        return true;
//    }
//
//    g_hPipe = CreateFileA(
//        g_pipeName,
//        GENERIC_READ,
//        0,
//        NULL,
//        OPEN_EXISTING,
//        0,
//        NULL
//    );
//
//    if (g_hPipe == INVALID_HANDLE_VALUE) {
//        return false;
//    }
//
//    DWORD dwMode = PIPE_NOWAIT;
//    if (!SetNamedPipeHandleState(g_hPipe, &dwMode, NULL, NULL)) {
//        CloseHandle(g_hPipe);
//        g_hPipe = INVALID_HANDLE_VALUE;
//        return false;
//    }
//
//    return true;
//}
//
//void CleanupPipe() {
//    if (g_hPipe != INVALID_HANDLE_VALUE) {
//        CloseHandle(g_hPipe);
//        g_hPipe = INVALID_HANDLE_VALUE;
//    }
//}
//
//void UpdatePoseDataFromPipe() {
//    if (g_hPipe == INVALID_HANDLE_VALUE) {
//        ULONGLONG now = GetTickCount64();
//        if (now - g_lastPipeAttempt > 2000) {
//            g_lastPipeAttempt = now;
//            g_hPipe = CreateFileA(g_pipeName, GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
//
//            if (g_hPipe != INVALID_HANDLE_VALUE) {
//                DWORD dwMode = PIPE_NOWAIT;
//                SetNamedPipeHandleState(g_hPipe, &dwMode, NULL, NULL);
//            }
//        }
//        return;
//    }
//
//    DWORD bytesAvailable = 0;
//    if (PeekNamedPipe(g_hPipe, NULL, 0, NULL, &bytesAvailable, NULL)) {
//        if (bytesAvailable >= sizeof(Packet)) {
//            int packetCount = bytesAvailable / sizeof(Packet);
//            DWORD bytesRead;
//
//            for (int i = 0; i < packetCount; i++) {
//                if (!ReadFile(g_hPipe, &ReceivedPacket, sizeof(Packet), &bytesRead, NULL)) {
//                    CleanupPipe();
//                    return;
//                }
//            }
//        }
//    }
//    else {
//        CleanupPipe();
//    }
//}
//
//bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//bool enable_left = GetBoolFromSettingsByKey("enable cl");
//bool enable_right = GetBoolFromSettingsByKey("enable cr");
//
//EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
//{
//    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);
//
//    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
//    enable_left = GetBoolFromSettingsByKey("enable cl");
//    enable_right = GetBoolFromSettingsByKey("enable cr");
//
//    ReceivedPacket.hmd_rot_w = 1.0;
//
//    TryConnectPipe();
//
//    if (enable_hmd) {
//        m_pNullHmdLatest = new CSampleDeviceDriver();
//        vr::VRServerDriverHost()->TrackedDeviceAdded(
//            m_pNullHmdLatest->GetSerialNumber().c_str(),
//            vr::TrackedDeviceClass_HMD,
//            m_pNullHmdLatest
//        );
//    }
//
//    if (enable_left) {
//        m_pController = new CSampleControllerDriver();
//        m_pController->SetControllerIndex(false);
//        vr::VRServerDriverHost()->TrackedDeviceAdded(
//            m_pController->GetSerialNumber().c_str(),
//            vr::TrackedDeviceClass_Controller,
//            m_pController
//        );
//    }
//
//    if (enable_right) {
//        m_pController2 = new CSampleControllerDriver();
//        m_pController2->SetControllerIndex(true);
//        vr::VRServerDriverHost()->TrackedDeviceAdded(
//            m_pController2->GetSerialNumber().c_str(),
//            vr::TrackedDeviceClass_Controller,
//            m_pController2
//        );
//    }
//
//    return VRInitError_None;
//}
//
//void CServerDriver_Sample::Cleanup()
//{
//    CleanupPipe();
//
//    if (enable_hmd) {
//        delete m_pNullHmdLatest;
//        m_pNullHmdLatest = NULL;
//    }
//
//    if (enable_left) {
//        delete m_pController;
//        m_pController = NULL;
//    }
//
//    if (enable_right) {
//        delete m_pController2;
//        m_pController2 = NULL;
//    }
//}
//
//void CServerDriver_Sample::RunFrame()
//{
//    UpdatePoseDataFromPipe();
//
//    if (m_pNullHmdLatest && enable_hmd) {
//        m_pNullHmdLatest->UpdateData(ReceivedPacket);
//        m_pNullHmdLatest->RunFrame();
//    }
//
//    if (m_pController && enable_left) {
//        m_pController->UpdateData(ReceivedPacket);
//        m_pController->RunFrame();
//    }
//
//    if (m_pController2 && enable_right) {
//        m_pController2->UpdateData(ReceivedPacket);
//        m_pController2->RunFrame();
//    }
//}
















































//#include "cserverdriver_sample.h"
//#include "settings.h" 
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include <windows.h>
//#include <iostream>
//#include <thread>
//#include <atomic>
//#include <mutex>
//#include <chrono>
//
//using namespace vr;
//
//// --- Globals ---
//Packet ReceivedPacket = { 0 };
//HANDLE g_hPipe = INVALID_HANDLE_VALUE;
//const char* g_pipeName = "\\\\.\\pipe\\GlassVR";
//ULONGLONG g_lastPipeAttempt = 0;
//
//// Thread management
//std::thread g_pipeThread;
//std::thread g_updateThread;
//std::atomic<bool> g_threadRunning(false);
//std::mutex g_packetMutex;
//
//// Device pointers for the update thread
//CSampleDeviceDriver* g_pHmd = nullptr;
//CSampleControllerDriver* g_pControllerLeft = nullptr;
//CSampleControllerDriver* g_pControllerRight = nullptr;
//
//bool g_enableHmd = false;
//bool g_enableLeft = false;
//bool g_enableRight = false;
//
//// --- Pipe Logic ---
//bool TryConnectPipe() {
//    if (g_hPipe != INVALID_HANDLE_VALUE) return true;
//
//    g_hPipe = CreateFileA(g_pipeName, GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
//
//    if (g_hPipe != INVALID_HANDLE_VALUE) {
//        DWORD dwMode = PIPE_NOWAIT;
//        SetNamedPipeHandleState(g_hPipe, &dwMode, NULL, NULL);
//        return true;
//    }
//    return false;
//}
//
//void CleanupPipe() {
//    if (g_hPipe != INVALID_HANDLE_VALUE) {
//        CloseHandle(g_hPipe);
//        g_hPipe = INVALID_HANDLE_VALUE;
//    }
//}
//
//// --- Thread 1: Pipe Reader ---
//void PipeReadThread() {
//    while (g_threadRunning) {
//        if (g_hPipe == INVALID_HANDLE_VALUE) {
//            ULONGLONG now = GetTickCount64();
//            if (now - g_lastPipeAttempt > 2000) {
//                g_lastPipeAttempt = now;
//                TryConnectPipe();
//            }
//            std::this_thread::sleep_for(std::chrono::milliseconds(100));
//            continue;
//        }
//
//        DWORD bytesAvailable = 0;
//        if (PeekNamedPipe(g_hPipe, NULL, 0, NULL, &bytesAvailable, NULL)) {
//            if (bytesAvailable >= sizeof(Packet)) {
//                int packetCount = bytesAvailable / sizeof(Packet);
//                DWORD bytesRead;
//                Packet latestPacket = { 0 };
//
//                // Read all available packets, but only keep the newest one
//                for (int i = 0; i < packetCount; i++) {
//                    if (!ReadFile(g_hPipe, &latestPacket, sizeof(Packet), &bytesRead, NULL)) {
//                        CleanupPipe();
//                        break;
//                    }
//                }
//
//                if (bytesRead == sizeof(Packet)) {
//                    std::lock_guard<std::mutex> lock(g_packetMutex);
//                    ReceivedPacket = latestPacket;
//                }
//            }
//        }
//        else {
//            CleanupPipe();
//        }
//
//        // High frequency polling (approx 2000Hz)
//        std::this_thread::sleep_for(std::chrono::microseconds(500));
//    }
//}
//
//// --- Thread 2: Device Updater ---
//void UpdateDataThread() {
//    while (g_threadRunning) {
//        Packet localPacket;
//        {
//            std::lock_guard<std::mutex> lock(g_packetMutex);
//            localPacket = ReceivedPacket;
//        }
//
//        // Push data to device instances
//        if (g_pHmd && g_enableHmd) g_pHmd->UpdateData(localPacket);
//        if (g_pControllerLeft && g_enableLeft) g_pControllerLeft->UpdateData(localPacket);
//        if (g_pControllerRight && g_enableRight) g_pControllerRight->UpdateData(localPacket);
//
//        std::this_thread::sleep_for(std::chrono::microseconds(1));
//    }
//}
//
//// --- Server Driver Class Implementation ---
//
//EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext) {
//    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);
//
//    g_enableHmd = GetBoolFromSettingsByKey("enable hmd");
//    g_enableLeft = GetBoolFromSettingsByKey("enable cl");
//    g_enableRight = GetBoolFromSettingsByKey("enable cr");
//
//    ReceivedPacket.hmd_rot_w = 1.0;
//    TryConnectPipe();
//
//    if (g_enableHmd) {
//        m_pNullHmdLatest = new CSampleDeviceDriver();
//        g_pHmd = m_pNullHmdLatest;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pNullHmdLatest->GetSerialNumber().c_str(), TrackedDeviceClass_HMD, m_pNullHmdLatest);
//    }
//
//    if (g_enableLeft) {
//        m_pController = new CSampleControllerDriver();
//        m_pController->SetControllerIndex(false);
//        g_pControllerLeft = m_pController;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController->GetSerialNumber().c_str(), TrackedDeviceClass_Controller, m_pController);
//    }
//
//    if (g_enableRight) {
//        m_pController2 = new CSampleControllerDriver();
//        m_pController2->SetControllerIndex(true);
//        g_pControllerRight = m_pController2;
//        vr::VRServerDriverHost()->TrackedDeviceAdded(m_pController2->GetSerialNumber().c_str(), TrackedDeviceClass_Controller, m_pController2);
//    }
//
//    // Launch background threads
//    g_threadRunning = true;
//    g_pipeThread = std::thread(PipeReadThread);
//    g_updateThread = std::thread(UpdateDataThread);
//
//    return VRInitError_None;
//}
//
//void CServerDriver_Sample::Cleanup() {
//    g_threadRunning = false;
//
//    if (g_pipeThread.joinable()) g_pipeThread.join();
//    if (g_updateThread.joinable()) g_updateThread.join();
//
//    g_pHmd = nullptr;
//    g_pControllerLeft = nullptr;
//    g_pControllerRight = nullptr;
//
//    CleanupPipe();
//
//    if (m_pNullHmdLatest) { delete m_pNullHmdLatest; m_pNullHmdLatest = nullptr; }
//    if (m_pController) { delete m_pController; m_pController = nullptr; }
//    if (m_pController2) { delete m_pController2; m_pController2 = nullptr; }
//}
//
//void CServerDriver_Sample::RunFrame() {
//    if (m_pNullHmdLatest && g_enableHmd) m_pNullHmdLatest->RunFrame();
//    if (m_pController && g_enableLeft) m_pController->RunFrame();
//    if (m_pController2 && g_enableRight) m_pController2->RunFrame();
//}











































#include "cserverdriver_sample.h"
#include "settings.h" 

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>
#include <iostream>
#include <cstring>

using namespace vr;

HANDLE g_hPipe = INVALID_HANDLE_VALUE;
Packet ReceivedPacket = { 0 };
const char* g_pipeName = "\\\\.\\pipe\\GlassVR";
ULONGLONG g_lastPipeAttempt = 0;

bool TryConnectPipe() {
    if (g_hPipe != INVALID_HANDLE_VALUE) {
        return true;
    }

    g_hPipe = CreateFileA(
        g_pipeName,
        GENERIC_READ,
        0,
        NULL,
        OPEN_EXISTING,
        0,
        NULL
    );

    if (g_hPipe == INVALID_HANDLE_VALUE) {
        return false;
    }

    DWORD dwMode = PIPE_NOWAIT;
    if (!SetNamedPipeHandleState(g_hPipe, &dwMode, NULL, NULL)) {
        CloseHandle(g_hPipe);
        g_hPipe = INVALID_HANDLE_VALUE;
        return false;
    }

    return true;
}

void CleanupPipe() {
    if (g_hPipe != INVALID_HANDLE_VALUE) {
        CloseHandle(g_hPipe);
        g_hPipe = INVALID_HANDLE_VALUE;
    }
}

void UpdatePoseDataFromPipe() {
    if (g_hPipe == INVALID_HANDLE_VALUE) {
        ULONGLONG now = GetTickCount64();
        if (now - g_lastPipeAttempt > 2000) {
            g_lastPipeAttempt = now;
            g_hPipe = CreateFileA(g_pipeName, GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);

            if (g_hPipe != INVALID_HANDLE_VALUE) {
                DWORD dwMode = PIPE_NOWAIT;
                SetNamedPipeHandleState(g_hPipe, &dwMode, NULL, NULL);
            }
        }
        return;
    }

    DWORD bytesAvailable = 0;
    if (PeekNamedPipe(g_hPipe, NULL, 0, NULL, &bytesAvailable, NULL)) {
        if (bytesAvailable >= sizeof(Packet)) {
            int packetCount = bytesAvailable / sizeof(Packet);
            DWORD bytesRead;

            for (int i = 0; i < packetCount; i++) {
                if (!ReadFile(g_hPipe, &ReceivedPacket, sizeof(Packet), &bytesRead, NULL)) {
                    CleanupPipe();
                    return;
                }
            }
        }
    }
    else {
        CleanupPipe();
    }
}

bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
bool enable_left = GetBoolFromSettingsByKey("enable cl");
bool enable_right = GetBoolFromSettingsByKey("enable cr");

EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
{
    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);

    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
    enable_left = GetBoolFromSettingsByKey("enable cl");
    enable_right = GetBoolFromSettingsByKey("enable cr");

    ReceivedPacket.hmd_rot_w = 1.0;

    TryConnectPipe();

    if (enable_hmd) {
        m_pNullHmdLatest = new CSampleDeviceDriver();
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pNullHmdLatest->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_HMD,
            m_pNullHmdLatest
        );
    }

    if (enable_left) {
        m_pController = new CSampleControllerDriver();
        m_pController->SetControllerIndex(false);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pController->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_Controller,
            m_pController
        );
    }

    if (enable_right) {
        m_pController2 = new CSampleControllerDriver();
        m_pController2->SetControllerIndex(true);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pController2->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_Controller,
            m_pController2
        );
    }

    return VRInitError_None;
}

void CServerDriver_Sample::Cleanup()
{
    CleanupPipe();

    if (enable_hmd) {
        delete m_pNullHmdLatest;
        m_pNullHmdLatest = NULL;
    }

    if (enable_left) {
        delete m_pController;
        m_pController = NULL;
    }

    if (enable_right) {
        delete m_pController2;
        m_pController2 = NULL;
    }
}

void CServerDriver_Sample::RunFrame()
{
    UpdatePoseDataFromPipe();

    if (m_pNullHmdLatest && enable_hmd) {
        m_pNullHmdLatest->UpdateData(ReceivedPacket);
        m_pNullHmdLatest->RunFrame();
    }

    if (m_pController && enable_left) {
        m_pController->UpdateData(ReceivedPacket);
        m_pController->RunFrame();
    }

    if (m_pController2 && enable_right) {
        m_pController2->UpdateData(ReceivedPacket);
        m_pController2->RunFrame();
    }
}