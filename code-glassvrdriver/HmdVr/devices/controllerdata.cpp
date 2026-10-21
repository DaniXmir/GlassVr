#include "controllerdata.h"
#include "comm.h"
#include "settings.h"
#include <mutex>
#include <string>

static ControllerDataHub* g_hub = nullptr;
static std::mutex g_hubMutex;

ControllerDataHub::ControllerDataHub() {
    m_comm[0] = nullptr;
    m_comm[1] = nullptr;
}

ControllerDataHub::~ControllerDataHub() {}

ControllerDataHub& ControllerDataHub::Get() {
    static std::once_flag once;
    std::call_once(once, [] { g_hub = new ControllerDataHub(); });
    return *g_hub;
}

void ControllerDataHub::Shutdown() {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    if (!g_hub) return;
    for (int i = 0; i < 2; i++) {
        if (g_hub->m_comm[i]) {
            g_hub->m_comm[i]->StopAll();
            g_hub->m_comm[i] = nullptr;
        }
    }
}

void ControllerDataHub::UpdateSerialPort(const std::string& devicePrefix, const std::string& mode) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) {
        g_hub->m_comm[i]->CheckAndUpdateSerialPort(devicePrefix, mode);
    }
}

PacketSkeletal ControllerDataHub::GetSerialSkeletal(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialSkeletal();
    return PacketSkeletal{};
}

PacketPos ControllerDataHub::GetSerialPos(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialPos();
    return PacketPos{ 0, 0, 0 };
}

PacketRot ControllerDataHub::GetSerialRot(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialRot();
    return PacketRot{ 1, 0, 0, 0 };
}

PacketInputIndex ControllerDataHub::GetSerialInputIndex(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialInput();
    return PacketInputIndex{};
}

PacketInputFrame ControllerDataHub::GetSerialInputFrame(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialInputFrame();
    return PacketInputFrame{};
}

PacketInputVive ControllerDataHub::GetSerialInputVive(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialInputVive();
    return PacketInputVive{};
}

PacketInputTouch ControllerDataHub::GetSerialInputTouch(const std::string& devicePrefix) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    int i = -1;
    if (devicePrefix == "cl" || devicePrefix == "cl ") i = 0;
    else if (devicePrefix == "cr" || devicePrefix == "cr ") i = 1;
    if (i >= 0 && i < 2 && g_hub->m_comm[i]) return g_hub->m_comm[i]->GetSerialInputTouch();
    return PacketInputTouch{};
}

void ControllerDataHub::Ensure(bool right) {
    std::lock_guard<std::mutex> lock(g_hubMutex);
    const int i = right ? 1 : 0;
    if (g_hub->m_comm[i]) return;

    CommManager* comm = new CommManager();
    comm->AddUDP(GetIntFromSettingsByKey(right ? "cr port" : "cl port"));

    const std::string base = std::string("\\\\.\\pipe\\GlassVR_CONTROLLER_") + (right ? "RIGHT" : "LEFT");
    comm->AddPipe(base + "_pos");
    comm->AddPipe(base + "_rot");
    comm->AddPipe(base + "_idx");
    comm->AddPipe(base + "_ifm");
    comm->AddPipe(base + "_ive");
    comm->AddPipe(base + "_itc");
    comm->AddPipe(base + "_skl");
    comm->AddPipe(base + "_ext");

    g_hub->m_comm[i] = comm;
}

PacketPos ControllerDataHub::GetPos(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialPos(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketPos{ 0, 0, 0 };
    return (mode == "UDP") ? c->GetUdpPos() : c->GetPipePos();
}

PacketRot ControllerDataHub::GetRot(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialRot(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketRot{ 1, 0, 0, 0 };
    return (mode == "UDP") ? c->GetUdpRot() : c->GetPipeRot();
}

PacketSkeletal ControllerDataHub::GetSkeletal(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialSkeletal(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketSkeletal{};
    return (mode == "UDP") ? c->GetUdpSkeletal() : c->GetPipeSkeletal();
}

PacketInputIndex ControllerDataHub::GetInputIndex(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialInputIndex(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputIndex{};
    return (mode == "UDP") ? c->GetUdpInput() : c->GetPipeInput();
}

PacketInputFrame ControllerDataHub::GetInputFrame(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialInputFrame(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputFrame{};
    return (mode == "UDP") ? c->GetUdpInputFrame() : c->GetPipeInputFrame();
}

PacketInputVive ControllerDataHub::GetInputVive(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialInputVive(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputVive{};
    return (mode == "UDP") ? c->GetUdpInputVive() : c->GetPipeInputVive();
}

PacketInputTouch ControllerDataHub::GetInputTouch(bool right, const std::string& mode) {
    std::string prefix = right ? "cr" : "cl";
    if (mode == "serial" || mode == "bluetooth") return GetSerialInputTouch(prefix);
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputTouch{};
    return (mode == "UDP") ? c->GetUdpInputTouch() : c->GetPipeInputTouch();
}

PacketPos ControllerDataHub::GetPos(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketPos{ 0, 0, 0 };
    return udp ? c->GetUdpPos() : c->GetPipePos();
}
PacketRot ControllerDataHub::GetRot(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketRot{ 1, 0, 0, 0 };
    return udp ? c->GetUdpRot() : c->GetPipeRot();
}
PacketSkeletal ControllerDataHub::GetSkeletal(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketSkeletal{};
    return udp ? c->GetUdpSkeletal() : c->GetPipeSkeletal();
}
PacketInputIndex ControllerDataHub::GetInputIndex(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputIndex{};
    return udp ? c->GetUdpInput() : c->GetPipeInput();
}
PacketInputFrame ControllerDataHub::GetInputFrame(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputFrame{};
    return udp ? c->GetUdpInputFrame() : c->GetPipeInputFrame();
}
PacketInputVive ControllerDataHub::GetInputVive(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputVive{};
    return udp ? c->GetUdpInputVive() : c->GetPipeInputVive();
}
PacketInputTouch ControllerDataHub::GetInputTouch(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketInputTouch{};
    return udp ? c->GetUdpInputTouch() : c->GetPipeInputTouch();
}
PacketExtra ControllerDataHub::GetExtra(bool right, bool udp) {
    CommManager* c = g_hub->m_comm[right ? 1 : 0];
    if (!c) return PacketExtra{};
    return udp ? c->GetUdpExtra() : c->GetPipeExtra();
}