#ifndef CONTROLLERDATA_H
#define CONTROLLERDATA_H

#include "packets.h"
#include <string>
#include <mutex>

class CommManager;

class ControllerDataHub {
public:
    static ControllerDataHub& Get();
    static void Shutdown();

    void Ensure(bool right);

    void UpdateSerialPort(const std::string& devicePrefix, const std::string& mode);
    PacketSkeletal GetSerialSkeletal(const std::string& devicePrefix);
    PacketPos GetSerialPos(const std::string& devicePrefix);
    PacketRot GetSerialRot(const std::string& devicePrefix);
    PacketInputIndex GetSerialInputIndex(const std::string& devicePrefix);
    PacketInputFrame GetSerialInputFrame(const std::string& devicePrefix);
    PacketInputVive GetSerialInputVive(const std::string& devicePrefix);
    PacketInputTouch GetSerialInputTouch(const std::string& devicePrefix);

    PacketPos GetPos(bool right, bool udp);
    PacketRot GetRot(bool right, bool udp);
    PacketSkeletal GetSkeletal(bool right, bool udp);
    PacketInputIndex GetInputIndex(bool right, bool udp);
    PacketInputFrame GetInputFrame(bool right, bool udp);
    PacketInputVive GetInputVive(bool right, bool udp);
    PacketInputTouch GetInputTouch(bool right, bool udp);
    PacketExtra GetExtra(bool right, bool udp);

    PacketPos GetPos(bool right, const std::string& mode);
    PacketRot GetRot(bool right, const std::string& mode);
    PacketSkeletal GetSkeletal(bool right, const std::string& mode);
    PacketInputIndex GetInputIndex(bool right, const std::string& mode);
    PacketInputFrame GetInputFrame(bool right, const std::string& mode);
    PacketInputVive GetInputVive(bool right, const std::string& mode);
    PacketInputTouch GetInputTouch(bool right, const std::string& mode);

private:
    ControllerDataHub();
    ~ControllerDataHub();
    CommManager* m_comm[2];
};

#endif