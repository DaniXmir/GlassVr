#include "skeletaloverride.h"
#include "controllerbase.h"
#include "controllerdata.h"
#include "controllerregistry.h"
#include "settings.h"
#include "hooking.h"

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <unordered_set>

namespace glassvr {
    namespace hooks {

        const char* const kFingerNames[kFingerCount] = { "thumb", "index", "middle", "ring", "pinky" };

        namespace {
            struct FingerBones { int first, last, aux; };
            const FingerBones kFingerBones[kFingerCount] = {
                {  2,  5, 26 },   // thumb
                {  6, 10, 27 },   // index
                { 11, 15, 28 },   // middle
                { 16, 20, 29 },   // ring
                { 21, 25, 30 },   // pinky
            };

            struct Component {
                vr::PropertyContainerHandle_t container = vr::k_ulInvalidPropertyContainer;
                vr::ETrackedControllerRole    hand = vr::TrackedControllerRole_Invalid;
                std::string                   serial;
            };

            std::mutex                                                  g_mutex;
            std::unordered_map<std::string, SkeletalOverride>           g_rules;
            std::unordered_map<vr::VRInputComponentHandle_t, Component> g_components;
            std::unordered_set<vr::VRInputComponentHandle_t>            g_warnedUnknown;
            std::shared_ptr<const HandBoneComputer>                     g_compute;

            std::atomic<bool> g_anyRules{ false };
            std::string       g_modes[2] = { "pipe", "pipe" };

            // ---- ring / pinky curl of the FINAL skeleton (what SteamVR receives), for "ring and pinky affect grip" ----
            struct FingerCurlSample {
                float    ring[2] = { 0.f, 0.f };    // by motion range: 0 = with controller, 1 = without controller
                float    pinky[2] = { 0.f, 0.f };
                uint64_t stamp[2] = { 0, 0 };       // ms of the last update, 0 = never
            };

            // open and closed hand of GlassVR's own hand simulation: curl is measured as how far the finger joints
            // are between those two (a ratio, so a few degrees of different rest pose in the other driver wash out)
            struct HandReference {
                bool                  valid = false;
                vr::VRBoneTransform_t open[kHandBoneCount];
                float                 span[2] = { 0.f, 0.f };   // joint angle sum open -> closed: ring, pinky
            };

            std::unordered_set<std::string>                                      g_gripSerials;
            std::unordered_map<vr::PropertyContainerHandle_t, FingerCurlSample>  g_curlByContainer;
            HandReference                                                        g_handRef[2];   // left, right
            std::atomic<bool>                                                    g_anyGrip{ false };

            constexpr uint64_t kCurlFreshMs = 500;

            uint64_t NowMs() {
                return (uint64_t)std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::steady_clock::now().time_since_epoch()).count();
            }

            float QuatAngle(const vr::HmdQuaternionf_t& a, const vr::HmdQuaternionf_t& b) {
                float d = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z;
                if (d < 0.0f) d = -d;
                if (d > 1.0f) d = 1.0f;
                return 2.0f * std::acos(d);
            }

            // the bending joints of a finger: proximal, intermediate, distal (metacarpal and tip do not curl)
            float JointAngleSum(const vr::VRBoneTransform_t* cur, const vr::VRBoneTransform_t* ref, int finger) {
                const FingerBones& fb = kFingerBones[finger];
                float sum = 0.0f;
                for (int b = fb.first + 1; b <= fb.last - 1; b++)
                    sum += QuatAngle(cur[b].orientation, ref[b].orientation);
                return sum;
            }

            float Curl01(float angle, float span) {
                if (span < 0.05f) return 0.0f;
                float c = angle / span;
                if (c < 0.0f) c = 0.0f;
                if (c > 1.0f) c = 1.0f;
                return c;
            }

            // g_mutex held
            bool BuildHandReference_Locked(int idx, vr::ETrackedControllerRole hand, const HandBoneComputer& compute) {
                float zero[kFingerCount], one[kFingerCount];
                for (int i = 0; i < kFingerCount; i++) { zero[i] = 0.0f; one[i] = 1.0f; }

                vr::VRBoneTransform_t closed[kHandBoneCount];
                HandReference& ref = g_handRef[idx];
                for (uint32_t b = 0; b < kHandBoneCount; b++) {
                    ref.open[b].position = { 0.f, 0.f, 0.f, 1.f };
                    ref.open[b].orientation = { 1.f, 0.f, 0.f, 0.f };
                    closed[b] = ref.open[b];
                }
                compute(hand, zero, zero, ref.open);
                compute(hand, one, zero, closed);

                ref.span[0] = JointAngleSum(closed, ref.open, 3);   // ring
                ref.span[1] = JointAngleSum(closed, ref.open, 4);   // pinky
                ref.valid = true;
                return true;
            }

            void RefreshAnyRules_Locked() {
                g_anyRules.store(!g_rules.empty(), std::memory_order_relaxed);
            }
        }

        void SetHandBoneComputer(HandBoneComputer fn) {
            auto shared = std::make_shared<const HandBoneComputer>(std::move(fn));
            std::lock_guard<std::mutex> lock(g_mutex);
            g_compute = shared;
        }

        void SetSkeletalOverride(const std::string& serial, const SkeletalOverride& rule) {
            if (!rule.active()) {
                ClearSkeletalOverride(serial);
                return;
            }
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_rules[serial] = rule;
                RefreshAnyRules_Locked();
            }
            std::string fingers;
            for (int i = 0; i < kFingerCount; i++) {
                if (!rule.fingers[i].any()) continue;
                fingers += std::string(" ") + kFingerNames[i] + "(" +
                    (rule.fingers[i].curl ? "c" : "") + (rule.fingers[i].splay ? "s" : "") + ")";
            }
            HookLog("[skeletal] '%s' <- %s:%s", serial.c_str(), rule.source.c_str(), fingers.c_str());
        }

        void ClearSkeletalOverride(const std::string& serial) {
            std::lock_guard<std::mutex> lock(g_mutex);
            if (g_rules.erase(serial)) HookLog("[skeletal] '%s' reverted", serial.c_str());
            RefreshAnyRules_Locked();
        }

        void ClearAllSkeletalOverrides() {
            std::lock_guard<std::mutex> lock(g_mutex);
            g_rules.clear();
            RefreshAnyRules_Locked();
        }

        void ForgetSkeletonComponents() {
            std::lock_guard<std::mutex> lock(g_mutex);
            g_components.clear();
            g_warnedUnknown.clear();
            g_curlByContainer.clear();
        }

        void SetFingerGripTracking(const std::string& serial, bool enabled) {
            std::lock_guard<std::mutex> lock(g_mutex);
            if (enabled) {
                if (g_gripSerials.insert(serial).second)
                    HookLog("[skeletal] '%s' ring/pinky grip tracking on", serial.c_str());
            }
            else if (g_gripSerials.erase(serial)) {
                HookLog("[skeletal] '%s' ring/pinky grip tracking off", serial.c_str());
            }
            g_anyGrip.store(!g_gripSerials.empty(), std::memory_order_relaxed);
        }

        void ClearAllFingerGripTracking() {
            std::lock_guard<std::mutex> lock(g_mutex);
            g_gripSerials.clear();
            g_curlByContainer.clear();
            g_anyGrip.store(false, std::memory_order_relaxed);
        }

        // Called for EVERY skeleton update with the bones that really go to SteamVR (after ApplySkeletalOverride).
        void ObserveFinalSkeleton(vr::VRInputComponentHandle_t handle, vr::EVRSkeletalMotionRange range,
            const vr::VRBoneTransform_t* bones, uint32_t count) {

            if (!g_anyGrip.load(std::memory_order_relaxed)) return;
            if (!bones || count != kHandBoneCount) return;

            std::lock_guard<std::mutex> lock(g_mutex);

            auto comp = g_components.find(handle);
            if (comp == g_components.end()) return;

            if (comp->second.serial.empty()) {
                comp->second.serial = ResolveContainerSerial(comp->second.container);
                if (comp->second.serial.empty()) return;
            }
            if (g_gripSerials.find(comp->second.serial) == g_gripSerials.end()) return;

            const int hIdx = (comp->second.hand == vr::TrackedControllerRole_RightHand) ? 1 : 0;
            HandReference& ref = g_handRef[hIdx];
            if (!ref.valid) {
                if (!g_compute || !*g_compute) return;          // hand simulation not registered (yet)
                BuildHandReference_Locked(hIdx, comp->second.hand, *g_compute);
            }

            const int r = (range == vr::VRSkeletalMotionRange_WithoutController) ? 1 : 0;
            FingerCurlSample& smp = g_curlByContainer[comp->second.container];
            smp.ring[r] = Curl01(JointAngleSum(bones, ref.open, 3), ref.span[0]);
            smp.pinky[r] = Curl01(JointAngleSum(bones, ref.open, 4), ref.span[1]);
            smp.stamp[r] = NowMs();
        }

        // false = no fresh final skeleton for this device (then the grip is left alone)
        bool GetFinalRingPinkyCurl(vr::PropertyContainerHandle_t container, float& ring, float& pinky) {
            std::lock_guard<std::mutex> lock(g_mutex);
            auto it = g_curlByContainer.find(container);
            if (it == g_curlByContainer.end()) return false;

            const FingerCurlSample& smp = it->second;
            const uint64_t now = NowMs();
            // the real finger pose is the "without controller" range, "with controller" is limited by the grip
            // limit; use whichever the driver actually sends
            for (int r = 1; r >= 0; r--) {
                if (smp.stamp[r] != 0 && now - smp.stamp[r] <= kCurlFreshMs) {
                    ring = smp.ring[r];
                    pinky = smp.pinky[r];
                    return true;
                }
            }
            return false;
        }

        static void EnsureHandBoneComputer() {
            static bool tried = false;
            if (tried) return;
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                if (g_compute) { tried = true; return; }
            }
            tried = true;
            std::unique_ptr<ControllerBase> probe(
                ControllerRegistry::Create(ControllerRegistry::DefaultType(), false));
            if (!probe) HookLog("[skeletal] could not create a controller to get the hand simulation from");
        }

        void TickSkeletalOverrides() {
            bool used[2] = { false, false };
            std::string modes[2] = { "pipe", "pipe" };

            {
                std::lock_guard<std::mutex> lock(g_mutex);
                for (const auto& kv : g_rules) {
                    if (kv.second.source == "cl") {
                        used[0] = true;
                        modes[0] = GetStringFromSettingsByKey("cl skeletal mode");
                        if (modes[0].empty()) modes[0] = GetStringFromSettingsByKey("clskeletal mode"); // Fallback
                    }
                    else if (kv.second.source == "cr") {
                        used[1] = true;
                        modes[1] = GetStringFromSettingsByKey("cr skeletal mode");
                        if (modes[1].empty()) modes[1] = GetStringFromSettingsByKey("crskeletal mode"); // Fallback
                    }
                }
            }

            bool needGrip;
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                needGrip = !g_gripSerials.empty();
            }
            if (used[0] || used[1] || needGrip) EnsureHandBoneComputer();

            for (int i = 0; i < 2; i++) {
                if (!used[i]) continue;
                const bool right = (i == 1);
                const std::string device = right ? "cr" : "cl";

                // Ensure the CommManager is created and updated with Serial/Bluetooth if needed,
                // even if the GlassVR controller itself is disabled.
                ControllerDataHub::Get().Ensure(right);

                if (modes[i] == "serial" || modes[i] == "bluetooth") {
                    ControllerDataHub::Get().UpdateSerialPort(device, "skeletal");
                }

                std::lock_guard<std::mutex> lock(g_mutex);
                g_modes[i] = modes[i];
            }
        }

        void OnSkeletonComponentCreated(vr::VRInputComponentHandle_t handle,
            vr::PropertyContainerHandle_t container,
            vr::ETrackedControllerRole hand) {
            Component c;
            c.container = container;
            c.hand = hand;
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_components[handle] = c;
            }
            HookLog("[skeletal] skeleton component %llu registered (%s hand)",
                (unsigned long long)handle, hand == vr::TrackedControllerRole_LeftHand ? "left" : "right");
        }

        bool ApplySkeletalOverride(vr::VRInputComponentHandle_t handle,
            const vr::VRBoneTransform_t* in, uint32_t count,
            vr::VRBoneTransform_t* out) {

            if (!g_anyRules.load(std::memory_order_relaxed)) return false;
            if (!in || count != kHandBoneCount) return false;

            SkeletalOverride                        rule;
            vr::ETrackedControllerRole              hand;
            std::shared_ptr<const HandBoneComputer> compute;

            {
                std::lock_guard<std::mutex> lock(g_mutex);
                auto comp = g_components.find(handle);
                if (comp == g_components.end()) {
                    if (g_warnedUnknown.insert(handle).second)
                        HookLog("[skeletal] update for unknown skeleton component %llu (created before hooks?)",
                            (unsigned long long)handle);
                    return false;
                }

                if (comp->second.serial.empty()) {
                    comp->second.serial = ResolveContainerSerial(comp->second.container);
                    if (comp->second.serial.empty()) return false;
                }

                auto r = g_rules.find(comp->second.serial);
                if (r == g_rules.end()) return false;

                rule = r->second;
                hand = comp->second.hand;
                compute = g_compute;
            }

            if (!compute || !*compute) return false;

            const bool srcRight = (rule.source == "cr");
            const int idx = srcRight ? 1 : 0;

            std::string mode;
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                mode = g_modes[idx];
            }

            // Fetch from the SOURCE hand's transport (UDP/Pipe/Serial/Bluetooth)
            const PacketSkeletal pk = ControllerDataHub::Get().GetSkeletal(srcRight, mode);

            float curls[kFingerCount], splays[kFingerCount];
            for (int i = 0; i < kFingerCount; i++) {
                curls[i] = rule.fingers[i].curl ? (float)pk.flexions[i * 4] : 0.0f;
                splays[i] = rule.fingers[i].splay ? (float)pk.splays[i] : 0.0f;
            }

            vr::VRBoneTransform_t simulated[kHandBoneCount];
            for (uint32_t b = 0; b < kHandBoneCount; b++) {
                simulated[b].position = { 0.f, 0.f, 0.f, 1.f };
                simulated[b].orientation = { 1.f, 0.f, 0.f, 0.f };
            }
            (*compute)(hand, curls, splays, simulated);

            std::memcpy(out, in, sizeof(vr::VRBoneTransform_t) * kHandBoneCount);

            for (int i = 0; i < kFingerCount; i++) {
                if (!rule.fingers[i].any()) continue;
                const FingerBones& fb = kFingerBones[i];
                for (int b = fb.first; b <= fb.last; b++) out[b].orientation = simulated[b].orientation;
                out[fb.aux].orientation = simulated[fb.aux].orientation;
            }
            return true;
        }

    }
}