#include "inputoverride.h"
#include "skeletaloverride.h"
#include "controllerdata.h"
#include "settings.h"
#include "hooking.h"

#include <algorithm>
#include <atomic>
#include <cstring>
#include <mutex>
#include <unordered_map>
#include <vector>

namespace glassvr {
    namespace hooks {

        const char* const kInputControlNames[kInputControlCount] = {
            "trigger", "grip", "joystick", "trackpad",
            "a", "b",
            "y_up", "a_down", "x_left", "b_right",
            "select", "bumper", "system",
        };
        const char* const kInputChannelNames[kInputChannelCount] = { "click", "touch", "value", "force", "x", "y" };

        namespace {
            constexpr unsigned Bit(int channel) { return 1u << channel; }
            constexpr unsigned kButton = Bit(kChClick) | Bit(kChTouch);

            const unsigned kChannelMask[kInputControlCount] = {
                kButton | Bit(kChValue),                                  // trigger
                kButton | Bit(kChValue) | Bit(kChForce),                  // grip
                kButton | Bit(kChX) | Bit(kChY),                          // joystick
                kButton | Bit(kChX) | Bit(kChY) | Bit(kChForce),          // trackpad
                kButton, kButton,                                         // a b
                kButton, kButton, kButton, kButton,                       // y_up a_down x_left b_right
                kButton, kButton, kButton,                                // select bumper system
            };

            constexpr bool IsBooleanChannel(int channel) { return channel == kChClick || channel == kChTouch; }
        }

        bool InputChannelValid(int control, int channel) {
            if (control < 0 || control >= kInputControlCount) return false;
            if (channel < 0 || channel >= kInputChannelCount) return false;
            return (kChannelMask[control] & Bit(channel)) != 0;
        }

        std::string InputOverrideKey(int control, int channel) {
            return std::string("input ") + kInputControlNames[control] + " " + kInputChannelNames[channel] + " override";
        }

        namespace {
            enum SourceType : int { kSrcNone = 0, kSrcIndex, kSrcFrame, kSrcVive, kSrcTouch };
            enum TargetClass : int { kClsNone = 0, kClsDpad, kClsAbxy };

            struct SourceData {
                SourceType       type = kSrcNone;
                bool             right = false;
                PacketInputIndex idx{};
                PacketInputFrame ifm{};
                PacketInputVive  ive{};
                PacketInputTouch itc{};
            };

            bool Bool(float& out, bool v) { out = v ? 1.0f : 0.0f; return true; }
            bool Num(float& out, double v) { out = (float)v; return true; }

            bool ReadIndex(const PacketInputIndex& p, int slot, float& out) {
                switch (slot) {
                case InputSlot(kCtlTrigger, kChClick):  return Bool(out, p.trigger_btn);
                case InputSlot(kCtlTrigger, kChTouch):  return Bool(out, p.trigger_cap);
                case InputSlot(kCtlTrigger, kChValue):  return Num(out, p.trigger);
                case InputSlot(kCtlGrip, kChTouch):     return Bool(out, p.grip_cap);
                case InputSlot(kCtlGrip, kChValue):     return Num(out, p.grip_pull);
                case InputSlot(kCtlGrip, kChForce):     return Num(out, p.grip_force);
                case InputSlot(kCtlJoystick, kChClick): return Bool(out, p.joy_btn);
                case InputSlot(kCtlJoystick, kChTouch): return Bool(out, p.joy_cap);
                case InputSlot(kCtlJoystick, kChX):     return Num(out, p.joy_x);
                case InputSlot(kCtlJoystick, kChY):     return Num(out, p.joy_y);
                case InputSlot(kCtlTrackpad, kChTouch): return Bool(out, p.touch_cap);
                case InputSlot(kCtlTrackpad, kChX):     return Num(out, p.touch_x);
                case InputSlot(kCtlTrackpad, kChY):     return Num(out, p.touch_y);
                case InputSlot(kCtlTrackpad, kChForce): return Num(out, p.touch_force);
                case InputSlot(kCtlA, kChClick):        return Bool(out, p.a);
                case InputSlot(kCtlA, kChTouch):        return Bool(out, p.a_cap);
                case InputSlot(kCtlB, kChClick):        return Bool(out, p.b);
                case InputSlot(kCtlB, kChTouch):        return Bool(out, p.b_cap);
                case InputSlot(kCtlSystem, kChClick):   return Bool(out, p.system);
                case InputSlot(kCtlSystem, kChTouch):   return Bool(out, p.system_cap);
                }
                return false;
            }

            bool ReadFrame(const PacketInputFrame& p, bool right, int targetClass, int slot, float& out) {
                const bool cluster = (targetClass == (right ? kClsAbxy : kClsDpad));
                switch (slot) {
                case InputSlot(kCtlTrigger, kChClick):  return Bool(out, p.trigger_btn);
                case InputSlot(kCtlTrigger, kChTouch):  return Bool(out, p.trigger_cap);
                case InputSlot(kCtlTrigger, kChValue):  return Num(out, p.trigger);
                case InputSlot(kCtlGrip, kChClick):     return Bool(out, p.grip_btn);
                case InputSlot(kCtlGrip, kChTouch):     return Bool(out, p.grip_cap);
                case InputSlot(kCtlGrip, kChValue):     return Num(out, p.grip);
                case InputSlot(kCtlJoystick, kChClick): return Bool(out, p.joy_btn);
                case InputSlot(kCtlJoystick, kChTouch): return Bool(out, p.joy_cap);
                case InputSlot(kCtlJoystick, kChX):     return Num(out, p.joy_x);
                case InputSlot(kCtlJoystick, kChY):     return Num(out, p.joy_y);
                case InputSlot(kCtlYUp, kChClick):      return cluster && Bool(out, p.y_up);
                case InputSlot(kCtlYUp, kChTouch):      return cluster && Bool(out, p.y_up_cap);
                case InputSlot(kCtlADown, kChClick):    return cluster && Bool(out, p.a_down);
                case InputSlot(kCtlADown, kChTouch):    return cluster && Bool(out, p.a_down_cap);
                case InputSlot(kCtlXLeft, kChClick):    return cluster && Bool(out, p.x_left);
                case InputSlot(kCtlXLeft, kChTouch):    return cluster && Bool(out, p.x_left_cap);
                case InputSlot(kCtlBRight, kChClick):   return cluster && Bool(out, p.b_right);
                case InputSlot(kCtlBRight, kChTouch):   return cluster && Bool(out, p.b_right_cap);
                case InputSlot(kCtlSelect, kChClick):   return Bool(out, p.select);
                case InputSlot(kCtlSelect, kChTouch):   return Bool(out, p.select_cap);
                case InputSlot(kCtlBumper, kChClick):   return Bool(out, p.bumper);
                case InputSlot(kCtlBumper, kChTouch):   return Bool(out, p.bumper_cap);
                case InputSlot(kCtlSystem, kChClick):   return Bool(out, p.system);
                case InputSlot(kCtlSystem, kChTouch):   return Bool(out, p.system_cap);
                }
                return false;
            }

            bool ReadVive(const PacketInputVive& p, int slot, float& out) {
                switch (slot) {
                case InputSlot(kCtlTrigger, kChClick):  return Bool(out, p.trigger_btn);
                case InputSlot(kCtlTrigger, kChValue):  return Num(out, p.trigger);
                case InputSlot(kCtlGrip, kChClick):     return Bool(out, p.grip_btn);
                case InputSlot(kCtlTrackpad, kChClick): return Bool(out, p.touch_btn);
                case InputSlot(kCtlTrackpad, kChTouch): return Bool(out, p.touch_cap);
                case InputSlot(kCtlTrackpad, kChX):     return Num(out, p.touch_x);
                case InputSlot(kCtlTrackpad, kChY):     return Num(out, p.touch_y);
                case InputSlot(kCtlSelect, kChClick):   return Bool(out, p.select);
                case InputSlot(kCtlSystem, kChClick):   return Bool(out, p.system);
                }
                return false;
            }

            bool ReadTouch(const PacketInputTouch& p, bool right, int slot, float& out) {
                switch (slot) {
                case InputSlot(kCtlTrigger, kChTouch):  return Bool(out, p.trigger_cap);
                case InputSlot(kCtlTrigger, kChValue):  return Num(out, p.trigger);
                case InputSlot(kCtlGrip, kChValue):     return Num(out, p.grip);
                case InputSlot(kCtlJoystick, kChClick): return Bool(out, p.joy_btn);
                case InputSlot(kCtlJoystick, kChTouch): return Bool(out, p.joy_cap);
                case InputSlot(kCtlJoystick, kChX):     return Num(out, p.joy_x);
                case InputSlot(kCtlJoystick, kChY):     return Num(out, p.joy_y);
                case InputSlot(kCtlA, kChClick):        return Bool(out, p.a_x);
                case InputSlot(kCtlA, kChTouch):        return Bool(out, p.a_x_cap);
                case InputSlot(kCtlB, kChClick):        return Bool(out, p.b_y);
                case InputSlot(kCtlB, kChTouch):        return Bool(out, p.b_y_cap);
                case InputSlot(kCtlSystem, kChClick):   return Bool(out, p.system);
                case InputSlot(kCtlSelect, kChClick):   return !right && Bool(out, p.system);
                }
                return false;
            }

            bool ReadSource(const SourceData& s, int control, int channel, int targetClass, float& out) {
                const int slot = InputSlot(control, channel);
                switch (s.type) {
                case kSrcIndex: return ReadIndex(s.idx, slot, out);
                case kSrcFrame: return ReadFrame(s.ifm, s.right, targetClass, slot, out);
                case kSrcVive:  return ReadVive(s.ive, slot, out);
                case kSrcTouch: return ReadTouch(s.itc, s.right, slot, out);
                default:        return false;
                }
            }

            void FetchSource(SourceData& s, SourceType type, bool right, const std::string& mode) {
                ControllerDataHub& hub = ControllerDataHub::Get();
                s.type = type;
                s.right = right;
                switch (type) {
                case kSrcIndex: s.idx = hub.GetInputIndex(right, mode); break;
                case kSrcFrame: s.ifm = hub.GetInputFrame(right, mode); break;
                case kSrcVive:  s.ive = hub.GetInputVive(right, mode); break;
                case kSrcTouch: s.itc = hub.GetInputTouch(right, mode); break;
                default: break;
                }
            }

            struct Cand { int control; int channel; int targetClass; };
            struct Resolved {
                Cand cands[3];
                int  count = 0;
            };

            Resolved ResolvePath(const std::string& path, bool deviceHasA) {
                Resolved r;
                static const char kPrefix[] = "/input/";
                const size_t prefixLen = sizeof(kPrefix) - 1;
                if (path.compare(0, prefixLen, kPrefix) != 0) return r;

                const size_t slash = path.find('/', prefixLen);
                if (slash == std::string::npos) return r;

                const std::string name = path.substr(prefixLen, slash - prefixLen);
                const std::string comp = path.substr(slash + 1);

                int channel = -1;
                for (int i = 0; i < kInputChannelCount; i++)
                    if (comp == kInputChannelNames[i]) channel = i;
                if (channel < 0) return r;

                auto add = [&](int control, int cls = kClsNone) {
                    if (r.count < 3 && InputChannelValid(control, channel))
                        r.cands[r.count++] = { control, channel, cls };
                    };

                if (name == "trigger")                         add(kCtlTrigger);
                else if (name == "grip")                       add(kCtlGrip);
                else if (name == "thumbstick" || name == "joystick") add(kCtlJoystick);
                else if (name == "trackpad")                   add(kCtlTrackpad);
                else if (name == "bumper")                     add(kCtlBumper);
                else if (name == "system")                     add(kCtlSystem);
                else if (name == "menu" || name == "view" || name == "application_menu") add(kCtlSelect);
                else if (name == "dpad_up")                    add(kCtlYUp, kClsDpad);
                else if (name == "dpad_down")                  add(kCtlADown, kClsDpad);
                else if (name == "dpad_left")                  add(kCtlXLeft, kClsDpad);
                else if (name == "dpad_right")                 add(kCtlBRight, kClsDpad);
                else if (name == "a") { add(kCtlA);  add(kCtlADown, kClsAbxy); }
                else if (name == "b") { add(kCtlB);  add(kCtlBRight, kClsAbxy); }
                else if (name == "x") {
                    if (!deviceHasA) add(kCtlA);
                    add(kCtlXLeft, kClsAbxy);
                }
                else if (name == "y") {
                    if (!deviceHasA) add(kCtlB);
                    add(kCtlYUp, kClsAbxy);
                }
                return r;
            }

            struct Component {
                vr::PropertyContainerHandle_t container = vr::k_ulInvalidPropertyContainer;
                bool        scalar = false;
                std::string path;
                std::string serial;
                Resolved    resolved;
                uint32_t    resolvedVersion = 0xFFFFFFFFu;
            };

            struct DeviceInfo {
                bool     hasA = false;
                uint32_t version = 0;
            };

            std::mutex                                                    g_mutex;
            std::unordered_map<std::string, InputOverride>                g_rules;
            std::unordered_map<vr::VRInputComponentHandle_t, Component>   g_components;
            std::unordered_map<vr::PropertyContainerHandle_t, DeviceInfo> g_devices;

            std::atomic<bool> g_anyRules{ false };
            std::atomic<int>  g_sourceType{ kSrcNone };
            std::string       g_modes[2] = { "pipe", "pipe" };

            void RefreshAnyRules_Locked() { g_anyRules.store(!g_rules.empty(), std::memory_order_relaxed); }

            SourceType ParseSourceType(std::string text) {
                std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return (char)std::tolower(c); });
                if (text == "index") return kSrcIndex;
                if (text == "frame") return kSrcFrame;
                if (text == "vive")  return kSrcVive;
                if (text == "touch") return kSrcTouch;
                return kSrcNone;
            }

            // "ring and pinky affect grip": curl below this is noise, not fingers on the grip
            constexpr float kGripTouchThreshold = 0.05f;
            constexpr float kGripClickThreshold = 0.95f;

            bool Override(vr::VRInputComponentHandle_t handle, bool scalarCall, float& value) {
                if (!g_anyRules.load(std::memory_order_relaxed)) return false;

                std::lock_guard<std::mutex> lock(g_mutex);

                auto it = g_components.find(handle);
                if (it == g_components.end()) return false;
                Component& c = it->second;
                if (c.scalar != scalarCall) return false;

                if (c.serial.empty()) {
                    c.serial = ResolveContainerSerial(c.container);
                    if (c.serial.empty()) return false;
                }

                auto rule = g_rules.find(c.serial);
                if (rule == g_rules.end()) return false;

                const DeviceInfo& dev = g_devices[c.container];
                if (c.resolvedVersion != dev.version) {
                    c.resolved = ResolvePath(c.path, dev.hasA);
                    c.resolvedVersion = dev.version;
                }

                bool changed = false;

                if (!rule->second.source.empty()) {
                    bool anyTicked = false;
                    for (int i = 0; i < c.resolved.count; i++) {
                        if (rule->second.enabled[InputSlot(c.resolved.cands[i].control, c.resolved.cands[i].channel)]) {
                            anyTicked = true;
                            break;
                        }
                    }

                    const SourceType type = (SourceType)g_sourceType.load(std::memory_order_relaxed);
                    if (anyTicked && type != kSrcNone) {
                        const bool right = (rule->second.source == "cr");
                        const std::string mode = g_modes[right ? 1 : 0];

                        SourceData src;
                        FetchSource(src, type, right, mode);

                        for (int i = 0; i < c.resolved.count; i++) {
                            const Cand& cand = c.resolved.cands[i];
                            if (!rule->second.enabled[InputSlot(cand.control, cand.channel)]) continue;
                            if (IsBooleanChannel(cand.channel) == scalarCall) continue;

                            float v;
                            if (!ReadSource(src, cand.control, cand.channel, cand.targetClass, v)) continue;

                            value = v;
                            changed = true;
                            break;
                        }
                    }
                }

                // ---- 2. ring and pinky affect grip ----
                // grip = highest of [hardware (value as it is now), ring, pinky]. ring / pinky come from the final
                // skeleton SteamVR gets for this device, not from the source packet. Never lowers the hardware value.
                if (rule->second.ringPinkyGrip) {
                    float ring = 0.0f, pinky = 0.0f;
                    if (GetFinalRingPinkyCurl(c.container, ring, pinky)) {
                        const float fingers = (ring > pinky) ? ring : pinky;

                        for (int i = 0; i < c.resolved.count; i++) {
                            const Cand& cand = c.resolved.cands[i];
                            if (cand.control != kCtlGrip) continue;
                            if (IsBooleanChannel(cand.channel) == scalarCall) continue;

                            if (cand.channel == kChValue) {
                                if (fingers > value) { value = fingers; changed = true; }
                            }
                            else if (cand.channel == kChTouch) {
                                if (value < 0.5f && fingers > kGripTouchThreshold) { value = 1.0f; changed = true; }
                            }
                            else if (cand.channel == kChClick) {
                                if (value < 0.5f && fingers > kGripClickThreshold) { value = 1.0f; changed = true; }
                            }
                            break;
                        }
                    }
                }

                return changed;
            }
        }

        void SetInputOverride(const std::string& serial, const InputOverride& rule) {
            if (!rule.active()) {
                ClearInputOverride(serial);
                return;
            }
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_rules[serial] = rule;
                RefreshAnyRules_Locked();
            }
            SetFingerGripTracking(serial, rule.ringPinkyGrip);
            HookLog("[input] '%s' <- %s: %d channels, ring/pinky grip=%d", serial.c_str(), rule.source.c_str(),
                (int)rule.enabled.count(), (int)rule.ringPinkyGrip);
        }

        void ClearInputOverride(const std::string& serial) {
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                if (g_rules.erase(serial)) HookLog("[input] '%s' reverted", serial.c_str());
                RefreshAnyRules_Locked();
            }
            SetFingerGripTracking(serial, false);
        }

        void ClearAllInputOverrides() {
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_rules.clear();
                RefreshAnyRules_Locked();
            }
            ClearAllFingerGripTracking();
        }

        void ForgetInputComponents() {
            std::lock_guard<std::mutex> lock(g_mutex);
            g_components.clear();
            g_devices.clear();
        }

        void TickInputOverrides() {
            bool used[2] = { false, false };
            std::string modes[2] = { "pipe", "pipe" };

            {
                std::lock_guard<std::mutex> lock(g_mutex);
                for (const auto& kv : g_rules) {
                    if (kv.second.source == "cl") {
                        used[0] = true;
                        modes[0] = GetStringFromSettingsByKey("cl input mode");
                    }
                    else if (kv.second.source == "cr") {
                        used[1] = true;
                        modes[1] = GetStringFromSettingsByKey("cr input mode");
                    }
                }
            }

            if (!used[0] && !used[1]) return;

            const SourceType type = ParseSourceType(GetStringFromSettingsByKey("con type"));
            if (g_sourceType.exchange(type) != type && type == kSrcNone)
                HookLog("[input] unknown \"con type\", input overrides are paused");

            for (int i = 0; i < 2; i++) {
                if (!used[i]) continue;
                const bool right = (i == 1);
                const std::string device = right ? "cr" : "cl";

                ControllerDataHub::Get().Ensure(right);

                if (modes[i] == "serial" || modes[i] == "bluetooth") {
                    ControllerDataHub::Get().UpdateSerialPort(device, "input");
                }

                std::lock_guard<std::mutex> lock(g_mutex);
                g_modes[i] = modes[i];
            }
        }

        void OnInputComponentCreated(vr::VRInputComponentHandle_t handle,
            vr::PropertyContainerHandle_t container,
            const char* path, bool scalar) {
            if (!path || std::strncmp(path, "/input/", 7) != 0) return;

            Component c;
            c.container = container;
            c.scalar = scalar;
            c.path = path;

            std::lock_guard<std::mutex> lock(g_mutex);
            DeviceInfo& dev = g_devices[container];
            if (std::strncmp(path, "/input/a/", 9) == 0) dev.hasA = true;
            dev.version++;
            g_components[handle] = c;
        }

        bool OverrideBooleanInput(vr::VRInputComponentHandle_t handle, bool& value) {
            float v = value ? 1.0f : 0.0f;
            if (!Override(handle, false, v)) return false;
            value = v > 0.5f;
            return true;
        }

        bool OverrideScalarInput(vr::VRInputComponentHandle_t handle, float& value) {
            return Override(handle, true, value);
        }

    }
}