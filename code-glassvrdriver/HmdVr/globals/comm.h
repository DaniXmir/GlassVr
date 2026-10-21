#ifndef COMM_H
#define COMM_H

#include "packets.h"
#include "settings.h"
#include <winsock2.h>
#include <mutex>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <windows.h>
#include <map>

class CommManager {
public:
    CommManager();
    ~CommManager();

    bool AddUDP(int port);
    void AddPipe(const std::string& pipeName);
    void StopAll();

    void CheckAndUpdateSerialPort(const std::string& devicePrefix, const std::string& mode);

#define COMM_GETTERS(Type, Name, Field) \
    Type GetUdp##Name()  { std::lock_guard<std::mutex> l(m_mutex); return m_udp.Field; } \
    Type GetPipe##Name() { std::lock_guard<std::mutex> l(m_mutex); return m_pipe.Field; } \
    Type GetSerial##Name() { std::lock_guard<std::mutex> l(m_mutex); return m_serial.Field; }

    COMM_GETTERS(PacketPos, Pos, pos)
        COMM_GETTERS(PacketRot, Rot, rot)
        COMM_GETTERS(PacketInputIndex, Input, idx)
        COMM_GETTERS(PacketInputFrame, InputFrame, ifm)
        COMM_GETTERS(PacketInputVive, InputVive, ive)
        COMM_GETTERS(PacketInputTouch, InputTouch, itc)
        COMM_GETTERS(PacketSkeletal, Skeletal, skl)
        COMM_GETTERS(PacketExtra, Extra, ext)
#undef COMM_GETTERS

private:
    struct Store {
        PacketPos        pos{ 0, 0, 0 };
        PacketRot        rot{ 1, 0, 0, 0 };
        PacketInputIndex idx{};
        PacketInputFrame ifm{};
        PacketInputVive  ive{};
        PacketInputTouch itc{};
        PacketSkeletal   skl{};
        PacketExtra      ext{};

        bool Apply(const char* tag, const void* data, size_t len);
        bool ApplyText(const char* line);
    };

    void UdpThreadLoop(SOCKET sock);
    void PipeThreadLoop(std::string pipeName);
    void SerialThreadLoop(std::string portName);
    void RestartSerialThread(const std::string& portName);

    std::map<SOCKET, HANDLE> m_pipeHandles;
    std::mutex m_mutex;
    std::atomic<bool> m_bIsRunning;

    std::vector<std::thread> m_threads;
    std::vector<SOCKET> m_sockets;

    Store m_udp;
    Store m_pipe;
    Store m_serial;

    std::string m_currentSerialPort;
    std::thread m_serialThread;
    std::atomic<bool> m_serialRunning{ false };
};

#endif