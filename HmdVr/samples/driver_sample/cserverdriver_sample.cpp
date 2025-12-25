/////thanks https://github.com/r57zone/OpenVR-driver-for-DIY
///m to open legacy hmd monitor

#include "cserverdriver_sample.h"
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <iostream>
#include <cstring>

using namespace vr;

bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");
bool enable_left = GetBoolFromSettingsByKey("enable cl");
bool enable_right = GetBoolFromSettingsByKey("enable cr");

EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
{
    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);

    enable_hmd = GetBoolFromSettingsByKey("enable hmd");
    enable_left = GetBoolFromSettingsByKey("enable cl");
    enable_right = GetBoolFromSettingsByKey("enable cr");

    if (enable_hmd) {
        m_pNullHmdLatest = new CSampleDeviceDriver();
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pNullHmdLatest->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_HMD,
            m_pNullHmdLatest
        );
    }

    if (enable_left) {
        m_pController = new CSampleControllerDriver();
        m_pController->SetControllerIndex(false);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pController->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_Controller,
            m_pController
        );
    }

    if (enable_right) {
        m_pController2 = new CSampleControllerDriver();
        m_pController2->SetControllerIndex(true);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pController2->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_Controller,
            m_pController2
        );
    }

    int trackerCount = GetIntFromSettingsByKey("trackers num");

    for (int i = 0; i < trackerCount; i++) {
        CSampleTracker* pTracker = new CSampleTracker();
        pTracker->SetTrackerIndex(i);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            pTracker->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_GenericTracker,
            pTracker
        );
        m_vecTrackers.push_back(pTracker);
    }

    return VRInitError_None;
}

void CServerDriver_Sample::Cleanup()
{
    if (enable_hmd) {
        delete m_pNullHmdLatest;
        m_pNullHmdLatest = NULL;
    }
    if (enable_left) {
        delete m_pController;
        m_pController = NULL;
    }
    if (enable_right) {
        delete m_pController2;
        m_pController2 = NULL;
    }

    for (auto pTracker : m_vecTrackers) {
        delete pTracker;
    }
    m_vecTrackers.clear();
}

void CServerDriver_Sample::RunFrame()
{
    if (m_pNullHmdLatest && enable_hmd) {
        m_pNullHmdLatest->RunFrame();
    }

    if (m_pController && enable_left) {
        m_pController->RunFrame();
    }

    if (m_pController2 && enable_right) {
        m_pController2->RunFrame();
    }

    for (auto pTracker : m_vecTrackers) {
        pTracker->RunFrame();
    }
}