#include "comm.h"
#pragma comment(lib, "Ws2_32.lib")

CommManager::CommManager() : m_bIsRunning(true) {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
}

CommManager::~CommManager() {
    StopAll();
    WSACleanup();
}

bool CommManager::AddUDP(int port) {
    SOCKET sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) return false;

    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sock, (SOCKADDR*)&addr, sizeof(addr)) == SOCKET_ERROR) {
        closesocket(sock);
        return false;
    }

    u_long mode = 1;
    ioctlsocket(sock, FIONBIO, &mode);

    m_sockets.push_back(sock);
    m_threads.emplace_back(&CommManager::UdpThreadLoop, this, sock);
    return true;
}

void CommManager::AddPipe(const std::string& pipeName) {
    m_threads.emplace_back(&CommManager::PipeThreadLoop, this, pipeName);
}

void CommManager::StopAll() {
    m_bIsRunning = false;

    for (SOCKET sock : m_sockets) {
        if (sock != INVALID_SOCKET) closesocket(sock);
    }
    m_sockets.clear();

    for (auto& t : m_threads) {
        if (t.joinable()) t.join();
    }
    m_threads.clear();
}

void CommManager::UdpThreadLoop(SOCKET sock) {
    char buf[512];
    int addrLen = sizeof(sockaddr_in);
    sockaddr_in from;

    while (m_bIsRunning) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);

        timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 100000;

        int result = select(0, &readfds, NULL, NULL, &tv);
        if (result > 0 && FD_ISSET(sock, &readfds)) {
            int bytes = recvfrom(sock, buf, sizeof(buf), 0, (SOCKADDR*)&from, &addrLen);
            if (bytes > 0) {
                std::lock_guard<std::mutex> lock(m_mutex);

                if (buf[0] == 'P' && bytes >= sizeof(PacketPos) + 1) {
                    memcpy(&m_udpPos, &buf[1], sizeof(PacketPos));
                }
                else if (buf[0] == 'R' && bytes >= sizeof(PacketRot) + 1) {
                    memcpy(&m_udpRot, &buf[1], sizeof(PacketRot));
                }
                else if (buf[0] == 'I' && bytes >= sizeof(PacketInputIndex) + 1) {
                    memcpy(&m_udpInput, &buf[1], sizeof(PacketInputIndex));
                }
                else if (buf[0] == 'S' && bytes >= sizeof(PacketSkeletal) + 1) {
                    memcpy(&m_udpSkeletal, &buf[1], sizeof(PacketSkeletal));
                }
            }
        }
    }
}

void CommManager::PipeThreadLoop(std::string pipeName) {
    while (m_bIsRunning) {
        HANDLE hPipe = CreateFileA(pipeName.c_str(), GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
        if (hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        char buffer[1024];
        DWORD bytesRead;

        while (m_bIsRunning) {
            if (ReadFile(hPipe, buffer, sizeof(buffer), &bytesRead, NULL) && bytesRead > 0) {
                std::lock_guard<std::mutex> lock(m_mutex);

                if (pipeName.find("_Pos") != std::string::npos && bytesRead == sizeof(PacketPos)) {
                    memcpy(&m_pipePos, buffer, sizeof(PacketPos));
                }
                else if (pipeName.find("_Rot") != std::string::npos && bytesRead == sizeof(PacketRot)) {
                    memcpy(&m_pipeRot, buffer, sizeof(PacketRot));
                }
                else if (pipeName.find("_Input") != std::string::npos && bytesRead == sizeof(PacketInputIndex)) {
                    memcpy(&m_pipeInput, buffer, sizeof(PacketInputIndex));
                }
                else if (pipeName.find("_Skeletal") != std::string::npos && bytesRead == sizeof(PacketSkeletal)) {
                    memcpy(&m_pipeSkeletal, buffer, sizeof(PacketSkeletal));
                }
            }
            else {
                break;
            }
        }
        CloseHandle(hPipe);
    }
}