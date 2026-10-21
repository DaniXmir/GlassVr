#include "controllerslot.h"
#include "controllerbase.h"
#include "controllerregistry.h"
#include "settings.h"

#include <openvr_driver.h>

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

ControllerSlot::ControllerSlot(bool right)
    : m_right(right)
{
}

ControllerSlot::~ControllerSlot()
{
    Shutdown();
}

void ControllerSlot::Sync()
{
    const bool enabled = GetBoolFromSettingsByKey(m_right ? "enable cr" : "enable cl");

    if (!enabled) {
        if (m_active) m_active->Disable();
        return;
    }

    std::string wanted = ControllerRegistry::Normalize(GetStringFromSettingsByKey("con type"));
    if (!ControllerRegistry::IsKnown(wanted)) {
        wanted = m_activeType.empty() ? ControllerRegistry::DefaultType() : m_activeType;
    }

    if (m_active && m_activeType == wanted) {
        m_active->Enable();
        return;
    }

    if (wanted == m_failedType) return;

    if (m_active) {
        m_active->Disable();
        m_active = nullptr;
        m_activeType.clear();
    }

    ControllerBase* next = nullptr;
    auto it = m_controllers.find(wanted);
    if (it != m_controllers.end()) {
        next = it->second;
    }
    else {
        next = ControllerRegistry::Create(wanted, m_right);
        if (!next) {
            m_failedType = wanted;
            return;
        }

        if (!vr::VRServerDriverHost()->TrackedDeviceAdded(
                next->GetSerialNumber().c_str(),
                vr::TrackedDeviceClass_Controller,
                next)) {
            OutputDebugStringA("GlassVR: TrackedDeviceAdded refused a controller\n");
            delete next;
            m_failedType = wanted;
            return;
        }

        m_controllers[wanted] = next;
    }

    m_failedType.clear();
    next->Enable();
    m_active = next;
    m_activeType = wanted;
}

void ControllerSlot::RunFrame()
{
    if (m_active) m_active->RunFrame();
}

void ControllerSlot::Shutdown()
{
    for (auto& kv : m_controllers) {
        delete kv.second;
    }
    m_controllers.clear();
    m_active = nullptr;
    m_activeType.clear();
    m_failedType.clear();
}
