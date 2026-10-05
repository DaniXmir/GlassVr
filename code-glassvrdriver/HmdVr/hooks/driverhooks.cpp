//very sloppy needs checking
#include "driverhooks.h"
#include "hooking.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <cstring>

namespace glassvr {
    namespace hooks {
        //duplicated struct from comm
        struct PositionOffset { double x = 0, y = 0, z = 0; };

        static std::mutex                                        g_stateMutex;
        static std::unordered_set<std::string>                   g_blockedSerials;
        static std::unordered_set<std::string>                   g_hiddenSerials;
        static std::unordered_map<std::string, PositionOffset>   g_offsets;

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

        static std::mutex                                  g_hostMutex;
        static std::unordered_map<void**, HostOriginals>   g_hostOriginals;

        static HostOriginals LookupOriginals(void* pHost)
        {
            void** vt = GetVTable(pHost);
            std::lock_guard<std::mutex> lock(g_hostMutex);
            auto it = g_hostOriginals.find(vt);
            return (it == g_hostOriginals.end()) ? HostOriginals{} : it->second;
        }

        typedef vr::ETrackedPropertyError(*WritePropertyBatch_t)(
            vr::IVRProperties*, vr::PropertyContainerHandle_t,
            vr::PropertyWrite_t*, uint32_t);

        static std::mutex                                         g_propsMutex;
        static std::unordered_map<void**, WritePropertyBatch_t>   g_propsOriginals;

        static WritePropertyBatch_t LookupPropsOriginal(void* pProps)
        {
            void** vt = GetVTable(pProps);
            std::lock_guard<std::mutex> lock(g_propsMutex);
            auto it = g_propsOriginals.find(vt);
            return (it == g_propsOriginals.end()) ? nullptr : it->second;
        }

        static std::string ReadSerialProperty(uint32_t unWhichDevice)
        {
            if (!vr::VRProperties()) return std::string();

            vr::PropertyContainerHandle_t container =
                vr::VRProperties()->TrackedDeviceToPropertyContainer(unWhichDevice);
            if (container == vr::k_ulInvalidPropertyContainer)
                return std::string();

            vr::ETrackedPropertyError err = vr::TrackedProp_Success;
            std::string serial = vr::VRProperties()->GetStringProperty(
                container, vr::Prop_SerialNumber_String, &err);

            if (err != vr::TrackedProp_Success) return std::string();
            return serial;
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

        static vr::PropertyContainerHandle_t ContainerForSerial(const std::string& serial)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            auto it = g_serialToContainer.find(serial);
            return (it == g_serialToContainer.end()) ? vr::k_ulInvalidPropertyContainer : it->second;
        }

        std::string SerialForDeviceIndex(uint32_t unWhichDevice)
        {
            return ResolveSerial(unWhichDevice);
        }

        static bool Detour_TrackedDeviceAdded(vr::IVRServerDriverHost* _this,
            const char* pchSerial,
            vr::ETrackedDeviceClass eClass,
            vr::ITrackedDeviceServerDriver* pDriver)
        {
            HostOriginals orig = LookupOriginals(_this);
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
            HostOriginals orig = LookupOriginals(_this);
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
            PositionOffset offset;
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

            vr::DriverPose_t pose = hasSourcePose ? sourcePose : newPose;

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
            WritePropertyBatch_t orig = LookupPropsOriginal(_this);
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

        typedef void* (*GetGenericInterface_t)(vr::IVRDriverContext*, const char*,
            vr::EVRInitError*);

        static Hook<GetGenericInterface_t>
            g_getGenericInterfaceHook("IVRDriverContext::GetGenericInterface");

        static void HookServerDriverHost(void* pHost, const char* pchVersion)
        {
            if (!pHost) return;

            void** vt = GetVTable(pHost);
            {
                std::lock_guard<std::mutex> lock(g_hostMutex);
                if (g_hostOriginals.find(vt) != g_hostOriginals.end())
                    return;
            }

            HostOriginals orig;

            if (MH_CreateHook(vt[0], reinterpret_cast<LPVOID>(&Detour_TrackedDeviceAdded),
                reinterpret_cast<LPVOID*>(&orig.added)) != MH_OK ||
                MH_EnableHook(vt[0]) != MH_OK) {
                HookLog("[hooks] failed to hook %s::TrackedDeviceAdded", pchVersion);
            }

            if (MH_CreateHook(vt[1], reinterpret_cast<LPVOID>(&Detour_TrackedDevicePoseUpdated),
                reinterpret_cast<LPVOID*>(&orig.poseUpdated)) != MH_OK ||
                MH_EnableHook(vt[1]) != MH_OK) {
                HookLog("[hooks] failed to hook %s::TrackedDevicePoseUpdated", pchVersion);
            }

            {
                std::lock_guard<std::mutex> lock(g_hostMutex);
                g_hostOriginals[vt] = orig;
            }
            HookLog("[hooks] hooked %s (vtable %p)", pchVersion, (void*)vt);
        }

        static void HookPropertiesInterface(void* pProps, const char* pchVersion)
        {
            if (!pProps) return;

            void** vt = GetVTable(pProps);
            {
                std::lock_guard<std::mutex> lock(g_propsMutex);
                if (g_propsOriginals.find(vt) != g_propsOriginals.end())
                    return;
            }

            WritePropertyBatch_t original = nullptr;

            if (MH_CreateHook(vt[1], reinterpret_cast<LPVOID>(&Detour_WritePropertyBatch),
                reinterpret_cast<LPVOID*>(&original)) != MH_OK ||
                MH_EnableHook(vt[1]) != MH_OK) {
                HookLog("[hooks] failed to hook %s::WritePropertyBatch", pchVersion);
                return;
            }

            {
                std::lock_guard<std::mutex> lock(g_propsMutex);
                g_propsOriginals[vt] = original;
            }
            HookLog("[hooks] hooked %s (vtable %p)", pchVersion, (void*)vt);
        }

        static void* Detour_GetGenericInterface(vr::IVRDriverContext* _this,
            const char* pchInterfaceVersion,
            vr::EVRInitError* peError)
        {
            void* result = g_getGenericInterfaceHook.originalFunc(_this, pchInterfaceVersion, peError);

            if (result && pchInterfaceVersion) {
                if (strncmp(pchInterfaceVersion, "IVRServerDriverHost_", 20) == 0) {
                    HookServerDriverHost(result, pchInterfaceVersion);
                }
                else if (strncmp(pchInterfaceVersion, "IVRProperties_", 14) == 0) {
                    HookPropertiesInterface(result, pchInterfaceVersion);
                }
            }

            return result;
        }

        static void ApplyModelVisibility(const std::string& serial, bool visible)
        {
            if (!vr::VRProperties()) return;

            uint32_t index = DeviceIndexForSerial(serial);
            if (index == vr::k_unTrackedDeviceIndexInvalid) return;

            vr::PropertyContainerHandle_t container =
                vr::VRProperties()->TrackedDeviceToPropertyContainer(index);
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
            if (!vr::VRProperties()) return;

            vr::PropertyContainerHandle_t container = ContainerForSerial(serial);
            if (container == vr::k_ulInvalidPropertyContainer) {
                uint32_t index = DeviceIndexForSerial(serial);
                if (index == vr::k_unTrackedDeviceIndexInvalid) return;
                container = vr::VRProperties()->TrackedDeviceToPropertyContainer(index);
                if (container == vr::k_ulInvalidPropertyContainer) return;
            }

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
            if (!vr::VRProperties()) return;
            vr::PropertyContainerHandle_t container = ContainerForSerial(serial);
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

        bool Install(vr::IVRDriverContext* pDriverContext)
        {
            if (g_installed) return true;
            if (!pDriverContext) return false;
            if (!InitHookingLibrary()) return false;

            g_getGenericInterfaceHook.CreateFromVTable(
                pDriverContext, 0,
                reinterpret_cast<void*>(&Detour_GetGenericInterface));

            if (vr::VRServerDriverHost())
                HookServerDriverHost(vr::VRServerDriverHost(), "IVRServerDriverHost (ours)");

            if (vr::VRProperties())
                HookPropertiesInterface(vr::VRProperties(), "IVRProperties (ours)");

            g_installed = true;
            HookLog("[hooks] install complete");
            return true;
        }

        void Remove()
        {
            if (!g_installed) return;

            std::unordered_map<std::string, std::string> modelsToRestore;
            std::unordered_map<std::string, vr::ETrackedControllerRole> rolesToRestore;
            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                modelsToRestore = g_originalRenderModel;
                rolesToRestore = g_originalRole;
                g_modelVisible.clear();
                g_roleOverride.clear();
            }
            for (const auto& kv : modelsToRestore)
                ApplyModelVisibility(kv.first, true);
            for (const auto& kv : rolesToRestore)
                RestoreRole(kv.first, kv.second);

            g_getGenericInterfaceHook.Destroy();

            {
                std::lock_guard<std::mutex> lock(g_hostMutex);
                for (auto& kv : g_hostOriginals) {
                    MH_DisableHook(kv.first[0]);
                    MH_RemoveHook(kv.first[0]);
                    MH_DisableHook(kv.first[1]);
                    MH_RemoveHook(kv.first[1]);
                }
                g_hostOriginals.clear();
            }

            {
                std::lock_guard<std::mutex> lock(g_propsMutex);
                for (auto& kv : g_propsOriginals) {
                    MH_DisableHook(kv.first[1]);
                    MH_RemoveHook(kv.first[1]);
                }
                g_propsOriginals.clear();
            }

            {
                std::lock_guard<std::mutex> lock(g_stateMutex);
                g_blockedSerials.clear();
                g_hiddenSerials.clear();
                g_offsets.clear();
                g_poseSourceByTarget.clear();
                g_poseSourceSerials.clear();
                g_latestPoseBySource.clear();
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

        void SetSerialBlocked(const std::string& serial, bool blocked)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            if (blocked) g_blockedSerials.insert(serial);
            else         g_blockedSerials.erase(serial);
        }

        void SetSerialHidden(const std::string& serial, bool hidden)
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            if (hidden) g_hiddenSerials.insert(serial);
            else        g_hiddenSerials.erase(serial);
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
            PositionOffset o; o.x = x; o.y = y; o.z = z;
            g_offsets[serial] = o;
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
            for (const auto& kv : modelsToRestore)
                ApplyModelVisibility(kv.first, true);
            for (const auto& kv : rolesToRestore)
                RestoreRole(kv.first, kv.second);
        }

    }
}