#pragma once

#include <openvr_driver.h>

#include <string>

namespace glassvr {
    namespace hooks {
        std::string ResolveContainerSerial(vr::PropertyContainerHandle_t container);
        inline const char* HandKey(bool right) { return right ? "cr" : "cl"; }
    }
}