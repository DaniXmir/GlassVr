#include "cstracker.h"
#include "basics.h"
#include <math.h>

using namespace vr;

CSampleTracker::CSampleTracker()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;
    m_nTrackerIndex = 0;
}

void CSampleTracker::SetTrackerIndex(int32_t TrackerIndex)
{
    m_nTrackerIndex = TrackerIndex;
}

CSampleTracker::~CSampleTracker()
{
}

vr::EVRInitError CSampleTracker::Activate(vr::TrackedDeviceIndex_t unObjectId)
{
    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, Prop_DeviceClass_Int32, TrackedDeviceClass_GenericTracker);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ModelNumber_String, "Vive Tracker");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ManufacturerName_String, "HTC");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_RenderModelName_String, "{htc}vr_tracker_vive_1_0");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ControllerType_String, "vive_tracker");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_TrackingSystemName_String, "VR Tracker");

    std::string Serial = GetSerialNumber();
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_SerialNumber_String, Serial.c_str());

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, Prop_ControllerRoleHint_Int32, TrackedControllerRole_OptOut);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_InputProfilePath_String, "{htc}/input/vive_tracker_profile.json");

    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/click", &m_hSystemButton);

    m_bThreadRunning = true;
    m_pPipeThread = new std::thread(&CSampleTracker::PipeThreadThreadEntry, this);

    return VRInitError_None;
}

void CSampleTracker::Deactivate()
{
    m_bThreadRunning = false;
    if (m_hPipe != INVALID_HANDLE_VALUE) {
        CancelIoEx(m_hPipe, NULL);
    }
    if (m_pPipeThread) {
        if (m_pPipeThread->joinable()) m_pPipeThread->join();
        delete m_pPipeThread;
        m_pPipeThread = nullptr;
    }
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
}

void CSampleTracker::EnterStandby() {}

void* CSampleTracker::GetComponent(const char* pchComponentNameAndVersion)
{
    return NULL;
}

void CSampleTracker::PowerOff() {}

void CSampleTracker::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) pchResponseBuffer[0] = 0;
}

vr::DriverPose_t CSampleTracker::GetPose()
{
    vr::DriverPose_t pose = { 0 };
    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = true;

    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    {
        std::lock_guard<std::mutex> lock(m_poseMutex);
        pose.vecPosition[0] = m_poseDataCache.pos_x;
        pose.vecPosition[1] = m_poseDataCache.pos_y;
        pose.vecPosition[2] = m_poseDataCache.pos_z;

        pose.qRotation.w = m_poseDataCache.rot_w;
        pose.qRotation.x = m_poseDataCache.rot_x;
        pose.qRotation.y = m_poseDataCache.rot_y;
        pose.qRotation.z = m_poseDataCache.rot_z;
    }
    return pose;
}

void CSampleTracker::RunFrame()
{
#if defined(_WINDOWS)
    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
#endif
}

void CSampleTracker::ProcessEvent(const vr::VREvent_t& vrEvent)
{
    
}

std::string CSampleTracker::GetSerialNumber() const
{
    return "TRK" + std::to_string(m_nTrackerIndex) + "Serial";
}

void CSampleTracker::UpdateData(const PacketTracker& data)
{
    m_poseDataCache = data;
}

void CSampleTracker::PipeThreadThreadEntry()
{
    std::string pipeName = "\\\\.\\pipe\\GlassVR_Tracker_" + std::to_string(m_nTrackerIndex);

    while (m_bThreadRunning)
    {
        m_hPipe = CreateFileA(pipeName.c_str(), GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);

        if (m_hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        PacketTracker incomingData;
        DWORD bytesRead;
        while (m_bThreadRunning)
        {
            bool bSuccess = ReadFile(m_hPipe, &incomingData, sizeof(PacketTracker), &bytesRead, NULL);

            if (bSuccess && bytesRead == sizeof(PacketTracker)) {
                std::lock_guard<std::mutex> lock(m_poseMutex);
                m_poseDataCache = incomingData;
            }
            else {
                break;
            }
        }
        CloseHandle(m_hPipe);
        m_hPipe = INVALID_HANDLE_VALUE;
    }
}