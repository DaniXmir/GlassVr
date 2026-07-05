#pragma once
#ifndef CSAMPLECONTROLLERDRIVER_H
#define CSAMPLECONTROLLERDRIVER_H

#include "openvr_driver.h"
#include <string>
#include <thread>
#include <atomic>
#include <mutex>

#include "hand_simulation.h"

#include "packets.h"
#include "comm.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
{
public:
    CSampleControllerDriver();
    virtual ~CSampleControllerDriver();

    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
    virtual void Deactivate() override;
    virtual void EnterStandby() override;
    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
    virtual vr::DriverPose_t GetPose() override;

    void RunFrame();
    void ProcessEvent(const vr::VREvent_t& vrEvent);
    std::string GetSerialNumber() const;
    void SetControllerIndex(int32_t CtrlIndex);
    void PowerOff();

private:
    void UpdateSkeletalInput(PacketSkeletal& packet);

    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    vr::VRInputComponentHandle_t m_HButtons[13];
    vr::VRInputComponentHandle_t m_HAnalog[12];
    vr::VRInputComponentHandle_t m_HSkeletal;

    vr::VRInputComponentHandle_t m_compHaptic;

    int32_t right;

    //connections
    CommManager m_comm;

    PacketPos pipe_pos;
    PacketRot pipe_rot;

    PacketPos udp_pos;
    PacketRot udp_rot;
    //connections

    //input
    PacketInputIndex pipe_input;
    PacketInputIndex udp_input;

    PacketSkeletal pipe_skeletal;
    PacketSkeletal udp_skeletal;
    //input

    MyHandSimulation m_handSimulation;
};

#endif