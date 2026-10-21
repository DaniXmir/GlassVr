#include "comm.h"
#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstring>
#include <setupapi.h>
#include <devguid.h>

#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "setupapi.lib")

namespace {
    template <class T>
    bool CopyPacket(T& dst, const void* src, size_t len) {
        if (len < sizeof(T)) return false;
        memcpy(&dst, src, sizeof(T));
        return true;
    }

    std::string FindComPortByBluetoothName(const std::string& btName) {
        HDEVINFO hDevInfo = SetupDiGetClassDevsA(&GUID_DEVCLASS_PORTS, NULL, NULL, DIGCF_PRESENT);
        if (hDevInfo == INVALID_HANDLE_VALUE) return "";

        SP_DEVINFO_DATA devInfoData;
        devInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

        for (DWORD i = 0; SetupDiEnumDeviceInfo(hDevInfo, i, &devInfoData); i++) {
            char friendlyName[256] = { 0 };
            SetupDiGetDeviceRegistryPropertyA(hDevInfo, &devInfoData, SPDRP_FRIENDLYNAME, NULL, (PBYTE)friendlyName, sizeof(friendlyName), NULL);

            std::string name(friendlyName);
            std::string nameLower = name;
            std::string btNameLower = btName;
            std::transform(nameLower.begin(), nameLower.end(), nameLower.begin(), ::tolower);
            std::transform(btNameLower.begin(), btNameLower.end(), btNameLower.begin(), ::tolower);

            if (nameLower.find(btNameLower) != std::string::npos) {
                size_t start = name.find("COM");
                if (start != std::string::npos) {
                    size_t end = name.find(")", start);
                    SetupDiDestroyDeviceInfoList(hDevInfo);
                    return (end != std::string::npos) ? name.substr(start, end - start) : name.substr(start);
                }
            }
        }
        SetupDiDestroyDeviceInfoList(hDevInfo);
        return "";
    }
}

bool CommManager::Store::ApplyText(const char* line) {
    if (strlen(line) < 3) return false;
    char tag[4] = { line[0], line[1], line[2], '\0' };

    if (strncmp(tag, "skl", 3) == 0) {
        PacketSkeletal temp_skl = skl;
        const char* ptr = line + 3;
        while (*ptr) {
            while (*ptr == ' ') ptr++;
            if (!*ptr) break;
            const char* eq = strchr(ptr, '=');
            if (!eq) break;
            std::string key(ptr, eq - ptr);
            const char* valStart = eq + 1;
            const char* valEnd = valStart;
            while (*valEnd && *valEnd != ' ' && *valEnd != '\n' && *valEnd != '\r') valEnd++;
            std::string val(valStart, valEnd - valStart);

            try {
                float fval = std::stof(val);
                if (key == "thumb") temp_skl.flexions[0] = fval;
                else if (key == "index") temp_skl.flexions[4] = fval;
                else if (key == "middle") temp_skl.flexions[8] = fval;
                else if (key == "ring") temp_skl.flexions[12] = fval;
                else if (key == "pinky") temp_skl.flexions[16] = fval;
                else if (key == "thumb_splay") temp_skl.splays[0] = fval;
                else if (key == "index_splay") temp_skl.splays[1] = fval;
                else if (key == "middle_splay") temp_skl.splays[2] = fval;
                else if (key == "ring_splay") temp_skl.splays[3] = fval;
                else if (key == "pinky_splay") temp_skl.splays[4] = fval;
            }
            catch (...) {}
            ptr = valEnd;
        }
        skl = temp_skl;
        return true;
    }

    if (strncmp(tag, "pos", 3) == 0) {
        PacketPos temp_pos = pos;
        const char* ptr = line + 3;
        while (*ptr) {
            while (*ptr == ' ') ptr++;
            if (!*ptr) break;
            const char* eq = strchr(ptr, '=');
            if (!eq) break;
            std::string key(ptr, eq - ptr);
            const char* valStart = eq + 1;
            const char* valEnd = valStart;
            while (*valEnd && *valEnd != ' ' && *valEnd != '\n' && *valEnd != '\r') valEnd++;
            try {
                float fval = std::stof(std::string(valStart, valEnd - valStart));
                if (key == "x") temp_pos.x = fval;
                else if (key == "y") temp_pos.y = fval;
                else if (key == "z") temp_pos.z = fval;
            }
            catch (...) {}
            ptr = valEnd;
        }
        pos = temp_pos;
        return true;
    }

    if (strncmp(tag, "rot", 3) == 0) {
        PacketRot temp_rot = rot;
        const char* ptr = line + 3;
        while (*ptr) {
            while (*ptr == ' ') ptr++;
            if (!*ptr) break;
            const char* eq = strchr(ptr, '=');
            if (!eq) break;
            std::string key(ptr, eq - ptr);
            const char* valStart = eq + 1;
            const char* valEnd = valStart;
            while (*valEnd && *valEnd != ' ' && *valEnd != '\n' && *valEnd != '\r') valEnd++;
            try {
                float fval = std::stof(std::string(valStart, valEnd - valStart));
                if (key == "w") temp_rot.w = fval;
                else if (key == "x") temp_rot.x = fval;
                else if (key == "y") temp_rot.y = fval;
                else if (key == "z") temp_rot.z = fval;
            }
            catch (...) {}
            ptr = valEnd;
        }
        rot = temp_rot;
        return true;
    }
    return false;
}

bool CommManager::Store::Apply(const char* tag, const void* data, size_t len) {
    if (!strncmp(tag, "pos", 3)) return CopyPacket(pos, data, len);
    if (!strncmp(tag, "rot", 3)) return CopyPacket(rot, data, len);
    if (!strncmp(tag, "idx", 3)) return CopyPacket(idx, data, len);
    if (!strncmp(tag, "ifm", 3)) return CopyPacket(ifm, data, len);
    if (!strncmp(tag, "ive", 3)) return CopyPacket(ive, data, len);
    if (!strncmp(tag, "itc", 3)) return CopyPacket(itc, data, len);
    if (!strncmp(tag, "skl", 3)) return CopyPacket(skl, data, len);
    if (!strncmp(tag, "ext", 3)) return CopyPacket(ext, data, len);
    return false;
}

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

    int reuse = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse));

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

    std::string pipeName = "\\\\.\\pipe\\UDP_RELAY_" + std::to_string(port);
    HANDLE hPipe = CreateNamedPipeA(pipeName.c_str(), PIPE_ACCESS_OUTBOUND, PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_NOWAIT, 1, 1024, 1024, 0, NULL);

    m_sockets.push_back(sock);
    m_pipeHandles[sock] = hPipe;
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
        if (t.joinable()) CancelSynchronousIo(t.native_handle());
    }
    for (auto& t : m_threads) {
        if (t.joinable()) t.detach();
    }
    m_threads.clear();
}

void CommManager::UdpThreadLoop(SOCKET sock) {
    char buf[512];
    int addrLen = sizeof(sockaddr_in);
    sockaddr_in from;
    HANDLE hPipe = m_pipeHandles[sock];

    while (m_bIsRunning) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);
        timeval tv = { 0, 100000 };

        if (select(0, &readfds, NULL, NULL, &tv) > 0 && FD_ISSET(sock, &readfds)) {
            int bytes = recvfrom(sock, buf, sizeof(buf), 0, (SOCKADDR*)&from, &addrLen);
            if (bytes > 0) {
                if (hPipe != INVALID_HANDLE_VALUE) {
                    DWORD bytesWritten;
                    if (!WriteFile(hPipe, buf, bytes, &bytesWritten, NULL)) {
                        DisconnectNamedPipe(hPipe);
                        ConnectNamedPipe(hPipe, NULL);
                    }
                }
                if (bytes > 3) {
                    std::lock_guard<std::mutex> lock(m_mutex);
                    m_udp.Apply(buf, buf + 3, (size_t)bytes - 3);
                }
            }
        }
    }
    if (hPipe != INVALID_HANDLE_VALUE) CloseHandle(hPipe);
}

void CommManager::PipeThreadLoop(std::string pipeName) {
    std::string tag;
    size_t us = pipeName.find_last_of('_');
    if (us != std::string::npos) {
        tag = pipeName.substr(us + 1);
        std::transform(tag.begin(), tag.end(), tag.begin(), [](unsigned char c) { return (char)std::tolower(c); });
    }
    if (tag.size() != 3) return;

    while (m_bIsRunning) {
        HANDLE hPipe = CreateFileA(pipeName.c_str(), GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
        if (hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        char buffer[1024];
        DWORD bytesRead, bytesAvailable = 0;
        while (m_bIsRunning) {
            if (PeekNamedPipe(hPipe, NULL, 0, NULL, &bytesAvailable, NULL)) {
                if (bytesAvailable > 0) {
                    if (ReadFile(hPipe, buffer, sizeof(buffer), &bytesRead, NULL) && bytesRead > 0) {
                        std::lock_guard<std::mutex> lock(m_mutex);
                        m_pipe.Apply(tag.c_str(), buffer, bytesRead);
                    }
                    else break;
                }
                else {
                    std::this_thread::sleep_for(std::chrono::milliseconds(2));
                }
            }
            else break;
        }
        CloseHandle(hPipe);
    }
}

void CommManager::CheckAndUpdateSerialPort(const std::string& devicePrefix, const std::string& mode) {
    std::string btNameKey = devicePrefix + " " + mode + " bluetooth name";
    std::string commPortKey = devicePrefix + " " + mode + " comm port";

    std::string btName = GetStringFromSettingsByKey(btNameKey);
    std::string commPort = GetStringFromSettingsByKey(commPortKey);
    std::string targetPort = commPort;

    if (!btName.empty()) {
        std::string foundPort = FindComPortByBluetoothName(btName);
        if (!foundPort.empty()) targetPort = foundPort;
    }

    if (!targetPort.empty() && targetPort != m_currentSerialPort) {
        RestartSerialThread(targetPort);
    }
}

void CommManager::RestartSerialThread(const std::string& portName) {
    m_serialRunning = false;
    if (m_serialThread.joinable()) m_serialThread.join();
    m_currentSerialPort = portName;
    m_serialRunning = true;
    m_serialThread = std::thread(&CommManager::SerialThreadLoop, this, portName);
}

void CommManager::SerialThreadLoop(std::string portName) {
    std::string fullPath = portName;
    if (fullPath.find("\\\\.\\") != 0) fullPath = "\\\\.\\" + fullPath;

    while (m_serialRunning) {
        HANDLE hComm = CreateFileA(fullPath.c_str(), GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
        if (hComm == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        DCB dcb = { 0 };
        dcb.DCBlength = sizeof(dcb);
        if (GetCommState(hComm, &dcb)) {
            dcb.BaudRate = CBR_115200;
            dcb.ByteSize = 8;
            dcb.StopBits = ONESTOPBIT;
            dcb.Parity = NOPARITY;
            SetCommState(hComm, &dcb);
        }

        char buffer[1024];
        DWORD bytesRead;
        std::string lineBuffer;

        while (m_serialRunning) {
            if (ReadFile(hComm, buffer, sizeof(buffer) - 1, &bytesRead, NULL) && bytesRead > 0) {
                buffer[bytesRead] = '\0';
                lineBuffer += buffer;
                size_t pos;
                while ((pos = lineBuffer.find('\n')) != std::string::npos) {
                    std::string line = lineBuffer.substr(0, pos);
                    lineBuffer.erase(0, pos + 1);
                    if (!line.empty() && line.back() == '\r') line.pop_back();
                    if (!line.empty()) {
                        std::lock_guard<std::mutex> lock(m_mutex);
                        m_serial.ApplyText(line.c_str());
                    }
                }
            }
            else {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        }
        CloseHandle(hComm);
    }
}