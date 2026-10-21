#pragma once
// Maps the "con type" setting value to a controller class.
// Adding vive / touch later = new class + ONE line in controllerregistry.cpp.

#include <string>

class ControllerBase;

namespace ControllerRegistry
{
    // type used when "con type" is empty
    const char* DefaultType();

    // lower-cases, trims, empty -> DefaultType()
    std::string Normalize(const std::string& raw);

    bool IsKnown(const std::string& type);

    // returns a new controller or nullptr for an unknown type; caller owns it
    ControllerBase* Create(const std::string& type, bool right);
}
