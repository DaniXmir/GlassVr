#pragma once
#ifndef CTOUCHCONTROLLERDRIVER_H
#define CTOUCHCONTROLLERDRIVER_H

#include "controllerbase.h"

class CTouchControllerDriver : public ControllerBase
{
public:
    explicit CTouchControllerDriver(bool right);
    virtual ~CTouchControllerDriver();

    const char* GetTypeId() const override { return "touch"; }

protected:
    const char* GetSerialPrefix() const override { return "GlassVRTouchCon"; }
    void SetupProperties(vr::PropertyContainerHandle_t container) override;
    void CreateInputComponents(vr::PropertyContainerHandle_t container) override;
    void UpdateInput(const PacketSkeletal& skeletal) override;

private:
    struct TouchHandles {
        vr::VRInputComponentHandle_t joyClick = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t joyTouch = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t joyX = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t joyY = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t triggerTouch = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t triggerValue = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t gripValue = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t thumbrest = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t topClick = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t topTouch = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t botClick = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t botTouch = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t sysClick = vr::k_ulInvalidInputComponentHandle;
        vr::VRInputComponentHandle_t sysClick2 = vr::k_ulInvalidInputComponentHandle;
    } m_h;
};

#endif