///very sloppy needs checking, leaving slop comments for now

// Driver side hooks: change how OTHER drivers' devices look to SteamVR (block, hide, re-source pose,
// offset, model visibility, controller role, per finger skeleton overrides).
// Hooks are placed on the vtables of the interfaces vrserver hands to every driver, see Install().
#include "driverhooks.h"
#include "hooking.h"
#include "packets.h"
#include "skeletaloverride.h"
#include "inputoverride.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <cstring>

namespace glassvr {
    namespace hooks {

        // =========================================================================================
        // vtable plumbing shared by every hooked interface
        // =========================================================================================

        // vtable slots of the hooked methods (openvr_driver.h declaration order)
        enum : size_t {
            kHost_TrackedDeviceAdded = 0,      // IVRServerDriverHost
            kHost_TrackedDevicePoseUpdated = 1,
            kProps_WritePropertyBatch = 1,     // IVRProperties
            kInput_CreateBooleanComponent = 0,  // IVRDriverInput
            kInput_UpdateBooleanComponent = 1,
            kInput_CreateScalarComponent = 2,
            kInput_UpdateScalarComponent = 3,
            kInput_CreateSkeletonComponent = 5,
            kInput_UpdateSkeletonComponent = 6,
        };

        // per vtable data. Several driver contexts share one vtable, so keying by vtable hooks it once.
        template <class T>
        class VTableRegistry
        {
        public:
            bool Contains(void** vt) const
            {
                std::lock_guard<std::mutex> lock(m_mutex);
                return m_map.find(vt) != m_map.end();
            }

            void Set(void** vt, const T& value)
            {
                std::lock_guard<std::mutex> lock(m_mutex);
                m_map[vt] = value;
            }

            T Get(void** vt) const
            {
                std::lock_guard<std::mutex> lock(m_mutex);
                auto it = m_map.find(vt);
                return (it == m_map.end()) ? T{} : it->second;
            }

            template <class Fn>
            void ForEachAndClear(Fn&& fn)
            {
                std::lock_guard<std::mutex> lock(m_mutex);
                for (auto& kv : m_map) fn(kv.first);
                m_map.clear();
            }

        private:
            mutable std::mutex              m_mutex;
            std::unordered_map<void**, T>   m_map;
        };

        static bool HookSlot(void** vt, size_t slot, void* detour, void** original,
            const char* version, const char* method)
        {
            if (MH_CreateHook(vt[slot], detour, original) != MH_OK || MH_EnableHook(vt[slot]) != MH_OK) {
                HookLog("[hooks] failed to hook %s::%s", version, method);
                return false;
            }
            return true;
        }

        static void UnhookSlot(void** vt, size_t slot)
        {
            MH_DisableHook(vt[slot]);
            MH_RemoveHook(vt[slot]);
        }

        struct SlotHook
        {
            size_t      slot;
            void* detour;
            void** original;
            const char* method;
        };

        // all or nothing: a half hooked interface would leave handles half known
        static bool HookAll(void** vt, const char* version, const SlotHook* hooks, size_t count)
        {
            for (size_t i = 0; i < count; i++) {
                if (!HookSlot(vt, hooks[i].slot, hooks[i].detour, hooks[i].original, version, hooks[i].method)) {
                    while (i-- > 0) UnhookSlot(vt, hooks[i].slot);
                    return false;
                }
            }
            return true;
        }

        // hooks `iface` once per vtable. install(vt, originals) places the hooks and returns whether to keep them.
        template <class Originals, class InstallFn>
        static void HookInterfaceOnce(void* iface, const char* version,
            VTableRegistry<Originals>& registry, InstallFn install)
        {
            if (!iface) return;

            void** vt = GetVTable(iface);
            if (registry.Contains(vt)) return;

            Originals originals{};
            if (!install(vt, originals)) return;

            registry.Set(vt, originals);
            HookLog("[hooks] hooked %s (vtable %p)", version, (void*)vt);
        }

        static bool HasPrefix(const char* text, const char* prefix)
        {
            return std::strncmp(text, prefix, std::strlen(prefix)) == 0;
        }

        // =========================================================================================
        // rule + device state (all guarded by g_stateMutex)
        // =========================================================================================

        static std::mutex                                        g_stateMutex;
        static std::unordered_set<std::string>                   g_blockedSerials;
        static std::unordered_set<std::string>                   g_hiddenSerials;
        static std::unordered_map<std::string, PacketPos>        g_offsets;

        static std::unordered_map<std::string, std::string>      g_poseSourceByTarget;
        static std::unordered_set<std::string>                   g_poseSourceSerials;
        static std::unordered_map<std::string, vr::DriverPose_t> g_latestPoseBySource;

        static std::unordered_map<std::string, bool>             g_modelVisible;
        static std::unordered_map<std::string, std::string>      g_originalRenderModel;

        static std::unordered_map<std::string, vr::ETrackedControllerRole> g_roleOverride;
        static std::unordered_map<std::string, vr::ETrackedControllerRole> g_originalRole;

        static std::unordered_map<uint32_t, std::string>         g_indexToSerial;
        static std::unordered_map<std::string, uint32_t>         g_serialToIndex;

        static std::unordered_map<vr::PropertyContainerHandle_t, std::string> g_containerToSerial;
        static std::unordered_map<std::string, vr::PropertyContainerHandle_t> g_serialToContainer;

        static bool g_installed = false;

        static void RebuildPoseSourceSet_Locked()
        {
            g_poseSourceSerials.clear();
            for (const auto& kv : g_poseSourceByTarget)
                if (!kv.second.empty()) g_poseSourceSerials.insert(kv.second);
        }

        static void SetMember(std::unordered_set<std::string>& set, const std::string& serial, bool member)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            if (member) set.insert(serial);
            else        set.erase(serial);
        }

        // ---- original function pointers, per interface vtable ----

        typedef bool (*TrackedDeviceAdded_t)(vr::IVRServerDriverHost*, const char*,
            vr::ETrackedDeviceClass,
            vr::ITrackedDeviceServerDriver*);
        typedef void (*TrackedDevicePoseUpdated_t)(vr::IVRServerDriverHost*, uint32_t,
            const vr::DriverPose_t&, uint32_t);
        struct HostOriginals
        {
            TrackedDeviceAdded_t       added = nullptr;
            TrackedDevicePoseUpdated_t poseUpdated = nullptr;
        };

        typedef vr::ETrackedPropertyError(*WritePropertyBatch_t)(
            vr::IVRProperties*, vr::PropertyContainerHandle_t,
            vr::PropertyWrite_t*, uint32_t);

        typedef vr::EVRInputError(*CreateSkeletonComponent_t)(
            vr::IVRDriverInput*, vr::PropertyContainerHandle_t, const char*, const char*, const char*,
            vr::EVRSkeletalTrackingLevel, const vr::VRBoneTransform_t*, uint32_t,
            vr::VRInputComponentHandle_t*);
        typedef vr::EVRInputError(*UpdateSkeletonComponent_t)(
            vr::IVRDriverInput*, vr::VRInputComponentHandle_t,
            vr::EVRSkeletalMotionRange, const vr::VRBoneTransform_t*, uint32_t);
        typedef vr::EVRInputError(*CreateBooleanComponent_t)(
            vr::IVRDriverInput*, vr::PropertyContainerHandle_t, const char*, vr::VRInputComponentHandle_t*);
        typedef vr::EVRInputError(*UpdateBooleanComponent_t)(
            vr::IVRDriverInput*, vr::VRInputComponentHandle_t, bool, double);
        typedef vr::EVRInputError(*CreateScalarComponent_t)(
            vr::IVRDriverInput*, vr::PropertyContainerHandle_t, const char*, vr::VRInputComponentHandle_t*,
            vr::EVRScalarType, vr::EVRScalarUnits);
        typedef vr::EVRInputError(*UpdateScalarComponent_t)(
            vr::IVRDriverInput*, vr::VRInputComponentHandle_t, float, double);

        struct InputOriginals
        {
            CreateBooleanComponent_t  createBoolean = nullptr;
            UpdateBooleanComponent_t  updateBoolean = nullptr;
            CreateScalarComponent_t   createScalar = nullptr;
            UpdateScalarComponent_t   updateScalar = nullptr;
            CreateSkeletonComponent_t createSkeleton = nullptr;
            UpdateSkeletonComponent_t updateSkeleton = nullptr;
        };

        static VTableRegistry<HostOriginals>        g_hostHooks;
        static VTableRegistry<WritePropertyBatch_t> g_propsHooks;
        static VTableRegistry<InputOriginals>       g_inputHooks;

        // ---- device <-> serial tables ----

        static std::string ReadContainerSerial(vr::PropertyContainerHandle_t container)
        {
            if (!vr::VRProperties() || container == vr::k_ulInvalidPropertyContainer)
                return std::string();

            vr::ETrackedPropertyError err = vr::TrackedProp_Success;
            std::string serial = vr::VRProperties()->GetStringProperty(
                container, vr::Prop_SerialNumber_String, &err);

            return (err == vr::TrackedProp_Success) ? serial : std::string();
        }

        static std::string ReadSerialProperty(uint32_t unWhichDevice)
        {
            if (!vr::VRProperties()) return std::string();
            return ReadContainerSerial(vr::VRProperties()->TrackedDeviceToPropertyContainer(unWhichDevice));
        }

        static void RememberDevice(uint32_t index, const std::string& serial)
        {
            if (serial.empty()) return;

            vr::PropertyContainerHandle_t container = vr::k_ulInvalidPropertyContainer;
            if (vr::VRProperties())
                container = vr::VRProperties()->TrackedDeviceToPropertyContainer(index);

            std::lock_guard<std::mutex> lock(g_stateMutex);
            g_indexToSerial[index] = serial;
            g_serialToIndex[serial] = index;
            if (container != vr::k_ulInvalidPropertyContainer) {
                g_containerToSerial[container] = serial;
                g_serialToContainer[serial] = container;
            }
        }

        static std::string ResolveSerial(uint32_t unWhichDevice)
        {
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                auto it = g_indexToSerial.find(unWhichDevice);
                if (it != g_indexToSerial.end() && !it->second.empty())
                    return it->second;
            }

            std::string serial = ReadSerialProperty(unWhichDevice);
            if (serial.empty()) return serial;

            RememberDevice(unWhichDevice, serial);
            HookLog("[hooks] device %u resolved to serial '%s'", unWhichDevice, serial.c_str());
            return serial;
        }

        static void RefreshDeviceTable()
        {
            for (uint32_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i) {
                std::string serial = ReadSerialProperty(i);
                if (!serial.empty()) RememberDevice(i, serial);
            }
        }

        uint32_t DeviceIndexForSerial(const std::string& serial)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            auto it = g_serialToIndex.find(serial);
            return (it == g_serialToIndex.end()) ? vr::k_unTrackedDeviceIndexInvalid : it->second;
        }

        static std::string SerialForContainer(vr::PropertyContainerHandle_t container)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            auto it = g_containerToSerial.find(container);
            return (it == g_containerToSerial.end()) ? std::string() : it->second;
        }

        // property container of a device: the cached one, else looked up through its device index
        static vr::PropertyContainerHandle_t FindContainer(const std::string& serial)
        {
            if (!vr::VRProperties()) return vr::k_ulInvalidPropertyContainer;

            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                auto it = g_serialToContainer.find(serial);
                if (it != g_serialToContainer.end()) return it->second;
            }

            uint32_t index = DeviceIndexForSerial(serial);
            if (index == vr::k_unTrackedDeviceIndexInvalid) return vr::k_ulInvalidPropertyContainer;
            return vr::VRProperties()->TrackedDeviceToPropertyContainer(index);
        }

        std::string SerialForDeviceIndex(uint32_t unWhichDevice)
        {
            return ResolveSerial(unWhichDevice);
        }

        // used by the skeletal hook, whose update calls only carry a handle: the cached serial if the device
        // table already knows the container, else read it from the container itself
        std::string ResolveContainerSerial(vr::PropertyContainerHandle_t container)
        {
            std::string serial = SerialForContainer(container);
            return serial.empty() ? ReadContainerSerial(container) : serial;
        }

        // =========================================================================================
        // detours
        // =========================================================================================

        static bool Detour_TrackedDeviceAdded(vr::IVRServerDriverHost* _this,
            const char* pchSerial,
            vr::ETrackedDeviceClass eClass,
            vr::ITrackedDeviceServerDriver* pDriver)
        {
            HostOriginals orig = g_hostHooks.Get(GetVTable(_this));
            if (!orig.added)
                return false;

            if (pchSerial) {
                bool blocked;
                {
                    std::lock_guard<std::mutex> lock(g_stateMutex);
                    blocked = g_blockedSerials.count(pchSerial) > 0;
                }
                if (blocked) {
                    HookLog("[hooks] BLOCKED TrackedDeviceAdded('%s', class %d)",
                        pchSerial, (int)eClass);
                    return false;
                }
                HookLog("[hooks] TrackedDeviceAdded('%s', class %d)", pchSerial, (int)eClass);
            }

            return orig.added(_this, pchSerial, eClass, pDriver);
        }

        static void Detour_TrackedDevicePoseUpdated(vr::IVRServerDriverHost* _this,
            uint32_t unWhichDevice,
            const vr::DriverPose_t& newPose,
            uint32_t unPoseStructSize)
        {
            HostOriginals orig = g_hostHooks.Get(GetVTable(_this));
            if (!orig.poseUpdated)
                return;

            bool anyRules;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                anyRules = !g_hiddenSerials.empty() || !g_offsets.empty() ||
                    !g_poseSourceByTarget.empty();
            }
            if (!anyRules) {
                orig.poseUpdated(_this, unWhichDevice, newPose, unPoseStructSize);
                return;
            }

            std::string serial = ResolveSerial(unWhichDevice);
            if (serial.empty()) {
                orig.poseUpdated(_this, unWhichDevice, newPose, unPoseStructSize);
                return;
            }

            bool hidden = false;
            bool hasOffset = false;
            bool hasSourcePose = false;
            PacketPos offset = { 0, 0, 0 };
            vr::DriverPose_t sourcePose{};

            {
                std::lock_guard<std::mutex> lock(g_stateMutex);

                if (g_poseSourceSerials.count(serial))
                    g_latestPoseBySource[serial] = newPose;

                hidden = g_hiddenSerials.count(serial) > 0;

                auto off = g_offsets.find(serial);
                if (off != g_offsets.end()) { hasOffset = true; offset = off->second; }

                auto src = g_poseSourceByTarget.find(serial);
                if (src != g_poseSourceByTarget.end() && !src->second.empty()) {
                    auto cached = g_latestPoseBySource.find(src->second);
                    if (cached != g_latestPoseBySource.end()) {
                        sourcePose = cached->second;
                        hasSourcePose = true;
                    }
                }
            }

            if (!hidden && !hasOffset && !hasSourcePose) {
                orig.poseUpdated(_this, unWhichDevice, newPose, unPoseStructSize);
                return;
            }

            // Default to the device's own pose
            vr::DriverPose_t pose = newPose;

            // If we have a valid source pose, use it and explicitly mark it as tracking OK
            if (hasSourcePose && sourcePose.poseIsValid) {
                pose = sourcePose;
                pose.poseIsValid = true;
                pose.result = vr::TrackingResult_Running_OK;
            }

            if (hasOffset) {
                pose.vecPosition[0] += offset.x;
                pose.vecPosition[1] += offset.y;
                pose.vecPosition[2] += offset.z;
            }

            if (hidden) {
                pose.deviceIsConnected = false;
                pose.poseIsValid = false;
                pose.result = vr::TrackingResult_Uninitialized;
            }

            orig.poseUpdated(_this, unWhichDevice, pose, unPoseStructSize);
        }

        static vr::ETrackedPropertyError Detour_WritePropertyBatch(
            vr::IVRProperties* _this,
            vr::PropertyContainerHandle_t ulContainerHandle,
            vr::PropertyWrite_t* pBatch,
            uint32_t unCountInBatch)
        {
            WritePropertyBatch_t orig = g_propsHooks.Get(GetVTable(_this));
            if (!orig) return vr::TrackedProp_InvalidOperation;

            bool anyRoles;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                anyRoles = !g_roleOverride.empty();
            }

            if (anyRoles && pBatch) {
                std::string serial = SerialForContainer(ulContainerHandle);
                if (!serial.empty()) {
                    vr::ETrackedControllerRole desiredRole = vr::TrackedControllerRole_Invalid;
                    bool hasRole = false;
                    {
                        std::lock_guard<std::mutex> lock(g_stateMutex);
                        auto it = g_roleOverride.find(serial);
                        if (it != g_roleOverride.end()) { hasRole = true; desiredRole = it->second; }
                    }

                    if (hasRole) {
                        for (uint32_t i = 0; i < unCountInBatch; ++i) {
                            vr::PropertyWrite_t& w = pBatch[i];
                            if (w.prop == vr::Prop_ControllerRoleHint_Int32 &&
                                w.writeType == vr::PropertyWrite_Set &&
                                w.pvBuffer && w.unBufferSize == sizeof(int32_t)) {

                                std::lock_guard<std::mutex> lock(g_stateMutex);
                                if (g_originalRole.find(serial) == g_originalRole.end()) {
                                    g_originalRole[serial] = static_cast<vr::ETrackedControllerRole>(
                                        *reinterpret_cast<int32_t*>(w.pvBuffer));
                                }
                                *reinterpret_cast<int32_t*>(w.pvBuffer) = static_cast<int32_t>(desiredRole);
                            }
                        }
                    }
                }
            }

            return orig(_this, ulContainerHandle, pBatch, unCountInBatch);
        }

        // buttons / axes: Create tells the input override which paths a device really has, Update swaps ticked values
        static vr::EVRInputError Detour_CreateBooleanComponent(
            vr::IVRDriverInput* _this, vr::PropertyContainerHandle_t ulContainer,
            const char* pchName, vr::VRInputComponentHandle_t* pHandle)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.createBoolean) return vr::VRInputError_InvalidHandle;

            vr::EVRInputError err = orig.createBoolean(_this, ulContainer, pchName, pHandle);
            if (err == vr::VRInputError_None && pHandle)
                OnInputComponentCreated(*pHandle, ulContainer, pchName, false);
            return err;
        }

        static vr::EVRInputError Detour_UpdateBooleanComponent(
            vr::IVRDriverInput* _this, vr::VRInputComponentHandle_t ulComponent,
            bool bNewValue, double fTimeOffset)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.updateBoolean) return vr::VRInputError_InvalidHandle;

            OverrideBooleanInput(ulComponent, bNewValue);
            return orig.updateBoolean(_this, ulComponent, bNewValue, fTimeOffset);
        }

        static vr::EVRInputError Detour_CreateScalarComponent(
            vr::IVRDriverInput* _this, vr::PropertyContainerHandle_t ulContainer,
            const char* pchName, vr::VRInputComponentHandle_t* pHandle,
            vr::EVRScalarType eType, vr::EVRScalarUnits eUnits)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.createScalar) return vr::VRInputError_InvalidHandle;

            vr::EVRInputError err = orig.createScalar(_this, ulContainer, pchName, pHandle, eType, eUnits);
            if (err == vr::VRInputError_None && pHandle)
                OnInputComponentCreated(*pHandle, ulContainer, pchName, true);
            return err;
        }

        static vr::EVRInputError Detour_UpdateScalarComponent(
            vr::IVRDriverInput* _this, vr::VRInputComponentHandle_t ulComponent,
            float fNewValue, double fTimeOffset)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.updateScalar) return vr::VRInputError_InvalidHandle;

            OverrideScalarInput(ulComponent, fNewValue);
            return orig.updateScalar(_this, ulComponent, fNewValue, fTimeOffset);
        }

        // remembers which device each skeleton component belongs to (updates only carry the handle)
        static vr::EVRInputError Detour_CreateSkeletonComponent(
            vr::IVRDriverInput* _this,
            vr::PropertyContainerHandle_t ulContainer,
            const char* pchName,
            const char* pchSkeletonPath,
            const char* pchBasePosePath,
            vr::EVRSkeletalTrackingLevel eSkeletalTrackingLevel,
            const vr::VRBoneTransform_t* pGripLimitTransforms,
            uint32_t unGripLimitTransformCount,
            vr::VRInputComponentHandle_t* pHandle)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.createSkeleton) return vr::VRInputError_InvalidHandle;

            vr::EVRInputError err = orig.createSkeleton(_this, ulContainer, pchName, pchSkeletonPath,
                pchBasePosePath, eSkeletalTrackingLevel, pGripLimitTransforms, unGripLimitTransformCount, pHandle);

            if (err == vr::VRInputError_None && pHandle && pchSkeletonPath) {
                // "/skeleton/hand/left" | "/skeleton/hand/right"
                if (std::strstr(pchSkeletonPath, "left"))
                    OnSkeletonComponentCreated(*pHandle, ulContainer, vr::TrackedControllerRole_LeftHand);
                else if (std::strstr(pchSkeletonPath, "right"))
                    OnSkeletonComponentCreated(*pHandle, ulContainer, vr::TrackedControllerRole_RightHand);
            }
            return err;
        }

        static vr::EVRInputError Detour_UpdateSkeletonComponent(
            vr::IVRDriverInput* _this,
            vr::VRInputComponentHandle_t ulComponent,
            vr::EVRSkeletalMotionRange eMotionRange,
            const vr::VRBoneTransform_t* pTransforms,
            uint32_t unTransformCount)
        {
            InputOriginals orig = g_inputHooks.Get(GetVTable(_this));
            if (!orig.updateSkeleton) return vr::VRInputError_InvalidHandle;

            // whatever goes to SteamVR (patched or the driver's own bones) is the "final skeleton"
            vr::VRBoneTransform_t patched[kHandBoneCount];
            const vr::VRBoneTransform_t* finalBones = pTransforms;
            if (ApplySkeletalOverride(ulComponent, pTransforms, unTransformCount, patched))
                finalBones = patched;

            ObserveFinalSkeleton(ulComponent, eMotionRange, finalBones, unTransformCount);

            return orig.updateSkeleton(_this, ulComponent, eMotionRange, finalBones, unTransformCount);
        }

        // =========================================================================================
        // installing / removing the hooks
        // =========================================================================================

        static void HookServerDriverHost(void* pHost, const char* pchVersion)
        {
            HookInterfaceOnce(pHost, pchVersion, g_hostHooks, [&](void** vt, HostOriginals& orig) {
                HookSlot(vt, kHost_TrackedDeviceAdded, reinterpret_cast<void*>(&Detour_TrackedDeviceAdded),
                    reinterpret_cast<void**>(&orig.added), pchVersion, "TrackedDeviceAdded");
                HookSlot(vt, kHost_TrackedDevicePoseUpdated, reinterpret_cast<void*>(&Detour_TrackedDevicePoseUpdated),
                    reinterpret_cast<void**>(&orig.poseUpdated), pchVersion, "TrackedDevicePoseUpdated");
                return true;
                });
        }

        static void HookPropertiesInterface(void* pProps, const char* pchVersion)
        {
            HookInterfaceOnce(pProps, pchVersion, g_propsHooks, [&](void** vt, WritePropertyBatch_t& orig) {
                return HookSlot(vt, kProps_WritePropertyBatch, reinterpret_cast<void*>(&Detour_WritePropertyBatch),
                    reinterpret_cast<void**>(&orig), pchVersion, "WritePropertyBatch");
                });
        }

        static void HookInputInterface(void* pInput, const char* pchVersion)
        {
            HookInterfaceOnce(pInput, pchVersion, g_inputHooks, [&](void** vt, InputOriginals& orig) {
                const SlotHook hooks[] = {
                    { kInput_CreateBooleanComponent,  reinterpret_cast<void*>(&Detour_CreateBooleanComponent),  reinterpret_cast<void**>(&orig.createBoolean),  "CreateBooleanComponent" },
                    { kInput_UpdateBooleanComponent,  reinterpret_cast<void*>(&Detour_UpdateBooleanComponent),  reinterpret_cast<void**>(&orig.updateBoolean),  "UpdateBooleanComponent" },
                    { kInput_CreateScalarComponent,   reinterpret_cast<void*>(&Detour_CreateScalarComponent),   reinterpret_cast<void**>(&orig.createScalar),   "CreateScalarComponent" },
                    { kInput_UpdateScalarComponent,   reinterpret_cast<void*>(&Detour_UpdateScalarComponent),   reinterpret_cast<void**>(&orig.updateScalar),   "UpdateScalarComponent" },
                    { kInput_CreateSkeletonComponent, reinterpret_cast<void*>(&Detour_CreateSkeletonComponent), reinterpret_cast<void**>(&orig.createSkeleton), "CreateSkeletonComponent" },
                    { kInput_UpdateSkeletonComponent, reinterpret_cast<void*>(&Detour_UpdateSkeletonComponent), reinterpret_cast<void**>(&orig.updateSkeleton), "UpdateSkeletonComponent" },
                };
                return HookAll(vt, pchVersion, hooks, sizeof(hooks) / sizeof(hooks[0]));
                });
        }

        typedef void* (*GetGenericInterface_t)(vr::IVRDriverContext*, const char*,
            vr::EVRInitError*);

        static Hook<GetGenericInterface_t>
            g_getGenericInterfaceHook("IVRDriverContext::GetGenericInterface");

        static void* Detour_GetGenericInterface(vr::IVRDriverContext* _this,
            const char* pchInterfaceVersion,
            vr::EVRInitError* peError)
        {
            void* result = g_getGenericInterfaceHook.originalFunc(_this, pchInterfaceVersion, peError);

            if (result && pchInterfaceVersion) {
                if (HasPrefix(pchInterfaceVersion, "IVRServerDriverHost_"))
                    HookServerDriverHost(result, pchInterfaceVersion);
                else if (HasPrefix(pchInterfaceVersion, "IVRProperties_"))
                    HookPropertiesInterface(result, pchInterfaceVersion);
                else if (HasPrefix(pchInterfaceVersion, "IVRDriverInput_"))
                    HookInputInterface(result, pchInterfaceVersion);
            }

            return result;
        }

        bool Install(vr::IVRDriverContext* pDriverContext)
        {
            if (g_installed) return true;
            if (!pDriverContext) return false;
            if (!InitHookingLibrary()) return false;

            g_getGenericInterfaceHook.CreateFromVTable(
                pDriverContext, 0,
                reinterpret_cast<void*>(&Detour_GetGenericInterface));

            // interfaces our own driver already holds were fetched before the hook above existed
            if (vr::VRServerDriverHost())
                HookServerDriverHost(vr::VRServerDriverHost(), "IVRServerDriverHost (ours)");

            if (vr::VRProperties())
                HookPropertiesInterface(vr::VRProperties(), "IVRProperties (ours)");

            if (vr::VRDriverInput())
                HookInputInterface(vr::VRDriverInput(), "IVRDriverInput (ours)");

            g_installed = true;
            HookLog("[hooks] install complete");
            return true;
        }

        void Remove()
        {
            if (!g_installed) return;

            // restores render models and roles through the still installed hooks
            ClearAllRules();
            ForgetSkeletonComponents();
            ForgetInputComponents();

            g_getGenericInterfaceHook.Destroy();

            g_hostHooks.ForEachAndClear([](void** vt) {
                UnhookSlot(vt, kHost_TrackedDeviceAdded);
                UnhookSlot(vt, kHost_TrackedDevicePoseUpdated);
                });
            g_propsHooks.ForEachAndClear([](void** vt) {
                UnhookSlot(vt, kProps_WritePropertyBatch);
                });
            g_inputHooks.ForEachAndClear([](void** vt) {
                for (size_t slot : { kInput_CreateBooleanComponent, kInput_UpdateBooleanComponent,
                    kInput_CreateScalarComponent, kInput_UpdateScalarComponent,
                    kInput_CreateSkeletonComponent, kInput_UpdateSkeletonComponent })
                    UnhookSlot(vt, slot);
                });

            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                g_originalRenderModel.clear();
                g_originalRole.clear();
                g_indexToSerial.clear();
                g_serialToIndex.clear();
                g_containerToSerial.clear();
                g_serialToContainer.clear();
            }

            CleanupHookingLibrary();
            g_installed = false;
            HookLog("[hooks] removed");
        }

        // =========================================================================================
        // property rules (model visibility, role), applied from the poll thread
        // =========================================================================================

        static void ApplyModelVisibility(const std::string& serial, bool visible)
        {
            vr::PropertyContainerHandle_t container = FindContainer(serial);
            if (container == vr::k_ulInvalidPropertyContainer) return;

            vr::ETrackedPropertyError err = vr::TrackedProp_Success;
            std::string current = vr::VRProperties()->GetStringProperty(
                container, vr::Prop_RenderModelName_String, &err);

            if (!visible) {
                if (current.empty()) return;

                {
                    std::lock_guard<std::mutex> lock(g_stateMutex);
                    if (g_originalRenderModel.find(serial) == g_originalRenderModel.end())
                        g_originalRenderModel[serial] = current;
                }

                vr::VRProperties()->SetStringProperty(container, vr::Prop_RenderModelName_String, "");
                HookLog("[hooks] '%s' render model hidden (was '%s')", serial.c_str(), current.c_str());
            }
            else {
                std::string original;
                {
                    std::lock_guard<std::mutex> lock(g_stateMutex);
                    auto it = g_originalRenderModel.find(serial);
                    if (it == g_originalRenderModel.end()) return;
                    original = it->second;
                }
                if (current == original) return;

                vr::VRProperties()->SetStringProperty(container,
                    vr::Prop_RenderModelName_String,
                    original.c_str());
                HookLog("[hooks] '%s' render model restored to '%s'", serial.c_str(), original.c_str());
            }
        }

        static void ApplyRoleOverride(const std::string& serial, vr::ETrackedControllerRole role)
        {
            vr::PropertyContainerHandle_t container = FindContainer(serial);
            if (container == vr::k_ulInvalidPropertyContainer) return;

            vr::ETrackedPropertyError err = vr::TrackedProp_Success;
            int32_t current = vr::VRProperties()->GetInt32Property(
                container, vr::Prop_ControllerRoleHint_Int32, &err);

            if (err == vr::TrackedProp_Success && current == static_cast<int32_t>(role))
                return;

            vr::VRProperties()->SetInt32Property(container, vr::Prop_ControllerRoleHint_Int32,
                static_cast<int32_t>(role));
            HookLog("[hooks] '%s' role set to %d", serial.c_str(), (int)role);
        }

        static void RestoreRole(const std::string& serial, vr::ETrackedControllerRole original)
        {
            vr::PropertyContainerHandle_t container = FindContainer(serial);
            if (container == vr::k_ulInvalidPropertyContainer) return;

            vr::VRProperties()->SetInt32Property(container, vr::Prop_ControllerRoleHint_Int32,
                static_cast<int32_t>(original));
            HookLog("[hooks] '%s' role restored to %d", serial.c_str(), (int)original);
        }

        void TickPropertyRules()
        {
            if (!g_installed) return;

            RefreshDeviceTable();

            std::unordered_map<std::string, bool> modelRules;
            std::unordered_map<std::string, vr::ETrackedControllerRole> roleRules;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                modelRules = g_modelVisible;
                roleRules = g_roleOverride;
            }
            for (const auto& kv : modelRules)
                ApplyModelVisibility(kv.first, kv.second);
            for (const auto& kv : roleRules)
                ApplyRoleOverride(kv.first, kv.second);
        }

        // =========================================================================================
        // public rule setters
        // =========================================================================================

        void SetSerialBlocked(const std::string& serial, bool blocked)
        {
            SetMember(g_blockedSerials, serial, blocked);
        }

        void SetSerialHidden(const std::string& serial, bool hidden)
        {
            SetMember(g_hiddenSerials, serial, hidden);
        }

        void SetSerialModelVisible(const std::string& serial, bool visible)
        {
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                g_modelVisible[serial] = visible;
            }
            ApplyModelVisibility(serial, visible);
        }

        void SetSerialPositionOffset(const std::string& serial, double x, double y, double z)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            g_offsets[serial] = PacketPos{ x, y, z };
        }

        void ClearSerialPositionOffset(const std::string& serial)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            g_offsets.erase(serial);
        }

        void SetPoseSource(const std::string& targetSerial, const std::string& sourceSerial)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            if (sourceSerial.empty() || sourceSerial == targetSerial)
                g_poseSourceByTarget.erase(targetSerial);
            else
                g_poseSourceByTarget[targetSerial] = sourceSerial;
            RebuildPoseSourceSet_Locked();
        }

        void ClearPoseSource(const std::string& targetSerial)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            g_poseSourceByTarget.erase(targetSerial);
            RebuildPoseSourceSet_Locked();
        }

        void SetSerialRole(const std::string& serial, vr::ETrackedControllerRole role)
        {
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                g_roleOverride[serial] = role;
            }

            ApplyRoleOverride(serial, role);
        }

        void ClearSerialRole(const std::string& serial)
        {
            vr::ETrackedControllerRole original = vr::TrackedControllerRole_Invalid;
            bool hadOriginal = false;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                g_roleOverride.erase(serial);
                auto it = g_originalRole.find(serial);
                if (it != g_originalRole.end()) { original = it->second; hadOriginal = true; }
                g_originalRole.erase(serial);
            }
            if (hadOriginal) RestoreRole(serial, original);
        }

        void ClearAllRules()
        {
            std::unordered_map<std::string, std::string> modelsToRestore;
            std::unordered_map<std::string, vr::ETrackedControllerRole> rolesToRestore;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                modelsToRestore = g_originalRenderModel;
                rolesToRestore = g_originalRole;
                g_blockedSerials.clear();
                g_hiddenSerials.clear();
                g_offsets.clear();
                g_poseSourceByTarget.clear();
                g_poseSourceSerials.clear();
                g_latestPoseBySource.clear();
                g_modelVisible.clear();
                g_roleOverride.clear();
            }
            ClearAllSkeletalOverrides();   // after the lock: they take their own
            ClearAllInputOverrides();

            for (const auto& kv : modelsToRestore)
                ApplyModelVisibility(kv.first, true);
            for (const auto& kv : rolesToRestore)
                RestoreRole(kv.first, kv.second);
        }

    }
}