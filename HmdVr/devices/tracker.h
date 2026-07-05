#ifndef CSAMPLETRACKER_H
#define CSAMPLETRACKER_H

#include <openvr_driver.h>
#include <string>
#include <thread>
#include <mutex>

#include "packets.h"
#include "comm.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

class CSampleTracker : public vr::ITrackedDeviceServerDriver
{
public:
    CSampleTracker();
    virtual ~CSampleTracker();

    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
    virtual void Deactivate() override;
    virtual void EnterStandby() override;
    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
    virtual void PowerOff();
    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
    virtual vr::DriverPose_t GetPose() override;

    void RunFrame();
    void ProcessEvent(const vr::VREvent_t& vrEvent);
    void SetTrackerIndex(int32_t TrackerIndex);
    std::string GetSerialNumber() const;

private:
    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    int32_t m_nTrackerIndex;

    vr::VRInputComponentHandle_t m_hSystemButton;

    //connections
    CommManager m_comm;

    PacketPos pipe_pos;
    PacketRot pipe_rot;

    PacketPos udp_pos;
    PacketRot udp_rot;
    //connections
};

#endif