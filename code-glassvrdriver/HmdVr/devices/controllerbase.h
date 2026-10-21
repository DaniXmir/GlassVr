#pragma once

#include "openvr_driver.h"
#include <string>

#include "hand_simulation.h"
#include "packets.h"

class ControllerBase : public vr::ITrackedDeviceServerDriver
{
public:
    explicit ControllerBase(bool right);
    virtual ~ControllerBase();

    vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
    void Deactivate() override;
    void EnterStandby() override {}
    void* GetComponent(const char* pchComponentNameAndVersion) override { return nullptr; }
    void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
    vr::DriverPose_t GetPose() override;

    void RunFrame();
    void ProcessEvent(const vr::VREvent_t& vrEvent);
    void PowerOff() {}

    void Enable();
    void Disable();
    bool IsDisabled() const { return m_disabled; }

    bool IsRight() const { return m_right; }
    std::string GetSerialNumber() const;

    virtual const char* GetTypeId() const = 0;

protected:
    virtual const char* GetSerialPrefix() const = 0;

    virtual void SetupProperties(vr::PropertyContainerHandle_t container) = 0;

    virtual void CreateInputComponents(vr::PropertyContainerHandle_t container) = 0;

    virtual bool WantsSkeleton() const { return true; }

    virtual void UpdateInput(const PacketSkeletal& skeletal) {}

    virtual void OnDisable() {}
    virtual void OnEnable() {}

    std::string DeviceKey() const { return m_right ? "cr" : "cl"; }

    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;
    bool m_right;
    bool m_disabled;

private:
    void UpdateSkeleton(const PacketSkeletal& packet);

    vr::VRInputComponentHandle_t m_HSkeletal;
    vr::VRInputComponentHandle_t m_compHaptic;

    MyHandSimulation m_handSimulation;
};
