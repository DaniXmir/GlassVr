#include "controllerregistry.h"
#include "controllerbase.h"

#include "indexcontroller.h"
#include "framecontroller.h"
#include "vivecontroller.h"
#include "touchcontroller.h"

#include <algorithm>
#include <cctype>

namespace {

struct Entry {
    const char* id;                      // value of "con type" in settings.json
    ControllerBase* (*create)(bool right);
};

const Entry kEntries[] = {
    { "index", [](bool right) -> ControllerBase* { return new CSampleControllerDriver(right); } },
    { "frame", [](bool right) -> ControllerBase* { return new CFrameControllerDriver(right); } },
    { "vive",  [](bool right) -> ControllerBase* { return new CViveControllerDriver(right); } },
    { "touch", [](bool right) -> ControllerBase* { return new CTouchControllerDriver(right); } },
};

const Entry* Find(const std::string& type)
{
    for (const Entry& e : kEntries) {
        if (type == e.id) return &e;
    }
    return nullptr;
}

}

const char* ControllerRegistry::DefaultType()
{
    return "index";
}

std::string ControllerRegistry::Normalize(const std::string& raw)
{
    std::string s = raw;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) { return (char)std::tolower(ch); });
    if (s.empty()) return DefaultType();
    return s;
}

bool ControllerRegistry::IsKnown(const std::string& type)
{
    return Find(type) != nullptr;
}

ControllerBase* ControllerRegistry::Create(const std::string& type, bool right)
{
    const Entry* e = Find(type);
    return e ? e->create(right) : nullptr;
}
