#pragma once
#ifndef CSAMPLECONTROLLERDRIVER_H
#define CSAMPLECONTROLLERDRIVER_H

#include "controllerbase.h"

class CSampleControllerDriver : public ControllerBase
{
public:
    explicit CSampleControllerDriver(bool right);
    virtual ~CSampleControllerDriver();

    const char* GetTypeId() const override { return "index"; }

protected:
    const char* GetSerialPrefix() const override { return "GlassVRIndexCon"; }
    void SetupProperties(vr::PropertyContainerHandle_t container) override;
    void CreateInputComponents(vr::PropertyContainerHandle_t container) override;
    void UpdateInput(const PacketSkeletal& skeletal) override;
    void OnDisable() override;

private:
    void PushInput(const PacketInputIndex& input, const PacketSkeletal& skeletal);

    vr::VRInputComponentHandle_t m_HButtons[13];
    vr::VRInputComponentHandle_t m_HAnalog[12];
};

#endif
