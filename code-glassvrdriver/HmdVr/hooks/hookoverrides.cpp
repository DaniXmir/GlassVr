#include "hookoverrides.h"
#include "driverhooks.h"
#include "hooking.h"

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

                bool operator==(const DeviceOverride& o) const
                {
                    return serial == o.serial
                        && disable == o.disable
                        && modelVisible == o.modelVisible
                        && trackingSource == o.trackingSource
                        && hasRole == o.hasRole
                        && (!hasRole || role == o.role);
                }
                bool operator!=(const DeviceOverride& o) const { return !(*this == o); }
            };

            static bool ParseRole(const std::string& text, vr::ETrackedControllerRole& outRole)
            {
                std::string v = text;
                for (char& c : v) c = (char)tolower((unsigned char)c);

                if (v.empty() || v == "pass")   return false;
                if (v == "left") { outRole = vr::TrackedControllerRole_LeftHand;  return true; }
                if (v == "right") { outRole = vr::TrackedControllerRole_RightHand; return true; }
                if (v == "optout") { outRole = vr::TrackedControllerRole_OptOut;    return true; }
                return false;
            }

            static DeviceOverride ParseOverride(const SettingsDict& dict)
            {
                DeviceOverride o;
                o.serial = DictGetString(dict, "serial");
                o.disable = DictGetBool(dict, "disable", false);
                o.modelVisible = DictGetBool(dict, "model visible", true);
                o.trackingSource = DictGetString(dict, "override tracking serial", "");
                o.hasRole = ParseRole(DictGetString(dict, "override role", "pass"), o.role);
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