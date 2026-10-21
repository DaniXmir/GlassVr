#pragma once

#include "hookcommon.h"

#include <functional>
#include <string>

namespace glassvr {
    namespace hooks {

        constexpr int      kFingerCount = 5;
        constexpr uint32_t kHandBoneCount = 31;

        extern const char* const kFingerNames[kFingerCount];

        struct FingerOverride {
            bool curl = false;
            bool splay = false;

            bool any() const { return curl || splay; }
            bool operator==(const FingerOverride& o) const { return curl == o.curl && splay == o.splay; }
        };

        struct SkeletalOverride {
            std::string    source;
            FingerOverride fingers[kFingerCount];

            bool active() const
            {
                if (source.empty()) return false;
                for (const FingerOverride& f : fingers)
                    if (f.any()) return true;
                return false;
            }

            bool operator==(const SkeletalOverride& o) const
            {
                if (source != o.source) return false;
                for (int i = 0; i < kFingerCount; i++)
                    if (!(fingers[i] == o.fingers[i])) return false;
                return true;
            }
        };

        void SetSkeletalOverride(const std::string& serial, const SkeletalOverride& rule);
        void ClearSkeletalOverride(const std::string& serial);
        void ClearAllSkeletalOverrides();
        void ForgetSkeletonComponents();

        void TickSkeletalOverrides();

        void OnSkeletonComponentCreated(vr::VRInputComponentHandle_t handle,
            vr::PropertyContainerHandle_t container,
            vr::ETrackedControllerRole hand);

        bool ApplySkeletalOverride(vr::VRInputComponentHandle_t handle,
            const vr::VRBoneTransform_t* in, uint32_t count,
            vr::VRBoneTransform_t* out);

        using HandBoneComputer = std::function<void(vr::ETrackedControllerRole role,
            const float* curls,
            const float* splays,
            vr::VRBoneTransform_t* out)>;
        void SetHandBoneComputer(HandBoneComputer fn);

        void SetFingerGripTracking(const std::string& serial, bool enabled);
        void ClearAllFingerGripTracking();
        void ObserveFinalSkeleton(vr::VRInputComponentHandle_t handle, vr::EVRSkeletalMotionRange range,
            const vr::VRBoneTransform_t* bones, uint32_t count);
        bool GetFinalRingPinkyCurl(vr::PropertyContainerHandle_t container, float& ring, float& pinky);

    }
}