//TODO: FIX THREADS NOT STOPPING AFTER SHUTDOWN!

////thanks https://github.com/r57zone/OpenVR-driver-for-DIY
//OutputDebugStringA(";P"); //this prints to DebugView log(change capture to Global Win32) very cool!
//m to open legacy hmd monitor

#include "main.h"
#include "controllerdata.h"
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <iostream>
#include <cstring>
#include <algorithm>

using namespace vr;

bool enable_hmd = GetBoolFromSettingsByKey("enable hmd");

EVRInitError CServerDriver_Sample::Init(vr::IVRDriverContext* pDriverContext)
{
    VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);

    glassvr::hooks::Install(pDriverContext);
    glassvr::hooks::overrides::Start();

    enable_hmd = GetBoolFromSettingsByKey("enable hmd");

    if (enable_hmd) {
        m_pNullHmdLatest = new CSampleDeviceDriver();
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pNullHmdLatest->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_HMD,
            m_pNullHmdLatest
        );
    }

    // creates the controller type selected by "con type" for every enabled hand
    m_slotLeft.Sync();
    m_slotRight.Sync();

    int trackerCount = (std::max)(0, GetIntFromSettingsByKey("trackers num"));

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
    glassvr::hooks::overrides::Stop();
    glassvr::hooks::Remove();

    if (m_pNullHmdLatest) {
        delete m_pNullHmdLatest;
        m_pNullHmdLatest = NULL;
    }

    m_slotLeft.Shutdown();
    m_slotRight.Shutdown();
    ControllerDataHub::Shutdown(); // after the controllers are gone

    for (auto pTracker : m_vecTrackers) {
        delete pTracker;
    }
    m_vecTrackers.clear();
}

void CServerDriver_Sample::RunFrame()
{
    if (!enable_hmd && GetBoolFromSettingsByKey("enable hmd")) {
        enable_hmd = true;
        m_pNullHmdLatest = new CSampleDeviceDriver();
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            m_pNullHmdLatest->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_HMD,
            m_pNullHmdLatest
        );
    }

    // "enable cl/cr" scanning + "con type" swapping
    m_slotLeft.Sync();
    m_slotRight.Sync();

    int wantedTrackers = (std::max)(0, GetIntFromSettingsByKey("trackers num"));
    while ((int)m_vecTrackers.size() < wantedTrackers) {
        int newIndex = (int)m_vecTrackers.size();
        CSampleTracker* pTracker = new CSampleTracker();
        pTracker->SetTrackerIndex(newIndex);
        vr::VRServerDriverHost()->TrackedDeviceAdded(
            pTracker->GetSerialNumber().c_str(),
            vr::TrackedDeviceClass_GenericTracker,
            pTracker
        );
        m_vecTrackers.push_back(pTracker);
    }

    if (m_pNullHmdLatest) {
        m_pNullHmdLatest->RunFrame();
    }

    m_slotLeft.RunFrame();
    m_slotRight.RunFrame();

    for (auto pTracker : m_vecTrackers) {
        pTracker->RunFrame();
    }
}

//;P
