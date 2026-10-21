#pragma once
#ifndef CFRAMECONTROLLERDRIVER_H
#define CFRAMECONTROLLERDRIVER_H

#include "controllerbase.h"
#include <vector>

class CFrameControllerDriver : public ControllerBase
{
public:
    explicit CFrameControllerDriver(bool right);
    virtual ~CFrameControllerDriver();

    const char* GetTypeId() const override { return "frame"; }

protected:
    const char* GetSerialPrefix() const override { return "GlassVRFrameCon"; }
    void SetupProperties(vr::PropertyContainerHandle_t container) override;
    void CreateInputComponents(vr::PropertyContainerHandle_t container) override;
    void UpdateInput(const PacketSkeletal& skeletal) override;

private:
    std::vector<vr::VRInputComponentHandle_t> m_components;
};

#endif
