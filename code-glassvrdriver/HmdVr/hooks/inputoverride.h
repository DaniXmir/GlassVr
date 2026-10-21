#pragma once

#include "hookcommon.h"

#include <bitset>
#include <string>

namespace glassvr {
    namespace hooks {

        enum InputControl : int {
            kCtlTrigger, kCtlGrip, kCtlJoystick, kCtlTrackpad,
            kCtlA, kCtlB,
            kCtlYUp, kCtlADown, kCtlXLeft, kCtlBRight,
            kCtlSelect,
            kCtlBumper, kCtlSystem,
            kInputControlCount
        };

        enum InputChannel : int {
            kChClick, kChTouch,                         // boolean
            kChValue, kChForce, kChX, kChY,             // scalar
            kInputChannelCount
        };

        constexpr int kInputSlotCount = kInputControlCount * kInputChannelCount;
        constexpr int InputSlot(int control, int channel) { return control * kInputChannelCount + channel; }

        extern const char* const kInputControlNames[kInputControlCount];
        extern const char* const kInputChannelNames[kInputChannelCount];

        bool InputChannelValid(int control, int channel);

        std::string InputOverrideKey(int control, int channel);

        struct InputOverride {
            std::string                     source;    // "cl" / "cr", empty = pass
            std::bitset<kInputSlotCount>    enabled;   // by InputSlot()

            // "ring and pinky affect grip": grip = max(device's own grip, ring curl, pinky curl), the curls are read
            // from the FINAL skeleton SteamVR gets for this device (after skeletal overrides).
            // Independent of source / enabled.
            bool                            ringPinkyGrip = false;

            bool active() const { return (!source.empty() && enabled.any()) || ringPinkyGrip; }
            bool operator==(const InputOverride& o) const {
                return source == o.source && enabled == o.enabled && ringPinkyGrip == o.ringPinkyGrip;
            }
        };

        void SetInputOverride(const std::string& serial, const InputOverride& rule);
        void ClearInputOverride(const std::string& serial);
        void ClearAllInputOverrides();
        void ForgetInputComponents();

        void TickInputOverrides();

        void OnInputComponentCreated(vr::VRInputComponentHandle_t handle,
            vr::PropertyContainerHandle_t container,
            const char* path, bool scalar);

        bool OverrideBooleanInput(vr::VRInputComponentHandle_t handle, bool& value);
        bool OverrideScalarInput(vr::VRInputComponentHandle_t handle, float& value);

    }
}