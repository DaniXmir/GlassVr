#pragma once

#include "openvr_driver.h"
#include <string>
#include <vector>

namespace controllerinput
{
    typedef std::vector<vr::VRInputComponentHandle_t> Handles;

    inline void AddBool(vr::PropertyContainerHandle_t c, const std::string& path, Handles& out)
    {
        vr::VRInputComponentHandle_t h = vr::k_ulInvalidInputComponentHandle;
        vr::VRDriverInput()->CreateBooleanComponent(c, path.c_str(), &h);
        out.push_back(h);
    }

    inline void AddClick(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out) { AddBool(c, source + "/click", out); }
    inline void AddTouch(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out) { AddBool(c, source + "/touch", out); }

    inline void AddButton(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out)
    {
        AddClick(c, source, out);
        AddTouch(c, source, out);
    }

    inline void AddValue(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out)
    {
        vr::VRInputComponentHandle_t h = vr::k_ulInvalidInputComponentHandle;
        vr::VRDriverInput()->CreateScalarComponent(c, (source + "/value").c_str(), &h,
            vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedOneSided);
        out.push_back(h);
    }

    inline void AddXY(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out)
    {
        for (const char* axis : { "/x", "/y" }) {
            vr::VRInputComponentHandle_t h = vr::k_ulInvalidInputComponentHandle;
            vr::VRDriverInput()->CreateScalarComponent(c, (source + axis).c_str(), &h,
                vr::VRScalarType_Absolute, vr::VRScalarUnits_NormalizedTwoSided);
            out.push_back(h);
        }
    }

    inline void AddTriggerLike(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out)
    {
        AddButton(c, source, out);
        AddValue(c, source, out);
    }

    inline void AddThumbstick(vr::PropertyContainerHandle_t c, const std::string& source, Handles& out)
    {
        AddButton(c, source, out);
        AddXY(c, source, out);
    }
}
