//#pragma once
//
//#include "openvr_driver.h"
//#include "packet.h"
//
//class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
//{
//public:
//    CSampleControllerDriver();
//    virtual ~CSampleControllerDriver();
//
//    void UpdateData(const Packet& data);
//
//    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId);
//    virtual void Deactivate();
//    virtual void EnterStandby();
//    void* GetComponent(const char* pchComponentNameAndVersion);
//    virtual void PowerOff();
//    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize);
//    virtual vr::DriverPose_t GetPose();
//
//    void RunFrame();
//    void ProcessEvent(const vr::VREvent_t& vrEvent);
//
//    std::string GetSerialNumber() const;
//    void SetControllerIndex(int32_t CtrlIndex);
//
//private:
//    Packet m_poseDataCache;
//
//    vr::TrackedDeviceIndex_t m_unObjectId;
//    vr::PropertyContainerHandle_t m_ulPropertyContainer;
//
//    vr::VRInputComponentHandle_t m_compHaptic;
//    // In csamplecontrollerdriver.h
//// Increased sizes to hold new inputs
//    vr::VRInputComponentHandle_t HButtons[12];
//    vr::VRInputComponentHandle_t HAnalog[12];
//
//    //vr::VRInputComponentHandle_t HButtons[3];  // A, B, System
//    //vr::VRInputComponentHandle_t HAnalog[3];   // Joystick X, Y, Trigger
//
//    // Skeletal input handles (one per controller)
//    vr::VRInputComponentHandle_t m_skeletonHandle;
//
//    int32_t ControllerIndex;
//
//    // Hand animation state
//    float m_handAnimationValue;
//
//    // Helper function to get skeletal data
//    vr::VRBoneTransform_t* GetBoneTransform();
//};






















//#pragma once
//
//#include <openvr_driver.h>
//#include "packet.h" // Assuming "packet.h" defines the 'Packet' struct
//#include <string>
//#include <cmath>
//#include <cstring> // Added for memset
//
//// Global Input Variables
//namespace ControllerInput {
//    // Joystick
//    extern float joystick_x;
//    extern float joystick_y;
//    extern bool joystick_click;
//    extern bool joystick_touch;
//
//    // Trigger
//    extern float trigger_value;
//    extern bool trigger_click;
//    extern bool trigger_touch;
//
//    // Grip
//    extern float grip_force;
//    extern float grip_value;
//    extern bool grip_touch;
//
//    // Trackpad
//    extern float trackpad_x;
//    extern float trackpad_y;
//    extern bool trackpad_touch;
//    extern float trackpad_force;
//
//    // Buttons
//    extern bool button_A;
//    extern bool button_B;
//    extern bool button_system;
//
//    // Finger tracking (0.0 = extended, 1.0 = curled)
//    extern float finger_thumb;
//    extern float finger_index;
//    extern float finger_middle;
//    extern float finger_ring;
//    extern float finger_pinky;
//}
//
//class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
//{
//public:
//    CSampleControllerDriver();
//    virtual ~CSampleControllerDriver();
//
//    // ITrackedDeviceServerDriver interface
//    virtual vr::EVRInitError Activate(uint32_t unObjectId) override;
//    virtual void Deactivate() override;
//    virtual void EnterStandby() override;
//    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
//    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
//    virtual vr::DriverPose_t GetPose() override;
//
//    // Custom methods
//    void SetControllerIndex(int index);
//    void UpdateData(const Packet& data);
//    void RunFrame();
//    std::string GetSerialNumber() const;
//
//private:
//    void UpdateSkeletalInput();
//    void UpdateButtonInputs();
//    void UpdateAnalogInputs();
//    vr::VRBoneTransform_t GetBoneTransform(int bone, float curl);
//
//    vr::TrackedDeviceIndex_t m_unObjectId;
//    vr::PropertyContainerHandle_t m_ulPropertyContainer;
//
//    std::string m_sSerialNumber;
//    std::string m_sModelNumber;
//
//    int m_nControllerIndex; // 1 = left, 2 = right
//    bool m_bIsRightHand;
//
//    Packet m_poseDataCache;
//
//    // Component handles
//    vr::VRInputComponentHandle_t m_compJoystick;
//    vr::VRInputComponentHandle_t m_compTrigger;
//    vr::VRInputComponentHandle_t m_compTriggerClick;
//    vr::VRInputComponentHandle_t m_compTriggerTouch;
//    vr::VRInputComponentHandle_t m_compGrip;
//    vr::VRInputComponentHandle_t m_compGripForce;
//    vr::VRInputComponentHandle_t m_compGripTouch;
//    vr::VRInputComponentHandle_t m_compTrackpad;
//    vr::VRInputComponentHandle_t m_compTrackpadTouch;
//    vr::VRInputComponentHandle_t m_compTrackpadForce;
//    vr::VRInputComponentHandle_t m_compButtonA;
//    vr::VRInputComponentHandle_t m_compButtonB;
//    vr::VRInputComponentHandle_t m_compButtonSystem;
//    vr::VRInputComponentHandle_t m_compJoystickClick;
//    vr::VRInputComponentHandle_t m_compJoystickTouch;
//    vr::VRInputComponentHandle_t m_compSkeleton;
//    vr::VRInputComponentHandle_t m_compHaptic;
//};




























//#ifndef CSAMPLECONTROLLERDRIVER_H
//#define CSAMPLECONTROLLERDRIVER_H
//
//#include "openvr_driver.h"
//#include "packet.h" 
//
//class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
//{
//public:
//    CSampleControllerDriver();
//    virtual ~CSampleControllerDriver();
//
//    // ITrackedDeviceServerDriver interface implementation
//    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
//    virtual void Deactivate() override;
//    virtual void EnterStandby() override;
//    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
//    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
//    virtual vr::DriverPose_t GetPose() override;
//
//    // Custom methods
//    void RunFrame();
//    void ProcessEvent(const vr::VREvent_t& vrEvent);
//    std::string GetSerialNumber() const;
//    void SetControllerIndex(int32_t CtrlIndex);
//    void PowerOff();
//
//    // Update controller data from UDP packet
//    void UpdateData(const Packet& data);
//
//private:
//    vr::TrackedDeviceIndex_t m_unObjectId;
//    vr::PropertyContainerHandle_t m_ulPropertyContainer;
//
//    //// Input component handles
//    //vr::VRInputComponentHandle_t HButtons[12];  // Increased from 11 to 12 for trackpad click
//    //vr::VRInputComponentHandle_t HAnalog[8];
//
//    // Haptic component handle
//    vr::VRInputComponentHandle_t m_compHaptic;
//
//    // Controller identifier (1 = Left, 2 = Right)
//    int32_t ControllerIndex;
//
//    // Cached UDP packet data
//    Packet m_poseDataCache;
//
//    // REMOVED: Skeleton-related members
//    // vr::VRInputComponentHandle_t m_skeletonHandle;
//    // float m_handAnimationValue;
//    // vr::VRBoneTransform_t* GetBoneTransform();
//};
//
//#endif // CSAMPLECONTROLLERDRIVER_H


































//#ifndef CSAMPLECONTROLLERDRIVER_H
//#define CSAMPLECONTROLLERDRIVER_H
//
//#include "openvr_driver.h"
//#include "packet.h"
//
//class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
//{
//public:
//    CSampleControllerDriver();
//    virtual ~CSampleControllerDriver();
//
//    // ITrackedDeviceServerDriver interface implementation
//    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
//    virtual void Deactivate() override;
//    virtual void EnterStandby() override;
//    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
//    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
//    virtual vr::DriverPose_t GetPose() override;
//
//    // Custom methods
//    void RunFrame();
//    void ProcessEvent(const vr::VREvent_t& vrEvent);
//    std::string GetSerialNumber() const;
//    void SetControllerIndex(bool CtrlIndex);
//    void PowerOff();
//
//    // Update controller data from UDP packet
//    void UpdateData(const Packet& data);
//
//private:
//    // New: Declaration for Skeletal input helper function
//    void UpdateSkeletalInput(bool isGripClosed);
//
//    vr::TrackedDeviceIndex_t m_unObjectId;
//    vr::PropertyContainerHandle_t m_ulPropertyContainer;
//
//    // Haptic component handle
//    vr::VRInputComponentHandle_t m_compHaptic;
//
//    // Controller identifier (1 = Left, 2 = Right)
//    bool right;
//
//    // Cached UDP packet data
//    Packet m_poseDataCache;
//};
//
//#endif // CSAMPLECONTROLLERDRIVER_H





















































#ifndef CSAMPLECONTROLLERDRIVER_H
#define CSAMPLECONTROLLERDRIVER_H

#include "openvr_driver.h"
#include "packet.h"

class CSampleControllerDriver : public vr::ITrackedDeviceServerDriver
{
public:
    CSampleControllerDriver();
    virtual ~CSampleControllerDriver();

    // ITrackedDeviceServerDriver interface implementation
    virtual vr::EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override;
    virtual void Deactivate() override;
    virtual void EnterStandby() override;
    virtual void* GetComponent(const char* pchComponentNameAndVersion) override;
    virtual void DebugRequest(const char* pchRequest, char* pchResponseBuffer, uint32_t unResponseBufferSize) override;
    virtual vr::DriverPose_t GetPose() override;

    // Custom methods
    void RunFrame();
    void ProcessEvent(const vr::VREvent_t& vrEvent);
    std::string GetSerialNumber() const;
    void SetControllerIndex(int32_t CtrlIndex);  // Changed back to int32_t
    void PowerOff();

    // Update controller data from UDP packet
    void UpdateData(const Packet& data);

private:
    // Skeletal input helper function
    void UpdateSkeletalInput(bool isGripClosed);

    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    // Input component handles - PER CONTROLLER INSTANCE (CRITICAL FIX)
    vr::VRInputComponentHandle_t m_HButtons[13];
    vr::VRInputComponentHandle_t m_HAnalog[10];
    vr::VRInputComponentHandle_t m_HSkeletal;

    // Haptic component handle
    vr::VRInputComponentHandle_t m_compHaptic;

    // Controller identifier (0 = Left, 1 = Right)
    int32_t right;  // Changed from bool to int32_t for consistency

    // Cached UDP packet data
    Packet m_poseDataCache;
};

#endif // CSAMPLECONTROLLERDRIVER_H