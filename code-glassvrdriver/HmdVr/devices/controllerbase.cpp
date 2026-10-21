#include "controllerbase.h"
#include "controllerdata.h"
#include "settings.h"
#include "globals.h"
#include "skeletaloverride.h"

#include <math.h>
#include <string>
#include <cstdarg>
#include <cstdio>
#include <memory>
#include <mutex>
#include <type_traits>

using namespace vr;

namespace {

    void Trace(const char* fmt, ...)
    {
        char buf[256];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buf, sizeof(buf) - 2, fmt, args);
        va_end(args);
        size_t n = strlen(buf);
        buf[n] = '\n'; buf[n + 1] = 0;
        VRDriverLog()->Log(buf);
    }

    HmdQuaternion_t QuatIdentity()
    {
        HmdQuaternion_t q;
        q.w = 1; q.x = 0; q.y = 0; q.z = 0;
        return q;
    }

    HmdQuaternion_t GetRotationFromMatrix(const HmdMatrix34_t& matrix)
    {
        HmdQuaternion_t q;
        q.w = sqrt(fmax(0, 1 + matrix.m[0][0] + matrix.m[1][1] + matrix.m[2][2])) / 2;
        q.x = sqrt(fmax(0, 1 + matrix.m[0][0] - matrix.m[1][1] - matrix.m[2][2])) / 2;
        q.y = sqrt(fmax(0, 1 - matrix.m[0][0] + matrix.m[1][1] - matrix.m[2][2])) / 2;
        q.z = sqrt(fmax(0, 1 - matrix.m[0][0] - matrix.m[1][1] + matrix.m[2][2])) / 2;
        q.x = _copysign(q.x, matrix.m[2][1] - matrix.m[1][2]);
        q.y = _copysign(q.y, matrix.m[0][2] - matrix.m[2][0]);
        q.z = _copysign(q.z, matrix.m[1][0] - matrix.m[0][1]);
        return q;
    }

    int GetTrackerIndexBySerial(const std::string& targetSerial)
    {
        if (targetSerial.empty()) return -1;

        for (uint32_t i = 0; i < k_unMaxTrackedDeviceCount; i++) {
            PropertyContainerHandle_t container = VRProperties()->TrackedDeviceToPropertyContainer(i);
            if (container == k_ulInvalidPropertyContainer) continue;

            char serialBuf[256];
            ETrackedPropertyError err;
            VRProperties()->GetStringProperty(container, Prop_SerialNumber_String, serialBuf, sizeof(serialBuf), &err);

            if (err == TrackedProp_Success && targetSerial == serialBuf) {
                return (int)i;
            }
        }
        return -1;
    }

}

ControllerBase::ControllerBase(bool right)
{
    m_right = right;
    m_disabled = false;
    m_unObjectId = k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = k_ulInvalidPropertyContainer;
    m_HSkeletal = k_ulInvalidInputComponentHandle;
    m_compHaptic = k_ulInvalidInputComponentHandle;

    static std::once_flag s_handBonesOnce;
    std::call_once(s_handBonesOnce, [this]() {
        auto sim = std::make_shared<std::decay_t<decltype(m_handSimulation)>>();
        auto lock = std::make_shared<std::mutex>();

        glassvr::hooks::SetHandBoneComputer(
            [sim, lock](ETrackedControllerRole role, const float* c, const float* s, VRBoneTransform_t* out) {
                MyFingerCurls curls = { c[0], c[1], c[2], c[3], c[4] };
                MyFingerSplays splays = { s[0], s[1], s[2], s[3], s[4] };

                std::lock_guard<std::mutex> guard(*lock);
                sim->ComputeSkeletonTransforms(role, curls, splays, out);
            });
        });
}

ControllerBase::~ControllerBase()
{
}

std::string ControllerBase::GetSerialNumber() const
{
    return std::string(GetSerialPrefix()) + (m_right ? "Right" : "Left");
}

EVRInitError ControllerBase::Activate(TrackedDeviceIndex_t unObjectId)
{
    const std::string serial = GetSerialNumber();
    Trace("[ctrl] %s Activate begin (id %u)", serial.c_str(), (unsigned)unObjectId);

    m_unObjectId = unObjectId;
    m_ulPropertyContainer = VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);
    const PropertyContainerHandle_t c = m_ulPropertyContainer;

    ControllerDataHub::Get().Ensure(m_right);
    Trace("[ctrl] %s hub ready", serial.c_str());

    VRProperties()->SetBoolProperty(c, Prop_WillDriftInYaw_Bool, false);
    VRProperties()->SetInt32Property(c, Prop_DeviceClass_Int32, TrackedDeviceClass_Controller);
    VRProperties()->SetStringProperty(c, Prop_SerialNumber_String, serial.c_str());
    VRProperties()->SetInt32Property(c, Prop_ControllerRoleHint_Int32,
        m_right ? TrackedControllerRole_RightHand : TrackedControllerRole_LeftHand);
    Trace("[ctrl] %s common props set", serial.c_str());

    SetupProperties(c);
    Trace("[ctrl] %s type props set", serial.c_str());

    CreateInputComponents(c);
    Trace("[ctrl] %s input components created", serial.c_str());

    if (WantsSkeleton()) {
        EVRInputError e = VRDriverInput()->CreateSkeletonComponent(
            c,
            m_right ? "/input/skeleton/right" : "/input/skeleton/left",
            m_right ? "/skeleton/hand/right" : "/skeleton/hand/left",
            "/pose/raw",
            VRSkeletalTracking_Full,
            nullptr,
            0U,
            &m_HSkeletal
        );
        Trace("[ctrl] %s skeleton create result %d (handle %llu)", serial.c_str(), (int)e, (unsigned long long)m_HSkeletal);
    }

    EVRInputError h = VRDriverInput()->CreateHapticComponent(c, "/output/haptic", &m_compHaptic);
    Trace("[ctrl] %s haptic create result %d", serial.c_str(), (int)h);

    Trace("[ctrl] %s Activate end", serial.c_str());
    return VRInitError_None;
}

void ControllerBase::Deactivate()
{
    m_unObjectId = k_unTrackedDeviceIndexInvalid;
}

void ControllerBase::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {
        pchResponseBuffer[0] = 0;
    }
}

void ControllerBase::Enable()
{
    if (!m_disabled) return;
    m_disabled = false;
    OnEnable();
}

void ControllerBase::Disable()
{
    if (m_disabled) return;
    m_disabled = true;
    OnDisable();

    if (m_unObjectId != k_unTrackedDeviceIndexInvalid) {
        VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
}

DriverPose_t ControllerBase::GetPose() {
    DriverPose_t pose = { 0 };
    pose.qWorldFromDriverRotation = QuatIdentity();
    pose.qDriverFromHeadRotation = QuatIdentity();

    if (m_disabled) {
        pose.qRotation = QuatIdentity();
        pose.poseIsValid = false;
        pose.deviceIsConnected = false;
        pose.result = TrackingResult_Uninitialized;
        return pose;
    }

    const std::string device = DeviceKey();
    pose.poseIsValid = true;
    pose.result = TrackingResult_Running_OK;
    pose.deviceIsConnected = GetBoolFromSettingsByKey(m_right ? "enable cr" : "enable cl");

    const std::string posmode = GetStringFromSettingsByKey(device + "pos mode");
    const std::string rotmode = GetStringFromSettingsByKey(device + "rot mode");

    TrackedDevicePose_t rawPoses[k_unMaxTrackedDeviceCount];
    VRServerDriverHost()->GetRawTrackedDevicePoses(0, rawPoses, k_unMaxTrackedDeviceCount);

    ControllerDataHub& hub = ControllerDataHub::Get();

    float raw_px = 0.0f, raw_py = 0.0f, raw_pz = 0.0f;
    float raw_rx = 0.0f, raw_ry = 0.0f, raw_rz = 0.0f, raw_rw = 1.0f;

    if (posmode == "copy") {
        std::string targetSerial = GetStringFromSettingsByKey(device + "pos copy serial");
        int tracker_pos_idx = GetTrackerIndexBySerial(targetSerial);
        if (tracker_pos_idx >= 0 && tracker_pos_idx < (int)k_unMaxTrackedDeviceCount && rawPoses[tracker_pos_idx].bPoseIsValid) {
            auto& m = rawPoses[tracker_pos_idx].mDeviceToAbsoluteTracking;
            raw_px = m.m[0][3]; raw_py = m.m[1][3]; raw_pz = m.m[2][3];
            pose.vecVelocity[0] = rawPoses[tracker_pos_idx].vVelocity.v[0];
            pose.vecVelocity[1] = rawPoses[tracker_pos_idx].vVelocity.v[1];
            pose.vecVelocity[2] = rawPoses[tracker_pos_idx].vVelocity.v[2];
        }
    }
    else if (posmode == "serial" || posmode == "bluetooth") {
        PacketPos p = hub.GetSerialPos(device);
        raw_px = (float)p.x; raw_py = (float)p.y; raw_pz = (float)p.z;
    }
    else {
        PacketPos p = hub.GetPos(m_right, posmode == "UDP");
        raw_px = (float)p.x; raw_py = (float)p.y; raw_pz = (float)p.z;
    }

    if (rotmode == "copy") {
        std::string targetRotSerial = GetStringFromSettingsByKey(device + "rot copy serial");
        int tracker_rot_idx = GetTrackerIndexBySerial(targetRotSerial);
        if (tracker_rot_idx >= 0 && tracker_rot_idx < (int)k_unMaxTrackedDeviceCount && rawPoses[tracker_rot_idx].bPoseIsValid) {
            auto& m = rawPoses[tracker_rot_idx].mDeviceToAbsoluteTracking;
            HmdQuaternion_t device_rotation = GetRotationFromMatrix(m);
            raw_rx = (float)device_rotation.x; raw_ry = (float)device_rotation.y;
            raw_rz = (float)device_rotation.z; raw_rw = (float)device_rotation.w;
            pose.vecAngularVelocity[0] = rawPoses[tracker_rot_idx].vAngularVelocity.v[0];
            pose.vecAngularVelocity[1] = rawPoses[tracker_rot_idx].vAngularVelocity.v[1];
            pose.vecAngularVelocity[2] = rawPoses[tracker_rot_idx].vAngularVelocity.v[2];
        }
    }
    else if (rotmode == "serial" || rotmode == "bluetooth") {
        PacketRot r = hub.GetSerialRot(device);
        raw_rx = (float)r.x; raw_ry = (float)r.y; raw_rz = (float)r.z; raw_rw = (float)r.w;
    }
    else {
        PacketRot r = hub.GetRot(m_right, rotmode == "UDP");
        raw_rx = (float)r.x; raw_ry = (float)r.y; raw_rz = (float)r.z; raw_rw = (float)r.w;
    }

    Transform FinalTransform = GetNewTransform(device, raw_px, raw_py, raw_pz, raw_rx, raw_ry, raw_rz, raw_rw);

    pose.vecPosition[0] = FinalTransform.pos_x;
    pose.vecPosition[1] = FinalTransform.pos_y;
    pose.vecPosition[2] = FinalTransform.pos_z;

    pose.qRotation.w = FinalTransform.rot_w;
    pose.qRotation.x = FinalTransform.rot_x;
    pose.qRotation.y = FinalTransform.rot_y;
    pose.qRotation.z = FinalTransform.rot_z;

    pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");
    return pose;
}

void ControllerBase::UpdateSkeleton(const PacketSkeletal& packet)
{
    if (m_HSkeletal == k_ulInvalidInputComponentHandle) return;

    VRBoneTransform_t boneTransforms[31];
    for (int i = 0; i < 31; i++) {
        boneTransforms[i].position = { 0.f, 0.f, 0.f, 1.f };
        boneTransforms[i].orientation = { 1.f, 0.f, 0.f, 0.f }; // w, x, y, z
    }

    MyFingerCurls curls = {
        (float)packet.flexions[0],//thumb
        (float)packet.flexions[4],//index
        (float)packet.flexions[8],//middle
        (float)packet.flexions[12],//ring
        (float)packet.flexions[16]//pinky
    };

    MyFingerSplays splays = {
        (float)packet.splays[0],
        (float)packet.splays[1],
        (float)packet.splays[2],
        (float)packet.splays[3],
        (float)packet.splays[4]
    };

    ETrackedControllerRole role = m_right ? TrackedControllerRole_RightHand : TrackedControllerRole_LeftHand;

    m_handSimulation.ComputeSkeletonTransforms(role, curls, splays, boneTransforms);

    VRDriverInput()->UpdateSkeletonComponent(m_HSkeletal, VRSkeletalMotionRange_WithController, boneTransforms, 31);
    VRDriverInput()->UpdateSkeletonComponent(m_HSkeletal, VRSkeletalMotionRange_WithoutController, boneTransforms, 31);
}

void ControllerBase::RunFrame() {
    if (m_disabled || m_unObjectId == k_unTrackedDeviceIndexInvalid) return;

    static int s_traced = 0;
    const bool trace = (s_traced < 8);
    if (trace) { s_traced++; Trace("[ctrl] %s RunFrame #%d begin", GetSerialNumber().c_str(), s_traced); }

    const std::string device = DeviceKey();

    const std::string posmode = GetStringFromSettingsByKey(device + "pos mode");
    const std::string rotmode = GetStringFromSettingsByKey(device + "rot mode");
    const std::string skeletalMode = GetStringFromSettingsByKey(device + "skeletal mode");
    const std::string inputMode = GetStringFromSettingsByKey(device + "input mode");

    if (posmode == "serial" || posmode == "bluetooth") ControllerDataHub::Get().UpdateSerialPort(device, "pos");
    if (rotmode == "serial" || rotmode == "bluetooth") ControllerDataHub::Get().UpdateSerialPort(device, "rot");
    if (skeletalMode == "serial" || skeletalMode == "bluetooth") ControllerDataHub::Get().UpdateSerialPort(device, "skeletal");
    if (inputMode == "serial" || inputMode == "bluetooth") ControllerDataHub::Get().UpdateSerialPort(device, "input");

    PacketSkeletal skeletal{};
    if (skeletalMode == "serial" || skeletalMode == "bluetooth") {
        skeletal = ControllerDataHub::Get().GetSerialSkeletal(device);
    }
    else {
        const bool skeletalUdp = (skeletalMode == "UDP");
        skeletal = ControllerDataHub::Get().GetSkeletal(m_right, skeletalUdp);
    }

    if (trace) Trace("[ctrl] %s got skeletal", GetSerialNumber().c_str());
    UpdateInput(skeletal);
    if (trace) Trace("[ctrl] %s input updated", GetSerialNumber().c_str());
    UpdateSkeleton(skeletal);
    if (trace) Trace("[ctrl] %s skeleton updated", GetSerialNumber().c_str());

    VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    if (trace) Trace("[ctrl] %s pose pushed", GetSerialNumber().c_str());
}

void ControllerBase::ProcessEvent(const VREvent_t& vrEvent)
{
    switch (vrEvent.eventType) {
    case VREvent_Input_HapticVibration:
        if (vrEvent.data.hapticVibration.componentHandle == m_compHaptic) {
        }
        break;
    }
}