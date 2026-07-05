//you may see lots of "OutputDebugStringA()" i usually remove unnecessary prints, espesially the one AI love to spawm 
//but virual display component was driving me insane so ill clean them up later
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include "hmd.h"
#include "settings.h" 
#include "basics.h"

#include <math.h>
#include <string>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <limits>
#include <cmath> 
#include <cstring> 
#include <cstdlib>
#include <cstdio>
#include <sstream>
#include <chrono>

#include <sddl.h>

#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

SOCKET m_udpSocket = INVALID_SOCKET;
sockaddr_in m_clientAddr = {};
SOCKET m_tsSocket = INVALID_SOCKET;
sockaddr_in m_tsClientAddr = {};

ComPtr<IMFTransform> m_pVideoEncoder;
ComPtr<ICodecAPI> m_pCodecAPI;
DWORD m_inStreamID = 0, m_outStreamID = 0;

ComPtr<IMFTransform> m_pColorConverter;
DWORD m_convInStreamID = 0, m_convOutStreamID = 0;
ComPtr<ID3D11Texture2D> m_pNV12Texture;
bool m_bConverterProvidesSamples = false;
bool m_bEncoderProvidesSamples = false;
DWORD m_dwEncoderOutputSize = 2 * 1024 * 1024;
std::atomic<bool> m_bStreamingReady = false;
std::atomic<double> m_dLastCaptureTime = 0.0;
std::atomic<int> m_nLastAppliedBitrateMbps = { 0 };

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;
using namespace std;

const float k_fRadFactor = (float)M_PI / 180.0f;

float HeadToEyeDist = 0.0f;
bool Stereoscopic = false;
float ResolutionX = 1920.0f;
float ResolutionY = 1080.0f;
bool FullScreen = false;
float RefreshRate = 90.0f;

//virtual display
static double GetSystemTimeInSeconds()
{
    using namespace std::chrono;
    return duration<double>(system_clock::now().time_since_epoch()).count();
}
//virtual display

CSampleDeviceDriver::CSampleDeviceDriver()
{
    //viture-
    m_pVitureDevice = nullptr;
    //viture-
    m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

    m_flIPD = GetFloatFromSettingsByKey("ipd");
    m_sSerialNumber = "GlassVR_HMD";
    m_sModelNumber = "GlassVR";

    m_flSecondsFromVsyncToPhotons = 0.008f;
    m_flDisplayFrequency = RefreshRate;

    //virtual display
    if (!InitializeD3D11()) {
        OutputDebugStringA("GlassVR: D3D11 device creation failed - virtual display capture unavailable, falling back to extended mode only\n");
    }

    if (!InitializeStreaming()) {
        OutputDebugStringA("GlassVR: Media Foundation Init failed...");
    }

    m_bRunning = true;
    m_streamThread = std::thread(&CSampleDeviceDriver::StreamWorkerThread, this);
    //virtual display
}

//viture-
CSampleDeviceDriver::~CSampleDeviceDriver() {
    if (m_pVitureDevice) {
        delete m_pVitureDevice;
        m_pVitureDevice = nullptr;
    }

    //virtual display
    m_bRunning = false;
    m_streamCv.notify_all();
    if (m_streamThread.joinable()) {
        m_streamThread.join();
    }

    {
        std::lock_guard<std::mutex> lock(m_textureMutex);
        if (m_pSharedTexture) {
            m_pSharedTexture->Release();
            m_pSharedTexture = nullptr;
        }
    }
    if (m_pStagingTexture) {
        m_pStagingTexture->Release();
        m_pStagingTexture = nullptr;
    }
    if (m_pD3D11Context) {
        m_pD3D11Context->Release();
        m_pD3D11Context = nullptr;
    }
    if (m_pD3D11Device) {
        m_pD3D11Device->Release();
        m_pD3D11Device = nullptr;
    }
    //virtual display

    m_pLocalTexture = nullptr;
}
//viture-

EVRInitError CSampleDeviceDriver::Activate(TrackedDeviceIndex_t unObjectId)
{
    Stereoscopic = GetBoolFromSettingsByKey("stereoscopic");
    ResolutionX = GetFloatFromSettingsByKey("resolution x");
    ResolutionY = GetFloatFromSettingsByKey("resolution y");
    FullScreen = GetBoolFromSettingsByKey("fullscreen");
    RefreshRate = GetFloatFromSettingsByKey("refresh rate");
    m_flDisplayFrequency = RefreshRate;

    m_nWindowX = 0;
    m_nWindowY = 0;

    if (Stereoscopic) {
        m_nWindowWidth = (uint32_t)(ResolutionX * 2);
        m_nRenderWidth = (uint32_t)(ResolutionX);
    }
    else {
        m_nWindowWidth = (uint32_t)ResolutionX;
        m_nRenderWidth = (uint32_t)ResolutionX;
    }
    m_nWindowHeight = (uint32_t)ResolutionY;
    m_nRenderHeight = (uint32_t)ResolutionY;

    m_unObjectId = unObjectId;
    m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);

    //needed for VRC for some reason
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_ModelNumber_String, "oculus_hmd");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_ManufacturerName_String, "Oculus");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_RenderModelName_String, "oculus_hmd");
    vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_SerialNumber_String, "GlassVRHmd"); //1WMHH000X00000 stolen serial from alvr lol
    //

    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserIpdMeters_Float, m_flIPD);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, HeadToEyeDist);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency);
    vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons);
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);
    vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_DisplayDebugMode_Bool, !FullScreen);

    //todo: make the headset never sleep
    //vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, vr::Prop_ContainsProximitySensor_Bool, true);

    //virtual display
    uint64_t graphicsAdapterLuid = 0;
    if (m_pD3D11Device)
    {
        IDXGIDevice* pDXGIDevice = nullptr;
        if (SUCCEEDED(m_pD3D11Device->QueryInterface(__uuidof(IDXGIDevice), (void**)&pDXGIDevice)))
        {
            IDXGIAdapter* pAdapter = nullptr;
            if (SUCCEEDED(pDXGIDevice->GetAdapter(&pAdapter)))
            {
                DXGI_ADAPTER_DESC desc;
                if (SUCCEEDED(pAdapter->GetDesc(&desc)))
                {
                    graphicsAdapterLuid = ((uint64_t)(uint32_t)desc.AdapterLuid.HighPart << 32) | (uint32_t)desc.AdapterLuid.LowPart;
                }
                pAdapter->Release();
            }
            pDXGIDevice->Release();
        }
    }
    vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, vr::Prop_GraphicsAdapterLuid_Uint64, graphicsAdapterLuid);
    //virtual display

    //viture-
    m_pVitureDevice = new Viture();
    //viture-

    //connections
    m_comm.AddUDP(GetIntFromSettingsByKey("hmd port"));
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_HMD_Pos");
    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_HMD_Rot");

    m_comm.AddPipe("\\\\.\\pipe\\GlassVR_HMD_Extra");
    //connections

    m_fVsyncPeriod = 1.0 / (double)m_flDisplayFrequency;
    m_dNextVsyncTime = GetSystemTimeInSeconds() + m_fVsyncPeriod;

    return VRInitError_None;
}

void CSampleDeviceDriver::Deactivate()
{
    if (m_pVitureDevice) {
        delete m_pVitureDevice;
        m_pVitureDevice = nullptr;
    }
    m_poseInitialized = false;
    m_startupInverse = { 1, 0, 0, 0 };

    m_bRunning = false;
    m_streamCv.notify_all();
    if (m_streamThread.joinable()) {
        m_streamThread.detach();
    }

    m_comm.StopAll();

    if (m_udpSocket != INVALID_SOCKET) {
        closesocket(m_udpSocket);
        m_udpSocket = INVALID_SOCKET;
    }
    if (m_tsSocket != INVALID_SOCKET) {
        closesocket(m_tsSocket);
        m_tsSocket = INVALID_SOCKET;
    }
    WSACleanup();

    m_pCodecAPI.Reset();

    if (m_pVideoEncoder) {
        m_pVideoEncoder->ProcessMessage(MFT_MESSAGE_NOTIFY_END_OF_STREAM, 0);
        m_pVideoEncoder.Reset();
    }

    if (m_pColorConverter) {
        m_pColorConverter->ProcessMessage(MFT_MESSAGE_NOTIFY_END_OF_STREAM, 0);
        m_pColorConverter.Reset();
    }

    m_pNV12Texture.Reset();
    MFShutdown();

    if (m_pLocalTexture)
    {
        m_pLocalTexture->Release();
        m_pLocalTexture = nullptr;
    }
}

void CSampleDeviceDriver::EnterStandby()
{

}

void CSampleDeviceDriver::PowerOff()
{

}

void* CSampleDeviceDriver::GetComponent(const char* pchComponentNameAndVersion)
{
    std::string displayMode = GetStringFromSettingsByKey("display mode");

    if (!_stricmp(pchComponentNameAndVersion, vr::IVRDisplayComponent_Version)) {
        return (vr::IVRDisplayComponent*)this;
    }
    //virtual display is very slow, do not use!
    if (displayMode == "virtual") {
        if (!_stricmp(pchComponentNameAndVersion, vr::IVRVirtualDisplay_Version)) {
            return (vr::IVRVirtualDisplay*)this;
        }
    }

    return NULL;
}

void CSampleDeviceDriver::DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize)
{
    if (unResponseBufferSize >= 1) {

        pchResponseBuffer[0] = 0;
    }
}

void CSampleDeviceDriver::GetWindowBounds(int32_t* pnX, int32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnX = m_nWindowX;
    *pnY = m_nWindowY;
    *pnWidth = m_nWindowWidth;
    *pnHeight = m_nWindowHeight;
}

bool CSampleDeviceDriver::IsDisplayOnDesktop()
{
    return false;
}

bool CSampleDeviceDriver::IsDisplayRealDisplay()
{
    return false;
}

void CSampleDeviceDriver::GetRecommendedRenderTargetSize(uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnWidth = m_nRenderWidth;
    *pnHeight = m_nRenderHeight;
}

void CSampleDeviceDriver::GetEyeOutputViewport(EVREye eEye, uint32_t* pnX, uint32_t* pnY, uint32_t* pnWidth, uint32_t* pnHeight)
{
    *pnY = m_nWindowY;
    *pnHeight = m_nWindowHeight;

    if (Stereoscopic)
    {
        *pnWidth = m_nWindowWidth / 2;
        if (eEye == Eye_Left)
        {
            *pnX = m_nWindowX;
        }
        else
        {
            *pnX = m_nWindowX + m_nWindowWidth / 2;
        }
    }
    else
    {
        *pnX = m_nWindowX;
        *pnWidth = m_nWindowWidth;
    }
}

void CSampleDeviceDriver::GetProjectionRaw(EVREye eEye, float* pfLeft, float* pfRight, float* pfTop, float* pfBottom)
{
    //todo: add lens correction! and merge stereo/mono

    float k_fAngleOuterH_Deg = 0.0;
    float k_fAngleInnerH_Deg = 0.0;
    float k_fAngleTopV_Deg = 0.0;
    float k_fAngleBottomV_Deg = 0.0;

    if (Stereoscopic) {
        k_fAngleOuterH_Deg = GetFloatFromSettingsByKey("outer stereo");
        k_fAngleInnerH_Deg = GetFloatFromSettingsByKey("inner stereo");
        k_fAngleTopV_Deg = GetFloatFromSettingsByKey("top stereo");
        k_fAngleBottomV_Deg = GetFloatFromSettingsByKey("bottom stereo");
    }
    else {
        k_fAngleOuterH_Deg = GetFloatFromSettingsByKey("outer mono");
        k_fAngleInnerH_Deg = GetFloatFromSettingsByKey("inner mono");
        k_fAngleTopV_Deg = GetFloatFromSettingsByKey("top mono");
        k_fAngleBottomV_Deg = GetFloatFromSettingsByKey("bottom mono");
    }

    float k_fTangentTopV = std::tan(k_fAngleTopV_Deg * k_fRadFactor);
    float k_fTangentBottomV = std::tan(k_fAngleBottomV_Deg * k_fRadFactor);
    float k_fTangentOuterH = std::tan(k_fAngleOuterH_Deg * k_fRadFactor);
    float k_fTangentInnerH = std::tan(k_fAngleInnerH_Deg * k_fRadFactor);

    *pfTop = -k_fTangentTopV;
    *pfBottom = k_fTangentBottomV;

    if (eEye == vr::Eye_Left)
    {
        *pfLeft = -k_fTangentOuterH;
        *pfRight = k_fTangentInnerH;
    }
    else
    {
        *pfLeft = -k_fTangentInnerH;
        *pfRight = k_fTangentOuterH;
    }
}

vr::HmdMatrix34_t CSampleDeviceDriver::GetEyeToHeadTransform(vr::EVREye eEye)
{
    //test later
    vr::HmdMatrix34_t matrix = {
        1.0f, 0.0f, 0.0f, 0.0f,//x right-left
        0.0f, 1.0f, 0.0f, 0.0f,//y up-down
        0.0f, 0.0f, 1.0f, 0.0f//z forward-back
    };

    float fHalfIPD = m_flIPD / 2.0f;

    if (eEye == vr::Eye_Left)
    {
        matrix.m[0][3] = -fHalfIPD;
    }
    else
    {
        matrix.m[0][3] = fHalfIPD;
    }

    return matrix;
}

vr::DistortionCoordinates_t CSampleDeviceDriver::ComputeDistortion(EVREye eEye, float fU, float fV)
{
    vr::DistortionCoordinates_t coordinates;
    coordinates.rfRed[0] = fU;
    coordinates.rfRed[1] = fV;
    coordinates.rfGreen[0] = fU;
    coordinates.rfGreen[1] = fV;
    coordinates.rfBlue[0] = fU;
    coordinates.rfBlue[1] = fV;
    return coordinates;
}

bool CSampleDeviceDriver::ComputeInverseDistortion(vr::HmdVector2_t* pA, vr::EVREye eEye, uint32_t unElement, float fU, float fV)
{
    pA[unElement].v[0] = fU;
    pA[unElement].v[1] = fV;
    return true;
}

//virtual display
bool CSampleDeviceDriver::InitializeD3D11()
{
    D3D_FEATURE_LEVEL featureLevel;
    HRESULT hr = D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_HARDWARE,
        nullptr,
        D3D11_CREATE_DEVICE_BGRA_SUPPORT,
        nullptr, 0,
        D3D11_SDK_VERSION,
        &m_pD3D11Device, &featureLevel, &m_pD3D11Context);
    return SUCCEEDED(hr);
}

void CSampleDeviceDriver::Present(const vr::PresentInfo_t* pPresentInfo, uint32_t unPresentInfoSize)
{
    if (pPresentInfo && unPresentInfoSize >= sizeof(vr::PresentInfo_t) && m_pD3D11Device)
    {
        HANDLE hTexture = (HANDLE)(uintptr_t)pPresentInfo->backbufferTextureHandle;
        if (hTexture)
        {
            std::lock_guard<std::mutex> lock(m_textureMutex);

            if (hTexture != m_hLastTextureHandle)
            {
                if (m_pSharedTexture) { m_pSharedTexture->Release(); m_pSharedTexture = nullptr; }
                if (m_pLocalTexture) { m_pLocalTexture->Release();  m_pLocalTexture = nullptr; }

                ID3D11Texture2D* pTexture = nullptr;
                HRESULT hr = m_pD3D11Device->OpenSharedResource(hTexture, __uuidof(ID3D11Texture2D), (void**)&pTexture);

                if (SUCCEEDED(hr) && pTexture)
                {
                    m_pSharedTexture = pTexture;
                    m_hLastTextureHandle = hTexture;

                    D3D11_TEXTURE2D_DESC desc;
                    pTexture->GetDesc(&desc);
                    desc.BindFlags |= D3D11_BIND_SHADER_RESOURCE;
                    m_pD3D11Device->CreateTexture2D(&desc, nullptr, &m_pLocalTexture);
                }
                else
                {
                    m_hLastTextureHandle = nullptr;
                    OutputDebugStringA("GlassVR: OpenSharedResource failed\n");
                }
            }

            if (m_pSharedTexture && m_pLocalTexture)
            {
                ComPtr<ID3D11DeviceContext> pContext;
                m_pD3D11Device->GetImmediateContext(&pContext);
                pContext->CopyResource(m_pLocalTexture, m_pSharedTexture);
            }

            m_nCurrentFrameId = pPresentInfo->nFrameId;
            m_dLastCaptureTime = GetSystemTimeInSeconds();

            {
                std::lock_guard<std::mutex> streamLock(m_streamMutex);
                m_bFramePending = true;
            }
            m_streamCv.notify_one();
        }
    }
}

bool CSampleDeviceDriver::GetTimeSinceLastVsync(float* pfSecondsSinceLastVsync, uint64_t* pulFrameCounter)
{
    double now = GetSystemTimeInSeconds();

    double dLastVsyncTime = m_dNextVsyncTime - m_fVsyncPeriod;
    double timeSinceVsync = now - dLastVsyncTime;

    *pfSecondsSinceLastVsync = (float)timeSinceVsync;
    *pulFrameCounter = m_nVsyncCounter;

    return true;
}

void CSampleDeviceDriver::WaitForPresent()
{
    m_nVsyncCounter++;

    double now = GetSystemTimeInSeconds();

    if (now > m_dNextVsyncTime + m_fVsyncPeriod)
    {
        m_dNextVsyncTime = now;
    }

    while (now < m_dNextVsyncTime)
    {
        double remainingSec = m_dNextVsyncTime - now;

        if (remainingSec > 0.002)
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        else
        {
            std::this_thread::yield();
        }

        now = GetSystemTimeInSeconds();
    }
    m_dNextVsyncTime += m_fVsyncPeriod;
}

bool CSampleDeviceDriver::InitializeStreaming()
{
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
    m_udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    m_clientAddr.sin_family = AF_INET;
    m_clientAddr.sin_port = htons(GetIntFromSettingsByKey("virtual port"));

    std::string ip_str = GetStringFromSettingsByKey("client ip");
    const char* ip = ip_str.c_str();

    inet_pton(AF_INET, ip, &m_clientAddr.sin_addr);

    m_tsSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    m_tsClientAddr.sin_family = AF_INET;
    m_tsClientAddr.sin_port = htons(GetIntFromSettingsByKey("virtual port") + 1);
    inet_pton(AF_INET, ip, &m_tsClientAddr.sin_addr);

    MFStartup(MF_VERSION);

    HRESULT hr = CoCreateInstance(CLSID_CMSH264EncoderMFT, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&m_pVideoEncoder));
    if (FAILED(hr)) { OutputDebugStringA("GlassVR: Failed to create H264 MFT\n"); return false; }

    hr = CoCreateInstance(CLSID_VideoProcessorMFT, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&m_pColorConverter));
    if (FAILED(hr)) { OutputDebugStringA("GlassVR: Failed to create Video Processor MFT\n"); return false; }

    m_pVideoEncoder.As(&m_pCodecAPI);
    if (m_pCodecAPI)
    {
        VARIANT var;
        VariantInit(&var);
        var.vt = VT_UI4;

        var.ulVal = eAVEncCommonRateControlMode_CBR;
        hr = m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonRateControlMode, &var);
        OutputDebugStringA(SUCCEEDED(hr) ? "GlassVR: RateControlMode set OK\n" : "GlassVR: RateControlMode SetValue FAILED\n");

        DWORD initBps = (DWORD)GetIntFromSettingsByKey("bitrate") * 1000000;
        if (initBps == 0) initBps = 20000000;
        m_nLastAppliedBitrateMbps = (int)(initBps / 1000000);

        var.ulVal = initBps;
        hr = m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonMeanBitRate, &var);
        OutputDebugStringA(SUCCEEDED(hr) ? "GlassVR: MeanBitRate set OK\n" : "GlassVR: MeanBitRate SetValue FAILED\n");

        var.ulVal = initBps * 2;
        hr = m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonMaxBitRate, &var);
        OutputDebugStringA(SUCCEEDED(hr) ? "GlassVR: MaxBitRate set OK\n" : "GlassVR: MaxBitRate SetValue FAILED\n");

        hr = m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonBufferSize, &var);
        OutputDebugStringA(SUCCEEDED(hr) ? "GlassVR: BufferSize set OK\n" : "GlassVR: BufferSize SetValue FAILED\n");

        var.vt = VT_BOOL;
        var.boolVal = VARIANT_TRUE;
        hr = m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonLowLatency, &var);
        OutputDebugStringA(SUCCEEDED(hr) ? "GlassVR: LowLatency set OK\n" : "GlassVR: LowLatency SetValue FAILED\n");

        VariantClear(&var);
    }
    else {
        OutputDebugStringA("GlassVR: ICodecAPI not available on this encoder - rate control settings not applied!\n");
    }

    ComPtr<IMFDXGIDeviceManager> pDXGIDeviceManager;
    UINT resetToken = 0;
    hr = MFCreateDXGIDeviceManager(&resetToken, &pDXGIDeviceManager);
    if (FAILED(hr) || !m_pD3D11Device) {
        OutputDebugStringA("GlassVR: Failed to create DXGI device manager\n");
        return false;
    }
    pDXGIDeviceManager->ResetDevice(m_pD3D11Device, resetToken);
    m_pColorConverter->ProcessMessage(MFT_MESSAGE_SET_D3D_MANAGER, (ULONG_PTR)pDXGIDeviceManager.Get());
    m_pVideoEncoder->ProcessMessage(MFT_MESSAGE_SET_D3D_MANAGER, (ULONG_PTR)pDXGIDeviceManager.Get());

    int resX = GetIntFromSettingsByKey("resolution x");
    int resY = GetIntFromSettingsByKey("resolution y");

    ComPtr<IMFMediaType> pOutputType;
    MFCreateMediaType(&pOutputType);
    pOutputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    pOutputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_H264);
    pOutputType->SetUINT32(MF_MT_AVG_BITRATE, (DWORD)GetIntFromSettingsByKey("bitrate") * 1000000);
    pOutputType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
    MFSetAttributeSize(pOutputType.Get(), MF_MT_FRAME_SIZE, resX, resY);
    MFSetAttributeRatio(pOutputType.Get(), MF_MT_FRAME_RATE, RefreshRate, 1);
    MFSetAttributeRatio(pOutputType.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
    hr = m_pVideoEncoder->SetOutputType(m_outStreamID, pOutputType.Get(), 0);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Encoder SetOutputType failed!\n");
        return false;
    }

    ComPtr<IMFMediaType> pEncInputType;
    MFCreateMediaType(&pEncInputType);
    pEncInputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    pEncInputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_NV12);
    MFSetAttributeSize(pEncInputType.Get(), MF_MT_FRAME_SIZE, resX, resY);
    MFSetAttributeRatio(pEncInputType.Get(), MF_MT_FRAME_RATE, RefreshRate, 1);
    MFSetAttributeRatio(pEncInputType.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
    pEncInputType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);

    hr = m_pVideoEncoder->SetInputType(m_inStreamID, pEncInputType.Get(), 0);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Encoder SetInputType failed!\n");
        return false;
    }

    ComPtr<IMFMediaType> pCheckType;
    hr = m_pVideoEncoder->GetInputCurrentType(m_inStreamID, &pCheckType);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Encoder rejected the input type configuration!\n");
        return false;
    }

    MFT_OUTPUT_STREAM_INFO encOutInfo = {};
    hr = m_pVideoEncoder->GetOutputStreamInfo(m_outStreamID, &encOutInfo);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Encoder GetOutputStreamInfo failed!\n");
        return false;
    }
    m_bEncoderProvidesSamples =
        (encOutInfo.dwFlags & (MFT_OUTPUT_STREAM_PROVIDES_SAMPLES | MFT_OUTPUT_STREAM_CAN_PROVIDE_SAMPLES)) != 0;
    m_dwEncoderOutputSize = std::max<DWORD>(encOutInfo.cbSize, 2 * 1024 * 1024);

    ComPtr<IMFMediaType> pConvInType;
    MFCreateMediaType(&pConvInType);
    pConvInType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    pConvInType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_ARGB32);
    MFSetAttributeSize(pConvInType.Get(), MF_MT_FRAME_SIZE, resX, resY);
    MFSetAttributeRatio(pConvInType.Get(), MF_MT_FRAME_RATE, RefreshRate, 1);
    MFSetAttributeRatio(pConvInType.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
    pConvInType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
    hr = m_pColorConverter->SetInputType(m_convInStreamID, pConvInType.Get(), 0);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Converter SetInputType failed!\n");
        return false;
    }

    ComPtr<IMFMediaType> pConvOutType;
    MFCreateMediaType(&pConvOutType);
    pConvOutType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    pConvOutType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_NV12);
    MFSetAttributeSize(pConvOutType.Get(), MF_MT_FRAME_SIZE, resX, resY);
    MFSetAttributeRatio(pConvOutType.Get(), MF_MT_FRAME_RATE, RefreshRate, 1);
    MFSetAttributeRatio(pConvOutType.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
    pConvOutType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
    hr = m_pColorConverter->SetOutputType(m_convOutStreamID, pConvOutType.Get(), 0);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Converter SetOutputType failed!\n");
        return false;
    }

    MFT_OUTPUT_STREAM_INFO convOutInfo = {};
    hr = m_pColorConverter->GetOutputStreamInfo(m_convOutStreamID, &convOutInfo);
    if (FAILED(hr)) {
        OutputDebugStringA("GlassVR: Converter GetOutputStreamInfo failed!\n");
        return false;
    }
    m_bConverterProvidesSamples =
        (convOutInfo.dwFlags & (MFT_OUTPUT_STREAM_PROVIDES_SAMPLES | MFT_OUTPUT_STREAM_CAN_PROVIDE_SAMPLES)) != 0;

    if (!m_bConverterProvidesSamples) {
        D3D11_TEXTURE2D_DESC nv12Desc = {};
        nv12Desc.Width = resX;
        nv12Desc.Height = resY;
        nv12Desc.MipLevels = 1;
        nv12Desc.ArraySize = 1;
        nv12Desc.Format = DXGI_FORMAT_NV12;
        nv12Desc.SampleDesc.Count = 1;
        nv12Desc.Usage = D3D11_USAGE_DEFAULT;
        nv12Desc.BindFlags = D3D11_BIND_RENDER_TARGET;
        hr = m_pD3D11Device->CreateTexture2D(&nv12Desc, nullptr, &m_pNV12Texture);
        if (FAILED(hr)) {
            OutputDebugStringA("GlassVR: Failed to create NV12 output texture\n");
            return false;
        }
    }

    m_pColorConverter->ProcessMessage(MFT_MESSAGE_COMMAND_FLUSH, 0);
    m_pColorConverter->ProcessMessage(MFT_MESSAGE_NOTIFY_BEGIN_STREAMING, 1);
    m_pColorConverter->ProcessMessage(MFT_MESSAGE_NOTIFY_START_OF_STREAM, 0);

    m_pVideoEncoder->ProcessMessage(MFT_MESSAGE_COMMAND_FLUSH, 0);
    m_pVideoEncoder->ProcessMessage(MFT_MESSAGE_NOTIFY_BEGIN_STREAMING, 1);
    m_pVideoEncoder->ProcessMessage(MFT_MESSAGE_NOTIFY_START_OF_STREAM, 0);

    OutputDebugStringA("GlassVR: yes");
    m_bStreamingReady = true;
    return true;
}

void CSampleDeviceDriver::StreamWorkerThread()
{
    OutputDebugStringA("GlassVR: StreamWorkerThread started.\n");

    while (m_bRunning)
    {
        std::unique_lock<std::mutex> lock(m_streamMutex);
        m_streamCv.wait(lock, [this] { return m_bFramePending.load() || !m_bRunning.load(); });
        if (!m_bRunning) {
            OutputDebugStringA("GlassVR: StreamWorkerThread shutting down.\n");
            break;
        }
        m_bFramePending = false;
        lock.unlock();

        if (!m_bStreamingReady || !m_pD3D11Device || !m_pD3D11Context || !m_pVideoEncoder || !m_pColorConverter) {
            continue;
        }

        if (m_pCodecAPI) {
            int newBitrateMbps = GetIntFromSettingsByKey("bitrate");
            if (newBitrateMbps > 0 && newBitrateMbps != m_nLastAppliedBitrateMbps.load()) {
                DWORD newBps = (DWORD)newBitrateMbps * 1000000;
                VARIANT var;
                VariantInit(&var);
                var.vt = VT_UI4;
                var.ulVal = newBps;
                m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonMeanBitRate, &var);
                var.ulVal = newBps * 2;
                m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonMaxBitRate, &var);
                var.ulVal = (newBps / 8) * 400 / 1000;
                m_pCodecAPI->SetValue(&CODECAPI_AVEncCommonBufferSize, &var);
                VariantClear(&var);
                m_nLastAppliedBitrateMbps = newBitrateMbps;
                char msg[128];
                sprintf_s(msg, "GlassVR: Bitrate -> %d Mbps\n", newBitrateMbps);
                OutputDebugStringA(msg);
            }
        }

        ComPtr<ID3D11Texture2D> pSourceTexture;
        double capturedTime = 0.0;
        {
            std::lock_guard<std::mutex> texLock(m_textureMutex);
            pSourceTexture = m_pSharedTexture;
            capturedTime = m_dLastCaptureTime.load();
        }

        if (!pSourceTexture) {
            continue;
        }

        ComPtr<IMFMediaBuffer> pBuffer;
        HRESULT hr = MFCreateDXGISurfaceBuffer(__uuidof(ID3D11Texture2D), pSourceTexture.Get(), 0, FALSE, &pBuffer);
        if (FAILED(hr)) {
            char err[256];
            sprintf_s(err, "GlassVR: MFCreateDXGISurfaceBuffer failed with HRESULT 0x%08X\n", hr);
            OutputDebugStringA(err);
            continue;
        }

        ComPtr<IMFSample> pSample;
        hr = MFCreateSample(&pSample);
        if (FAILED(hr)) {
            char err[256];
            sprintf_s(err, "GlassVR: MFCreateSample failed with HRESULT 0x%08X\n", hr);
            OutputDebugStringA(err);
            continue;
        }

        hr = pSample->AddBuffer(pBuffer.Get());
        if (FAILED(hr)) {
            OutputDebugStringA("GlassVR: pSample->AddBuffer failed\n");
            continue;
        }

        LONGLONG hnsSampleTime = (LONGLONG)(GetSystemTimeInSeconds() * 10000000);
        pSample->SetSampleTime(hnsSampleTime);
        pSample->SetSampleDuration(10000000 / RefreshRate);

        hr = m_pColorConverter->ProcessInput(m_convInStreamID, pSample.Get(), 0);
        if (FAILED(hr)) {
            char err[256];
            sprintf_s(err, "GlassVR: Converter ProcessInput failed with HRESULT 0x%08X\n", hr);
            OutputDebugStringA(err);
            continue;
        }

        bool convNeedsMoreInput = false;
        while (!convNeedsMoreInput)
        {
            ComPtr<IMFSample> pNV12Sample;
            MFT_OUTPUT_DATA_BUFFER convOutputBuffer = {};
            convOutputBuffer.dwStreamID = m_convOutStreamID;

            if (!m_bConverterProvidesSamples) {
                MFCreateSample(&pNV12Sample);
                ComPtr<IMFMediaBuffer> pNV12Buffer;
                hr = MFCreateDXGISurfaceBuffer(__uuidof(ID3D11Texture2D), m_pNV12Texture.Get(), 0, FALSE, &pNV12Buffer);
                if (FAILED(hr)) {
                    char err[256];
                    sprintf_s(err, "GlassVR: MFCreateDXGISurfaceBuffer (NV12) failed with HRESULT 0x%08X\n", hr);
                    OutputDebugStringA(err);
                    break;
                }
                pNV12Sample->AddBuffer(pNV12Buffer.Get());
                pNV12Sample->SetSampleTime(hnsSampleTime);
                pNV12Sample->SetSampleDuration(10000000 / RefreshRate);
                convOutputBuffer.pSample = pNV12Sample.Get();
            }

            DWORD convStatus = 0;
            hr = m_pColorConverter->ProcessOutput(0, 1, &convOutputBuffer, &convStatus);

            if (hr == MF_E_TRANSFORM_NEED_MORE_INPUT) {
                if (convOutputBuffer.pEvents) convOutputBuffer.pEvents->Release();
                convNeedsMoreInput = true;
                break;
            }
            else if (FAILED(hr)) {
                char err[256];
                sprintf_s(err, "GlassVR: Converter ProcessOutput failed with HRESULT 0x%08X\n", hr);
                OutputDebugStringA(err);
                if (convOutputBuffer.pEvents) convOutputBuffer.pEvents->Release();
                break;
            }

            if (m_bConverterProvidesSamples) {
                pNV12Sample.Attach(convOutputBuffer.pSample);
            }
            if (convOutputBuffer.pEvents) convOutputBuffer.pEvents->Release();

            hr = m_pVideoEncoder->ProcessInput(m_inStreamID, pNV12Sample.Get(), 0);
            if (FAILED(hr)) {
                char err[256];
                sprintf_s(err, "GlassVR: ProcessInput failed with HRESULT 0x%08X\n", hr);
                OutputDebugStringA(err);
                continue;
            }

            MFT_OUTPUT_DATA_BUFFER outputDataBuffer = {};
            outputDataBuffer.dwStreamID = m_outStreamID;
            DWORD status = 0;

            ComPtr<IMFSample> pOutputSample;
            if (!m_bEncoderProvidesSamples) {
                MFCreateSample(&pOutputSample);
                ComPtr<IMFMediaBuffer> pOutputMediaBuffer;
                MFCreateMemoryBuffer(m_dwEncoderOutputSize, &pOutputMediaBuffer);
                pOutputSample->AddBuffer(pOutputMediaBuffer.Get());
                outputDataBuffer.pSample = pOutputSample.Get();
            }

            hr = m_pVideoEncoder->ProcessOutput(0, 1, &outputDataBuffer, &status);

            if (hr == MF_E_TRANSFORM_NEED_MORE_INPUT) {
                if (outputDataBuffer.pEvents) outputDataBuffer.pEvents->Release();
                continue;
            }
            else if (FAILED(hr)) {
                char err[256];
                sprintf_s(err, "GlassVR: ProcessOutput failed with HRESULT 0x%08X\n", hr);
                OutputDebugStringA(err);

                if (outputDataBuffer.pEvents) outputDataBuffer.pEvents->Release();
                continue;
            }

            if (m_bEncoderProvidesSamples) {
                pOutputSample.Attach(outputDataBuffer.pSample);
            }

            ComPtr<IMFMediaBuffer> pResultBuffer;
            hr = pOutputSample->GetBufferByIndex(0, &pResultBuffer);
            if (FAILED(hr)) {
                OutputDebugStringA("GlassVR: GetBufferByIndex failed\n");
                if (outputDataBuffer.pEvents) outputDataBuffer.pEvents->Release();
                continue;
            }

            BYTE* pData = nullptr;
            DWORD cbData = 0;
            hr = pResultBuffer->Lock(&pData, nullptr, &cbData);
            if (SUCCEEDED(hr))
            {
                const int MTU_PAYLOAD = 1400;
                int bytesSent = 0;
                bool socketError = false;

                while (bytesSent < cbData)
                {
                    int sendSize = std::min((int)(cbData - bytesSent), MTU_PAYLOAD);
                    int result = sendto(m_udpSocket, (const char*)(pData + bytesSent), sendSize, 0, (sockaddr*)&m_clientAddr, sizeof(m_clientAddr));

                    if (result == SOCKET_ERROR) {
                        char err[256];
                        sprintf_s(err, "GlassVR: sendto failed! WSAGetLastError: %d\n", WSAGetLastError());
                        OutputDebugStringA(err);
                        socketError = true;
                        break;
                    }
                    bytesSent += result;
                }

                pResultBuffer->Unlock();

                if (!socketError) {
                    sendto(m_tsSocket, (const char*)&capturedTime, sizeof(capturedTime),
                        0, (sockaddr*)&m_tsClientAddr, sizeof(m_tsClientAddr));

                    static double s_latencySum = 0.0;
                    static int s_latencyCount = 0;
                    double latencyMs = (GetSystemTimeInSeconds() - capturedTime) * 1000.0;
                    s_latencySum += latencyMs;
                    s_latencyCount++;
                    if (s_latencyCount >= 120) {
                        char msg[128];
                        sprintf_s(msg, "GlassVR: avg capture-to-send latency: %.1f ms\n", s_latencySum / s_latencyCount);
                        OutputDebugStringA(msg);
                        s_latencySum = 0.0;
                        s_latencyCount = 0;
                    }
                }
            }
            else
            {
                OutputDebugStringA("GlassVR: pResultBuffer->Lock failed\n");
            }

            if (outputDataBuffer.pEvents) outputDataBuffer.pEvents->Release();
        }
    }
}
//virtual display

//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
static uint32_t g_foundTrackers[vr::k_unMaxTrackedDeviceCount];
static uint32_t g_trackerCount = 0;
static int g_selectedIndex = 0;

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

static int GetTrackerIndexBySerial(const std::string& targetSerial) {
    if (targetSerial.empty()) return -1;

    for (uint32_t i = 0; i < vr::k_unMaxTrackedDeviceCount; i++) {
        vr::PropertyContainerHandle_t container = vr::VRProperties()->TrackedDeviceToPropertyContainer(i);
        if (container == vr::k_ulInvalidPropertyContainer) continue;

        char serialBuf[256];
        vr::ETrackedPropertyError err;
        vr::VRProperties()->GetStringProperty(container, vr::Prop_SerialNumber_String, serialBuf, sizeof(serialBuf), &err);

        if (err == vr::TrackedProp_Success && targetSerial == serialBuf) {
            return (int)i;
        }
    }
    return -1;
}

vr::DriverPose_t CSampleDeviceDriver::GetPose()
{
    UpdateTrackers();

    std::string device = "hmd";

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

    //connections
    udp_pos = m_comm.GetUdpPos();
    udp_rot = m_comm.GetUdpRot();

    pipe_pos = m_comm.GetPipePos();
    pipe_rot = m_comm.GetPipeRot();
    //connections

    //pos here///////////////////////////////////////////////////////
    if (posmode == "copy") {
        std::string targetSerial = GetStringFromSettingsByKey(device + "pos copy serial");
        int tracker_pos_idx = GetTrackerIndexBySerial(targetSerial);

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
    else if (posmode == "offsets") {
        pose.vecPosition[0] = GetFloatFromSettingsByKey(device + " offset world x");
        pose.vecPosition[1] = GetFloatFromSettingsByKey(device + " offset world y");
        pose.vecPosition[2] = GetFloatFromSettingsByKey(device + " offset world z");
    }

    //viture-6dof
    else if (posmode == "xr glasses 6dof") {
        if (m_pVitureDevice && m_pVitureDevice->is_carina()) {
            float quat[4], pos[3];
            bool stable = false;
            if (m_pVitureDevice->get_6dof_pose(quat, pos, &stable) && stable) {
                Transform FinalTransform = GetNewTransform(device,
                    pos[0], pos[1], pos[2],
                    quat[1], quat[2], quat[3], quat[0]);

                pose.vecPosition[0] = FinalTransform.pos_x;
                pose.vecPosition[1] = FinalTransform.pos_y;
                pose.vecPosition[2] = FinalTransform.pos_z;
            }
        }
    }

    else if (posmode == "UDP") {
        Transform FinalTransform = GetNewTransform(device, udp_pos.x, udp_pos.y, udp_pos.z, pose.qRotation.x, pose.qRotation.y, pose.qRotation.z, pose.qRotation.w);

        pose.vecPosition[0] = FinalTransform.pos_x;
        pose.vecPosition[1] = FinalTransform.pos_y;
        pose.vecPosition[2] = FinalTransform.pos_z;
    }
    else if (posmode == "test") {
        //get from remote!
    }
    else {
        pose.vecPosition[0] = pipe_pos.x;
        pose.vecPosition[1] = pipe_pos.y;
        pose.vecPosition[2] = pipe_pos.z;
    }

    //rot here///////////////////////////////////////////////////////
    if (rotmode == "copy") {
        std::string targetRotSerial = GetStringFromSettingsByKey(device + "rot copy serial");
        int tracker_rot_idx = GetTrackerIndexBySerial(targetRotSerial);

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
    else if (rotmode == "offsets") {
        float yaw = GetFloatFromSettingsByKey(device + " offset world yaw");
        float pitch = GetFloatFromSettingsByKey(device + " offset world pitch");
        float roll = GetFloatFromSettingsByKey(device + " offset world roll");

        vr::HmdQuaternion_t offsetQuat = EulerToQuatZYX(roll, yaw, pitch);

        pose.qRotation.w = offsetQuat.w;
        pose.qRotation.x = offsetQuat.x;
        pose.qRotation.y = offsetQuat.y;
        pose.qRotation.z = offsetQuat.z;
    }

    //viture-6dof
    else if (rotmode == "xr glasses 6dof") {
        //todo: add hardcoded offset for local pitch by 1.40!
        if (m_pVitureDevice && m_pVitureDevice->is_carina()) {
            float quat[4], pos[3];
            bool stable = false;
            if (m_pVitureDevice->get_6dof_pose(quat, pos, &stable)) {
                pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
                pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

                //hardcoded offsets
                Transform HardOffsetTransform = OffsetTransform(pose.vecPosition[0], pose.vecPosition[1], pose.vecPosition[2],
                    quat[1], quat[2], quat[3], quat[0],
                    0,0,0,0,0.240,0,//GetFloatFromSettingsByKey("0tracker offset world x"), 0,
                    0,0,0,0,0,0);

                //Transform FinalTransform = GetNewTransform(device,
                //    pose.vecPosition[0], pose.vecPosition[1], pose.vecPosition[2],
                //    quat[1], quat[2], quat[3], quat[0]);

                Transform FinalTransform = GetNewTransform(device,
                    HardOffsetTransform.pos_x, HardOffsetTransform.pos_y, HardOffsetTransform.pos_z,
                    HardOffsetTransform.rot_x, HardOffsetTransform.rot_y, HardOffsetTransform.rot_z, HardOffsetTransform.rot_w);

                pose.qRotation.w = FinalTransform.rot_w;
                pose.qRotation.x = FinalTransform.rot_x;
                pose.qRotation.y = FinalTransform.rot_y;
                pose.qRotation.z = FinalTransform.rot_z;

                pose.poseIsValid = stable;
                if (!stable) {
                    pose.result = vr::TrackingResult_Fallback_RotationOnly;
                }
            }
        }
    }
    //viture-6dof

    //viture-
    else if (rotmode == "xr glasses") {
        if (m_pVitureDevice && m_pVitureDevice->is_connected()) {

            float euler[3], quat[4], gyro[3];
            m_pVitureDevice->get_imu_data(euler, quat, gyro);

            pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
            pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);

            vr::HmdQuaternion_t device_rotation;
            if (m_pVitureDevice->is_carina()) {
                device_rotation.w = quat[0];
                device_rotation.x = quat[1];
                device_rotation.y = quat[2];
                device_rotation.z = quat[3];

                pose.vecAngularVelocity[0] = 0;
                pose.vecAngularVelocity[1] = 0;
                pose.vecAngularVelocity[2] = 0;
            }
            else {
                device_rotation.x = quat[1];
                device_rotation.y = -quat[0];
                device_rotation.z = -quat[2];
                device_rotation.w = quat[3];

                pose.vecAngularVelocity[0] = gyro[1];
                pose.vecAngularVelocity[1] = -gyro[0];
                pose.vecAngularVelocity[2] = -gyro[2];
            }

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
        }
    }
    //viture-

    else if (rotmode == "UDP") {
        Transform FinalTransform = GetNewTransform(device, pose.vecPosition[0], pose.vecPosition[1], pose.vecPosition[2], udp_rot.x, udp_rot.y, udp_rot.z, udp_rot.w);

        pose.qRotation.w = FinalTransform.rot_w;
        pose.qRotation.x = FinalTransform.rot_x;
        pose.qRotation.y = FinalTransform.rot_y;
        pose.qRotation.z = FinalTransform.rot_z;
    }
    else if (rotmode == "test") {
        //get from remote!
    }
    else {
        pose.qRotation.w = pipe_rot.w;
        pose.qRotation.x = pipe_rot.x;
        pose.qRotation.y = pipe_rot.y;
        pose.qRotation.z = pipe_rot.z;
    }

    pose.poseTimeOffset = GetFloatFromSettingsByKey("prediction time");

    return pose;
}

//pose here/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void CSampleDeviceDriver::RunFrame()
{
    if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
        vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));

        m_flIPD = GetFloatFromSettingsByKey("ipd");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserIpdMeters_Float,
            m_flIPD
        );
        HeadToEyeDist = GetFloatFromSettingsByKey("head to eye dist");
        vr::VRProperties()->SetFloatProperty(
            m_ulPropertyContainer,
            vr::Prop_UserHeadToEyeDepthMeters_Float,
            HeadToEyeDist
        );

        //viture reset--
        static bool reset_was_down = false;

        PacketExtra extra = m_comm.GetPipeExtra();
        bool reset_is_down = extra.reset;

        if (reset_is_down && !reset_was_down) {
            if (m_pVitureDevice) {
                if (m_pVitureDevice->is_carina()) {
                    m_pVitureDevice->reset_origin_carina();
                }
                else {
                    m_pVitureDevice->recenter_3dof();
                }
            }
        }
        reset_was_down = reset_is_down;
        //viture reset--

    }
}