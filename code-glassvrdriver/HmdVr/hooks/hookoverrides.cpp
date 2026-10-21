#include "hookoverrides.h"
#include "driverhooks.h"
#include "hooking.h"
#include "skeletaloverride.h"
#include "inputoverride.h"

#include "settings.h"

#include <atomic>
#include <cctype>
#include <chrono>
#include <condition_variable>
#include <map>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace glassvr {
    namespace hooks {
        namespace overrides {

            const char* kOverridesKey = "hook overrides";

            struct DeviceOverride
            {
                std::string serial;

                bool        disable = false;
                bool        modelVisible = true;
                std::string trackingSource;

                bool                      hasRole = false;
                vr::ETrackedControllerRole role = vr::TrackedControllerRole_Invalid;

                SkeletalOverride          skeletal;
                InputOverride             input;

                bool operator==(const DeviceOverride& o) const
                {
                    return serial == o.serial
                        && disable == o.disable
                        && modelVisible == o.modelVisible
                        && trackingSource == o.trackingSource
                        && hasRole == o.hasRole
                        && (!hasRole || role == o.role)
                        && skeletal == o.skeletal
                        && input == o.input;
                }
                bool operator!=(const DeviceOverride& o) const { return !(*this == o); }
            };

            static std::string ToLower(std::string s)
            {
                for (char& c : s) c = (char)tolower((unsigned char)c);
                return s;
            }

            static bool ParseRole(const std::string& text, vr::ETrackedControllerRole& outRole)
            {
                const std::string v = ToLower(text);

                if (v.empty() || v == "pass")   return false;
                if (v == "left") { outRole = vr::TrackedControllerRole_LeftHand;  return true; }
                if (v == "right") { outRole = vr::TrackedControllerRole_RightHand; return true; }
                if (v == "optout") { outRole = vr::TrackedControllerRole_OptOut;    return true; }
                return false;
            }

            static SkeletalOverride ParseSkeletal(const SettingsDict& dict)
            {
                SkeletalOverride s;

                const std::string source = ToLower(DictGetString(dict, "skeletal override", ""));
                if (source == "cl" || source == "cr") s.source = source;

                for (int i = 0; i < kFingerCount; i++) {
                    const std::string finger = kFingerNames[i];
                    s.fingers[i].curl = DictGetBool(dict, finger + " curl override", false);
                    s.fingers[i].splay = DictGetBool(dict, finger + " splay override", false);
                }
                return s;
            }

            static InputOverride ParseInput(const SettingsDict& dict)
            {
                InputOverride in;

                const std::string source = ToLower(DictGetString(dict, "input override", ""));
                if (source == "cl" || source == "cr") in.source = source;

                for (int control = 0; control < kInputControlCount; control++)
                    for (int channel = 0; channel < kInputChannelCount; channel++)
                        if (InputChannelValid(control, channel))
                            in.enabled[InputSlot(control, channel)] = DictGetBool(dict, InputOverrideKey(control, channel), false);

                in.ringPinkyGrip = DictGetBool(dict, "ring and pinky affect grip", false);
                return in;
            }

            static DeviceOverride ParseOverride(const SettingsDict& dict)
            {
                DeviceOverride o;
                o.serial = DictGetString(dict, "serial");
                o.disable = DictGetBool(dict, "disable", false);
                o.modelVisible = DictGetBool(dict, "model visible", true);
                o.trackingSource = DictGetString(dict, "override tracking serial", "");
                o.hasRole = ParseRole(DictGetString(dict, "override role", "pass"), o.role);
                o.skeletal = ParseSkeletal(dict);
                o.input = ParseInput(dict);
                return o;
            }

            static void ApplyOverride(const DeviceOverride& o)
            {
                hooks::SetSerialBlocked(o.serial, o.disable);
                hooks::SetSerialHidden(o.serial, o.disable);

                hooks::SetSerialModelVisible(o.serial, o.modelVisible);

                if (o.trackingSource.empty())
                    hooks::ClearPoseSource(o.serial);
                else
                    hooks::SetPoseSource(o.serial, o.trackingSource);

                if (o.hasRole)
                    hooks::SetSerialRole(o.serial, o.role);
                else
                    hooks::ClearSerialRole(o.serial);

                if (o.skeletal.active())
                    hooks::SetSkeletalOverride(o.serial, o.skeletal);
                else
                    hooks::ClearSkeletalOverride(o.serial);

                if (o.input.active())
                    hooks::SetInputOverride(o.serial, o.input);
                else
                    hooks::ClearInputOverride(o.serial);

                HookLog("[overrides] '%s' disable=%d model=%d track<-'%s' role=%s",
                    o.serial.c_str(), (int)o.disable, (int)o.modelVisible,
                    o.trackingSource.c_str(), o.hasRole ? std::to_string((int)o.role).c_str() : "pass");
            }

            static void RevertOverride(const std::string& serial)
            {
                hooks::SetSerialBlocked(serial, false);
                hooks::SetSerialHidden(serial, false);
                hooks::SetSerialModelVisible(serial, true);
                hooks::ClearPoseSource(serial);
                hooks::ClearSerialPositionOffset(serial);
                hooks::ClearSerialRole(serial);
                hooks::ClearSkeletalOverride(serial);
                hooks::ClearInputOverride(serial);

                HookLog("[overrides] '%s' reverted", serial.c_str());
            }

            static std::mutex                              g_activeMutex;
            static std::map<std::string, DeviceOverride>   g_active;

            static std::thread              g_thread;
            static std::atomic<bool>        g_running{ false };
            static std::mutex               g_sleepMutex;
            static std::condition_variable  g_sleepCv;

            void PollOnce()
            {
                std::vector<SettingsDict> dicts = GetDictArrayFromSettingsByKey(kOverridesKey);

                std::map<std::string, DeviceOverride> wanted;
                for (const SettingsDict& d : dicts) {
                    DeviceOverride o = ParseOverride(d);
                    if (o.serial.empty()) continue;
                    if (o.trackingSource == o.serial) o.trackingSource.clear();
                    wanted[o.serial] = o;
                }

                std::lock_guard<std::mutex> lock(g_activeMutex);

                for (auto it = g_active.begin(); it != g_active.end(); ) {
                    if (wanted.find(it->first) == wanted.end()) {
                        RevertOverride(it->first);
                        it = g_active.erase(it);
                    }
                    else {
                        ++it;
                    }
                }

                for (const auto& kv : wanted) {
                    auto cur = g_active.find(kv.first);
                    if (cur == g_active.end() || cur->second != kv.second) {
                        ApplyOverride(kv.second);
                        g_active[kv.first] = kv.second;
                    }
                }

                hooks::TickPropertyRules();
                hooks::TickSkeletalOverrides();
                hooks::TickInputOverrides();
            }

            static void PollLoop(int intervalMs)
            {
                HookLog("[overrides] poll thread started (%d ms)", intervalMs);

                while (g_running.load()) {
                    PollOnce();

                    std::unique_lock<std::mutex> lock(g_sleepMutex);
                    g_sleepCv.wait_for(lock, std::chrono::milliseconds(intervalMs),
                        [] { return !g_running.load(); });
                }

                HookLog("[overrides] poll thread stopped");
            }

            void Start(int pollIntervalMs)
            {
                if (g_running.exchange(true)) return;
                if (pollIntervalMs < 20) pollIntervalMs = 20;
                g_thread = std::thread(PollLoop, pollIntervalMs);
            }

            void Stop()
            {
                if (!g_running.exchange(false)) return;

                g_sleepCv.notify_all();
                if (g_thread.joinable()) g_thread.join();

                std::lock_guard<std::mutex> lock(g_activeMutex);
                for (const auto& kv : g_active)
                    RevertOverride(kv.first);
                g_active.clear();
            }

        }
    }
}