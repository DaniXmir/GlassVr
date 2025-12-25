#ifndef CSAMPLEDEVICEDRIVER_H
#define CSAMPLEDEVICEDRIVER_H

#include <openvr_driver.h>
#include "settings.h"
#include <string> 
#include <cstdint>
#include <thread>
#include <atomic>

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

struct PacketHmd {
    double pos_x;
    double pos_y;
    double pos_z;

    double rot_w;
    double rot_x;
    double rot_y;
    double rot_z;

    double ipd;
    double head_to_eye_dist;
};

class CSampleDeviceDriver : public vr::ITrackedDeviceServerDriver, public vr::IVRDisplayComponent
{
public:
    CSampleDeviceDriver();
    virtual ~CSampleDeviceDriver();

    void UpdateData(const PacketHmd& data);

    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
    virtual void Deactivate() override;
    virtual void EnterStandby() override;
    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
    virtual void PowerOff();
    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
    virtual vr::DriverPose_t GetPose() override;

    virtual void GetWindowBounds(int32_t* pnX, int32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight) override;
    virtual bool IsDisplayOnDesktop() override;
    virtual bool IsDisplayRealDisplay() override;
    virtual void GetRecommendedRenderTargetSize(uint32_t* pnWidth, uint32_t* pnHeight) override;
    virtual void GetEyeOutputViewport(vr::EVREye eEye, uint32_t* pnX, uint32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight) override;
    virtual void GetProjectionRaw(vr::EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom) override;

    virtual vr::HmdMatrix34_t GetEyeToHeadTransform(vr::EVREye eEye);
    //*virtual vr::DriverPose_t GetHeadFromEyePose(vr::EVREye eEye);

    virtual vr::DistortionCoordinates_t ComputeDistortion(vr::EVREye eEye, float fU, float fV) override;

    virtual bool ComputeInverseDistortion(vr::HmdVector2_t* pA, vr::EVREye eEye, uint32_t unElement, float fU, float fV) override;

    void RunFrame();
    std::string GetSerialNumber() const { return m_sSerialNumber; }

private:
    void PipeThreadThreadEntry();
    std::thread* m_pPipeThread;
    std::atomic<bool> m_bThreadRunning;
    HANDLE m_hPipe;

    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    std::string m_sSerialNumber;
    std::string m_sModelNumber;

    PacketHmd m_poseDataCache;

    int32_t m_nWindowX;
    int32_t m_nWindowY;
    uint32_t m_nWindowWidth;
    uint32_t m_nWindowHeight;
    uint32_t m_nRenderWidth;
    uint32_t m_nRenderHeight;
    float m_flSecondsFromVsyncToPhotons;
    float m_flDisplayFrequency;
    float m_flIPD;
};

#endif