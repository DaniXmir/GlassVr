#pragma once
#ifndef CVIVECONTROLLERDRIVER_H
#define CVIVECONTROLLERDRIVER_H

#include "controllerbase.h"
#include "controllerinput.h"

class CViveControllerDriver : public ControllerBase
{
public:
    explicit CViveControllerDriver(bool right);
    virtual ~CViveControllerDriver();

    const char* GetTypeId() const override { return "vive"; }

protected:
    const char* GetSerialPrefix() const override { return "GlassVRViveCon"; }
    void SetupProperties(vr::PropertyContainerHandle_t container) override;
    void CreateInputComponents(vr::PropertyContainerHandle_t container) override;
    void UpdateInput(const PacketSkeletal& skeletal) override;

    bool WantsSkeleton() const override { return false; }

private:
    controllerinput::Handles m_components;
};

#endif