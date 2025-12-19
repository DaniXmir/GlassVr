//#pragma once
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include "csampledevicedriver.h"
//#include "basics.h"
//
//#include <math.h>
//#include <winsock2.h>
//#include <ws2tcpip.h>
//#include <windows.h>
//#include <string>
//#include <fstream>
//#include <limits>
//#include <sstream>
//// ... include other necessary headers here
//
//#pragma comment(lib, "ws2_32.lib")
//
//#ifndef M_PI
//#define M_PI 3.14159265358979323846
//#endif
//
//using namespace vr;
//
//// ------------------------------------------------------------------
//// Declarations (Signatures and External Global Variables)
//// ------------------------------------------------------------------
//
//// External declarations for constant strings defined in settings.cpp
//// This tells the compiler that these exist, but they are defined in another file.
//extern const std::string SettingsFileName;
//extern const std::string AppFolderName;
//
//// Global cache for settings content: Needs 'extern' to avoid multiple definitions
//extern std::string g_settingsContent;
//
//// Function Declarations (Signatures only - bodies must be in settings.cpp)
//std::string GetFullSettingsPath();
//std::string trim_value(const std::string& str);
//const std::string& GetSettings();
//std::string GetValueStringFromContent_JSONLike(const std::string& key);
//std::string GetStringFromSettingsByKey(const std::string& key);
//int GetIntFromSettingsByKey(const std::string& key);
//float GetFloatFromSettingsByKey(const std::string& key);
//bool GetBoolFromSettingsByKey(const std::string& key);




#pragma once

#include <string>
#include <limits>

// Global Constants (Defined in settings.cpp)
extern const std::string SettingsFileName;
extern const std::string AppFolderName;

// Global cache for settings content (Defined in settings.cpp)
extern std::string g_settingsContent;

// Function Declarations (Definitions must be in settings.cpp)
std::string GetFullSettingsPath();
std::string trim_value(const std::string& str);
const std::string& GetSettings();
std::string GetValueStringFromContent_JSONLike(const std::string& key);

// Public API Declarations
std::string GetStringFromSettingsByKey(const std::string& key);
int GetIntFromSettingsByKey(const std::string& key);
float GetFloatFromSettingsByKey(const std::string& key);
bool GetBoolFromSettingsByKey(const std::string& key);