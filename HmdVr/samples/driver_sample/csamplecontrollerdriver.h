#ifndef CSAMPLECONTROLLERDRIVER_H
#define CSAMPLECONTROLLERDRIVER_H

#include "openvr_driver.h"
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <windows.h>

#pragma pack(push, 1)
struct PacketController {
    double pos_x, pos_y, pos_z;
    double rot_w, rot_x, rot_y, rot_z;
    double joy_x, joy_y;
    double touch_x, touch_y;
    double trigger;

    bool a;
    bool b;
    bool menu;
    bool joy_btn;
    bool touch_btn;
    bool grip;
};
#pragma pack(pop)

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

    void UpdateData(const PacketController& data);

private:
    void PipeThreadThreadEntry();
    std::thread* m_pPipeThread = nullptr;
    std::atomic<bool> m_bThreadRunning{ false };
    HANDLE m_hPipe = INVALID_HANDLE_VALUE;
    std::mutex m_poseMutex;

    void UpdateSkeletalInput(bool isGripClosed);

    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    vr::VRInputComponentHandle_t m_HButtons[13];
    vr::VRInputComponentHandle_t m_HAnalog[10];
    vr::VRInputComponentHandle_t m_HSkeletal;

    vr::VRInputComponentHandle_t m_compHaptic;

    int32_t right;

    PacketController m_poseDataCache;
};

#endif