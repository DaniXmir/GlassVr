#ifndef COMM_H
#define COMM_H

#include "packets.h"
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

    PacketPos GetUdpPos() { std::lock_guard<std::mutex> l(m_mutex); return m_udpPos; }
    PacketRot GetUdpRot() { std::lock_guard<std::mutex> l(m_mutex); return m_udpRot; }

    PacketPos GetPipePos() { std::lock_guard<std::mutex> l(m_mutex); return m_pipePos; }
    PacketRot GetPipeRot() { std::lock_guard<std::mutex> l(m_mutex); return m_pipeRot; }

    PacketInputIndex GetUdpInput() { std::lock_guard<std::mutex> lock(m_mutex); return m_udpInput; }
    PacketInputIndex GetPipeInput() { std::lock_guard<std::mutex> lock(m_mutex); return m_pipeInput; }

    PacketSkeletal GetUdpSkeletal() { std::lock_guard<std::mutex> lock(m_mutex); return m_udpSkeletal; }
    PacketSkeletal GetPipeSkeletal() { std::lock_guard<std::mutex> lock(m_mutex); return m_pipeSkeletal; }

private:
    void UdpThreadLoop(SOCKET sock);
    void PipeThreadLoop(std::string pipeName);

    std::map<SOCKET, HANDLE> m_pipeHandles;

    std::mutex m_mutex;
    std::atomic<bool> m_bIsRunning;

    std::vector<std::thread> m_threads;
    std::vector<SOCKET> m_sockets;

    PacketPos m_udpPos = { 0, 0, 0 };
    PacketRot m_udpRot = { 1, 0, 0, 0 };

    PacketPos m_pipePos = { 0, 0, 0 };
    PacketRot m_pipeRot = { 1, 0, 0, 0 };

    PacketInputIndex m_udpInput = { 0 };
    PacketInputIndex m_pipeInput = { 0 };

    PacketSkeletal m_udpSkeletal = { 0 };
    PacketSkeletal m_pipeSkeletal = { 0 };

    PacketExtra m_udpExtra = { 0 };
    PacketExtra m_pipeExtra = { 0 };
};

#endif