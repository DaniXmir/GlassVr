#ifndef CSAMPLEDEVICEDRIVER_H
#define CSAMPLEDEVICEDRIVER_H

#include <openvr_driver.h>
#include <string> 
#include <cstdint>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

#include "settings.h"
#include "globals.h"

#include "packets.h"
#include "comm.h"

//viture-
#include "viture.h"
//viture-

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

//virtual display
#include <d3d11.h>
#include <dxgi.h>
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "dxgi.lib")


#include <mfapi.h>
#include <mfidl.h>
#include <mferror.h>
#include <wmcodecdsp.h>
#include <codecapi.h>
#include <wrl/client.h>
#pragma comment(lib, "mfplat.lib")
#pragma comment(lib, "mfuuid.lib")
#pragma comment(lib, "wmcodecdspuuid.lib")

#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")

#include <chrono>

using Microsoft::WRL::ComPtr;
//virtual display

class CSampleDeviceDriver : public vr::ITrackedDeviceServerDriver, public vr::IVRDisplayComponent, public vr::IVRVirtualDisplay
{
public:
    CSampleDeviceDriver();
    virtual ~CSampleDeviceDriver();

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
    virtual vr::DistortionCoordinates_t ComputeDistortion(vr::EVREye eEye, float fU, float fV) override;
    virtual bool ComputeInverseDistortion(vr::HmdVector2_t* pA, vr::EVREye eEye, uint32_t unElement, float fU, float fV) override;

    virtual void Present(const vr::PresentInfo_t* pPresentInfo, uint32_t unPresentInfoSize) override;
    virtual void WaitForPresent() override;
    virtual bool GetTimeSinceLastVsync(float* pfSecondsSinceLastVsync, uint64_t* pulFrameCounter) override;
    virtual bool InitializeStreaming();
    void RunFrame();
    std::string GetSerialNumber() const { return m_sSerialNumber; }

    double m_fVsyncPeriod = 0.0;
    double m_dNextVsyncTime = 0.0;
    ID3D11Texture2D* m_pLocalTexture = nullptr;

private:
    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    std::string m_sSerialNumber;
    std::string m_sModelNumber;

    //viture-
    Viture* m_pVitureDevice = nullptr;
    //viture-

    //connections
    CommManager m_comm;

    PacketPos pipe_pos;
    PacketRot pipe_rot;

    PacketPos udp_pos;
    PacketRot udp_rot;
    //connections

    int32_t m_nWindowX;
    int32_t m_nWindowY;
    uint32_t m_nWindowWidth;
    uint32_t m_nWindowHeight;
    uint32_t m_nRenderWidth;
    uint32_t m_nRenderHeight;
    float m_flSecondsFromVsyncToPhotons;
    float m_flDisplayFrequency;
    float m_flIPD;

    //viture-
    bool m_poseInitialized = false;
    vr::HmdQuaternion_t m_startupInverse = { 1, 0, 0, 0 };

    bool m_6dofRecenterPending = false;
    //viture-

    //virtual display
    bool InitializeD3D11();
    void StreamWorkerThread();

    ID3D11Device* m_pD3D11Device = nullptr;
    ID3D11DeviceContext* m_pD3D11Context = nullptr;

    std::mutex m_textureMutex;
    ID3D11Texture2D* m_pSharedTexture = nullptr;
    HANDLE m_hLastTextureHandle = nullptr;

    std::atomic<uint64_t> m_nCurrentFrameId{ 0 };

    double m_flLastVsyncTimeInSeconds = 0.0;
    uint64_t m_nVsyncCounter = 0;

    ID3D11Texture2D* m_pStagingTexture = nullptr;
    HANDLE m_hVideoPipe = INVALID_HANDLE_VALUE;
    bool m_bPipeConnected = false;

    std::thread m_streamThread;
    std::mutex m_streamMutex;
    std::condition_variable m_streamCv;
    std::atomic<bool> m_bRunning{ false };
    std::atomic<bool> m_bFramePending{ false };
    //virtual display
};

#endif