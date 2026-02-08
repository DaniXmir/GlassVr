//AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
// help plz!!!!!!!!!!! skeletal input is bugged
//https://github.com/LucidVR/opengloves-driver/blob/develop/driver/src/device/drivers/knuckle_device_driver.cpp
//https://github.com/SDraw/driver_leap/blob/master/driver_leap/Devices/Controller/CLeapIndexController.cpp
//https://github.com/spayne/soft_knuckles/blob/master/soft_knuckles_device.cpp
//https://github.com/HadesVR/HadesVR/blob/main/Software/Driver/src/samples/driver_HadesVR/src/driver_main.cpp
#include "csamplecontrollerdriver.h"
#include "settings.h" 
#include <math.h>
#include <string>

using namespace vr;

static HmdQuaternion_t HmdQuaternion_Init(double w, double x, double y, double z)
{
    HmdQuaternion_t quat;
    quat.w = w;
    quat.x = x;
    quat.y = y;
    quat.z = z;
    return quat;
}

CSampleControllerDriver::CSampleControllerDriver()
{
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;
    m_compHaptic = vr::k_ulInvalidInputComponentHandle;
    m_HSkeletal = vr::k_ulInvalidInputComponentHandle;

    for (int i = 0; i < 13; i++) {
        m_HButtons[i] = vr::k_ulInvalidInputComponentHandle;
    }
    for (int i = 0; i < 10; i++) {
        m_HAnalog[i] = vr::k_ulInvalidInputComponentHandle;
    }

    m_poseDataCache = { 0 };
    right = 0;
}

void CSampleControllerDriver::SetControllerIndex(int32_t CtrlIndex)
{
    right = CtrlIndex;
}

CSampleControllerDriver::~CSampleControllerDriver()
{
}

vr::EVRInitError CSampleControllerDriver::Activate(vr::TrackedDeviceIndex_t unObjectId)
{
    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ControllerType_String, "knuckles");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ModelNumber_String, "Knuckles EV3.0");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_ManufacturerName_String, "Valve");
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, vr::Prop_WillDriftInYaw_Bool, false);
    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_DeviceClass_Int32, vr::TrackedDeviceClass_Controller);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_RenderModelName_String,
        right ? "{indexcontroller}valve_controller_knu_1_0_right" : "{indexcontroller}valve_controller_knu_1_0_left");

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_SerialNumber_String, GetSerialNumber().c_str());
    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_ControllerRoleHint_Int32,
        right ? vr::TrackedControllerRole_RightHand : vr::TrackedControllerRole_LeftHand);

    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_InputProfilePath_String, "{indexcontroller}/input/index_controller_profile.json");

    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/a/click", &m_HButtons[0]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/b/click", &m_HButtons[1]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/click", &m_HButtons[2]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/system/touch", &m_HButtons[3]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trigger/click", &m_HButtons[4]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trackpad/touch", &m_HButtons[5]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/grip/click", &m_HButtons[6]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/grip/touch", &m_HButtons[6]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/thumbstick/click", &m_HButtons[7]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/thumbstick/touch", &m_HButtons[8]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/a/touch", &m_HButtons[9]);
    vr::VRDriverInput()->CreateBooleanComponent(m_ulPropertyContainer, "/input/trackpad/click", &m_HButtons[11]);

    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/thumbstick/x", &m_HAnalog[0], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/thumbstick/y", &m_HAnalog[1], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trigger/value", &m_HAnalog[2], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/x", &m_HAnalog[3], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/y", &m_HAnalog[4], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/trackpad/force", &m_HAnalog[5], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/grip/force", &m_HAnalog[6], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/grip/value", &m_HAnalog[7], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);

    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/index", &m_HAnalog[8], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/middle", &m_HAnalog[8], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/ring", &m_HAnalog[8], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
    vr::VRDriverInput()->CreateScalarComponent(m_ulPropertyContainer, "/input/finger/pinky", &m_HAnalog[8], vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);

    vr::VRProperties()->SetInt32Property(m_ulPropertyContainer, vr::Prop_Axis0Type_Int32, vr::k_eControllerAxis_Joystick);

    if (right == false) {
        vr::VRDriverInput()->CreateSkeletonComponent(
            m_ulPropertyContainer,
            "/input/skeleton/left",
            "/skeleton/hand/left",
            "/pose/raw",
            vr::VRSkeletalTracking_Partial,
            nullptr,
            0U,
            &m_HSkeletal
        );
    }
    else {
        vr::VRDriverInput()->CreateSkeletonComponent(
            m_ulPropertyContainer,
            "/input/skeleton/right",
            "/skeleton/hand/right",
            "/pose/raw",
            vr::VRSkeletalTracking_Partial,
            nullptr,
            0U,
            &m_HSkeletal
        );
    }

    vr::VRDriverInput()->CreateHapticComponent(m_ulPropertyContainer, "/output/haptic", &m_compHaptic);

    m_bThreadRunning = true;
    m_pPipeThread = new std::thread(&CSampleControllerDriver::PipeThreadThreadEntry, this);

    return VRInitError_None;
}

void CSampleControllerDriver::Deactivate()
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

void CSampleControllerDriver::EnterStandby()
{
}

void* CSampleControllerDriver::GetComponent(const char* pchComponentNameAndVersion)
{
    return NULL;
}

void CSampleControllerDriver::PowerOff()
{
}

void CSampleControllerDriver::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {
        pchResponseBuffer[0] = 0;
    }
}

//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
static uint32_t g_foundTrackers[vr::k_unMaxTrackedDeviceCount];
static uint32_t g_trackerCount = 0;
static int g_selectedIndex = 0;//GetIntFromSettingsByKey("hmd index");

static void UpdateTrackers() {
    g_trackerCount = 0;
    for (uint32_t i = 0; i < vr::k_unMaxTrackedDeviceCount; i++) {
        g_foundTrackers[g_trackerCount] = i;
        g_trackerCount++;
    }
}

static vr::HmdQuaternion_t GetRotationFromMatrix(const vr::HmdMatrix34_t& matrix) {
    vr::HmdQuaternion_t q;
    q.w = sqrt(fmax(0, 1 + matrix.m[0][0] + matrix.m[1][1] + matrix.m[2][2])) / 2;
    q.x = sqrt(fmax(0, 1 + matrix.m[0][0] - matrix.m[1][1] - matrix.m[2][2])) / 2;
    q.y = sqrt(fmax(0, 1 - matrix.m[0][0] + matrix.m[1][1] - matrix.m[2][2])) / 2;
    q.z = sqrt(fmax(0, 1 - matrix.m[0][0] - matrix.m[1][1] + matrix.m[2][2])) / 2;
    q.x = _copysign(q.x, matrix.m[2][1] - matrix.m[1][2]);
    q.y = _copysign(q.y, matrix.m[0][2] - matrix.m[2][0]);
    q.z = _copysign(q.z, matrix.m[1][0] - matrix.m[0][1]);
    return q;
}

static void RotateVectorByQuat(const vr::HmdQuaternion_t& q, const float vIn[3], double vOut[3]) {
    float x = q.x, y = q.y, z = q.z, w = q.w;
    float vx = vIn[0], vy = vIn[1], vz = vIn[2];

    vOut[0] = vx * (1 - 2 * y * y - 2 * z * z) + vy * (2 * x * y - 2 * w * z) + vz * (2 * x * z + 2 * w * y);
    vOut[1] = vx * (2 * x * y + 2 * w * z) + vy * (1 - 2 * x * x - 2 * z * z) + vz * (2 * y * z - 2 * w * x);
    vOut[2] = vx * (2 * x * z - 2 * w * y) + vy * (2 * y * z + 2 * w * x) + vz * (1 - 2 * x * x - 2 * y * y);
}

static vr::HmdQuaternion_t QuatMul(const vr::HmdQuaternion_t& q, const vr::HmdQuaternion_t& r) {
    vr::HmdQuaternion_t res;
    res.w = q.w * r.w - q.x * r.x - q.y * r.y - q.z * r.z;
    res.x = q.w * r.x + q.x * r.w + q.y * r.z - q.z * r.y;
    res.y = q.w * r.y - q.x * r.z + q.y * r.w + q.z * r.x;
    res.z = q.w * r.z + q.x * r.y - q.y * r.x + q.z * r.w;
    return res;
}

static vr::HmdQuaternion_t EulerToQuatZYX(float roll, float yaw, float pitch) {
    float cr = cos(roll * 0.5f);  float sr = sin(roll * 0.5f);
    float cy = cos(yaw * 0.5f);   float sy = sin(yaw * 0.5f);
    float cp = cos(pitch * 0.5f); float sp = sin(pitch * 0.5f);

    vr::HmdQuaternion_t q;
    q.w = cr * cy * cp + sr * sy * sp;
    q.x = cr * cy * sp - sr * sy * cp;
    q.y = cr * sy * cp + sr * cy * sp;
    q.z = sr * cy * cp - cr * sy * sp;
    return q;
}

vr::DriverPose_t CSampleControllerDriver::GetPose()
{
    UpdateTrackers();
    std::string device = right ? "cr" : "cl";

    vr::DriverPose_t pose = { 0 };
    pose.poseIsValid = true;
    pose.result = vr::TrackingResult_Running_OK;
    pose.deviceIsConnected = true;
    pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
    pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

    std::string posmode = GetStringFromSettingsByKey(device + "pos mode");
    std::string rotmode = GetStringFromSettingsByKey(device + "rot mode");

    vr::TrackedDevicePose_t rawPoses[vr::k_unMaxTrackedDeviceCount];
    vr::VRServerDriverHost()->GetRawTrackedDevicePoses(0, rawPoses, vr::k_unMaxTrackedDeviceCount);

    //pos here///////////////////////////////////////////////////////
    if (posmode == "redirect") {
        int tracker_pos_idx = GetIntFromSettingsByKey(device + "pos index");

        if (tracker_pos_idx >= 0 && tracker_pos_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_pos_idx].bPoseIsValid)
        {
            auto& m = rawPoses[tracker_pos_idx].mDeviceToAbsoluteTracking;
            vr::HmdQuaternion_t device_rotation = GetRotationFromMatrix(m);

            float offset_local[3] = {
                GetFloatFromSettingsByKey(device + " offset local x"),
                GetFloatFromSettingsByKey(device + " offset local y"),
                GetFloatFromSettingsByKey(device + " offset local z")
            };

            double rotated_local_offset[3];
            RotateVectorByQuat(device_rotation, offset_local, rotated_local_offset);

            float offset_world[3] = {
                GetFloatFromSettingsByKey(device + " offset world x"),
                GetFloatFromSettingsByKey(device + " offset world y"),
                GetFloatFromSettingsByKey(device + " offset world z")
            };

            pose.vecPosition[0] = m.m[0][3] + rotated_local_offset[0] + offset_world[0];
            pose.vecPosition[1] = m.m[1][3] + rotated_local_offset[1] + offset_world[1];
            pose.vecPosition[2] = m.m[2][3] + rotated_local_offset[2] + offset_world[2];

            pose.vecVelocity[0] = rawPoses[tracker_pos_idx].vVelocity.v[0];
            pose.vecVelocity[1] = rawPoses[tracker_pos_idx].vVelocity.v[1];
            pose.vecVelocity[2] = rawPoses[tracker_pos_idx].vVelocity.v[2];
        }
        else {
            pose.vecPosition[0] = 0.0f;
            pose.vecPosition[1] = 0.0f;
            pose.vecPosition[2] = 0.0f;
        }
    }
    else if (posmode == "test") {
        //
    }
    else {
        pose.vecPosition[0] = m_poseDataCache.pos_x;
        pose.vecPosition[1] = m_poseDataCache.pos_y;
        pose.vecPosition[2] = m_poseDataCache.pos_z;
    }

    //rot here///////////////////////////////////////////////////////
    if (rotmode == "redirect") {
        int tracker_rot_idx = GetIntFromSettingsByKey(device + "rot index");

        if (tracker_rot_idx >= 0 && tracker_rot_idx < vr::k_unMaxTrackedDeviceCount && rawPoses[tracker_rot_idx].bPoseIsValid)
        {
            auto& m = rawPoses[tracker_rot_idx].mDeviceToAbsoluteTracking;
            vr::HmdQuaternion_t device_rotation = GetRotationFromMatrix(m);

            vr::HmdQuaternion_t offset_local_rotation = EulerToQuatZYX(
                GetFloatFromSettingsByKey(device + " offset local roll"),
                GetFloatFromSettingsByKey(device + " offset local yaw"),
                GetFloatFromSettingsByKey(device + " offset local pitch")
            );

            vr::HmdQuaternion_t offset_world_rotation = EulerToQuatZYX(
                GetFloatFromSettingsByKey(device + " offset world roll"),
                GetFloatFromSettingsByKey(device + " offset world yaw"),
                GetFloatFromSettingsByKey(device + " offset world pitch")
            );

            vr::HmdQuaternion_t combined = QuatMul(offset_world_rotation, device_rotation);
            pose.qRotation = QuatMul(combined, offset_local_rotation);

            pose.vecAngularVelocity[0] = rawPoses[tracker_rot_idx].vAngularVelocity.v[0];
            pose.vecAngularVelocity[1] = rawPoses[tracker_rot_idx].vAngularVelocity.v[1];
            pose.vecAngularVelocity[2] = rawPoses[tracker_rot_idx].vAngularVelocity.v[2];
        }
        else {
            pose.qRotation.w = 1.0f;
            pose.qRotation.x = 0.0f;
            pose.qRotation.y = 0.0f;
            pose.qRotation.z = 0.0f;
        }
    }
    else if (rotmode == "test") {
        //
    }
    else {
        pose.qRotation.w = m_poseDataCache.rot_w;
        pose.qRotation.x = m_poseDataCache.rot_x;
        pose.qRotation.y = m_poseDataCache.rot_y;
        pose.qRotation.z = m_poseDataCache.rot_z;
    }

    pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");

    std::lock_guard<std::mutex> lock(m_poseMutex);
    return pose;
}
//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void CSampleControllerDriver::UpdateSkeletalInput(bool isGripClosed)
{
    VRBoneTransform_t boneTransforms[31];

    for (int i = 0; i < 31; i++) {
        boneTransforms[i].position.v[0] = 0.0f;
        boneTransforms[i].position.v[1] = 0.0f;
        boneTransforms[i].position.v[2] = 0.0f;
        boneTransforms[i].position.v[3] = 1.0f;

        boneTransforms[i].orientation.w = 1.0f;
        boneTransforms[i].orientation.x = 0.0f;
        boneTransforms[i].orientation.y = 0.0f;
        boneTransforms[i].orientation.z = 0.0f;
    }

    float curlAngle = isGripClosed ? 1.2f : 0.0f;

    for (int finger = 0; finger < 5; finger++) {
        int baseIndex = 2 + (finger * 4);
        for (int joint = 0; joint < 3; joint++) {
            int boneIndex = baseIndex + joint + 1;
            if (boneIndex < 31) {
                float angle = curlAngle * (joint + 1) / 3.0f;
                boneTransforms[boneIndex].orientation.w = cos(angle / 2.0f);
                boneTransforms[boneIndex].orientation.x = sin(angle / 2.0f);
                boneTransforms[boneIndex].orientation.y = 0.0f;
                boneTransforms[boneIndex].orientation.z = 0.0f;
            }
        }
    }

    vr::VRDriverInput()->UpdateSkeletonComponent(m_HSkeletal, vr::VRSkeletalMotionRange_WithController, boneTransforms, 31);
    vr::VRDriverInput()->UpdateSkeletonComponent(m_HSkeletal, vr::VRSkeletalMotionRange_WithoutController, boneTransforms, 31);
}

void CSampleControllerDriver::RunFrame()
{
    const float TRIGGER_CLICK_THRESHOLD = 0.9f;

    float thumbX = m_poseDataCache.joy_x;
    float thumbY = m_poseDataCache.joy_y;
    float trackpadX = m_poseDataCache.touch_x;
    float trackpadY = m_poseDataCache.touch_y;
    float triggerValue = m_poseDataCache.trigger;
    bool isGripPressed = m_poseDataCache.grip;
    bool isTrackpadClicked = m_poseDataCache.touch_btn;

    bool isTriggerPressed = (triggerValue > TRIGGER_CLICK_THRESHOLD);
    bool isThumbTouched = m_poseDataCache.joy_btn || (fabs(thumbX) > 0.01f) || (fabs(thumbY) > 0.01f);
    bool isTrackpadTouched = isTrackpadClicked || (fabs(trackpadX) > 0.01f) || (fabs(trackpadY) > 0.01f);
    float gripValue = isGripPressed ? 1.0f : 0.0f;

    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[0], m_poseDataCache.a, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[1], m_poseDataCache.b, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[2], m_poseDataCache.menu, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[4], isTriggerPressed, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[6], m_poseDataCache.grip, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[7], m_poseDataCache.joy_btn, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[11], m_poseDataCache.touch_btn, 0);

    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[9], m_poseDataCache.a, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[10], m_poseDataCache.b, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[3], m_poseDataCache.menu, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[8], isThumbTouched, 0);
    vr::VRDriverInput()->UpdateBooleanComponent(m_HButtons[5], isTrackpadTouched, 0);

    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[0], thumbX, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[1], thumbY, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[2], triggerValue, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[3], trackpadX, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[4], trackpadY, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[5], isTrackpadClicked ? 1.0f : 0.0f, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[6], gripValue, 0);
    vr::VRDriverInput()->UpdateScalarComponent(m_HAnalog[7], gripValue, 0);

    UpdateSkeletalInput(isGripPressed);

    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        if (right) {
            g_selectedIndex = GetIntFromSettingsByKey("cr index");
        }
        else {
            g_selectedIndex = GetIntFromSettingsByKey("cl index");
        }
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
    }
}

void CSampleControllerDriver::ProcessEvent(const vr::VREvent_t& vrEvent)
{
    switch (vrEvent.eventType) {
    case vr::VREvent_Input_HapticVibration:
        if (vrEvent.data.hapticVibration.componentHandle == m_compHaptic) {
        }
        break;
    }
}

std::string CSampleControllerDriver::GetSerialNumber() const
{
    switch (right) {
    case false:
        return "CTRL1Serial";
    case true:
        return "CTRL2Serial";
    default:
        return "CTRLSerial";
    }
}

void CSampleControllerDriver::UpdateData(const PacketController& data)
{
    m_poseDataCache = data;
}

void CSampleControllerDriver::PipeThreadThreadEntry()
{
    std::string pipeName = right ? "\\\\.\\pipe\\GlassVR_Right" : "\\\\.\\pipe\\GlassVR_Left";

    while (m_bThreadRunning)
    {
        m_hPipe = CreateFileA(
            pipeName.c_str(),
            GENERIC_READ,
            0,
            NULL,
            OPEN_EXISTING,
            0,
            NULL);

        if (m_hPipe == INVALID_HANDLE_VALUE) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        PacketController incomingData;
        DWORD bytesRead;
        while (m_bThreadRunning)
        {
            bool bSuccess = ReadFile(
                m_hPipe,
                &incomingData,
                sizeof(PacketController),
                &bytesRead,
                NULL);

            if (bSuccess && bytesRead == sizeof(PacketController)) {
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