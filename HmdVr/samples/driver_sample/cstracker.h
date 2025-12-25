#ifndef CSAMPLETRACKER_H
#define CSAMPLETRACKER_H

#include <openvr_driver.h>
#include <string>
#include <thread>
#include <mutex>
#include <windows.h>

#pragma pack(push, 1)
struct PacketTracker {
    double pos_x, pos_y, pos_z;
    double rot_w, rot_x, rot_y, rot_z;
};
#pragma pack(pop)

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

    void UpdateData(const PacketTracker& data);

    void PipeThreadThreadEntry();

private:
    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    int32_t m_nTrackerIndex;

    vr::VRInputComponentHandle_t m_hSystemButton;

    PacketTracker m_poseDataCache;

    std::thread* m_pPipeThread = nullptr;
    bool m_bThreadRunning = false;
    std::mutex m_poseMutex;
    HANDLE m_hPipe = INVALID_HANDLE_VALUE;

};

#endif