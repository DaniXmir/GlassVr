//#pragma once
//
//#define WIN32_LEAN_AND_MEAN
//#define NOMINMAX
//
//#include "csampledevicedriver.h"
//
//#include "basics.h"
//#include <math.h>
//
//#include <winsock2.h>
//#include <ws2tcpip.h>
//#pragma comment(lib, "ws2_32.lib")
//
//#include <windows.h>
//
//#include <string>
//#include <iostream>
//#include <algorithm>
//#include <fstream>
//#include <limits>
//#include <stdexcept>
//#include <cctype>
//#include <cmath>
//#include <cstring>
//#include <cstdlib>
//#include <cstdio>
//#include <sstream>
//
//#ifndef M_PI
//#define M_PI 3.14159265358979323846
//#endif
//
//using namespace vr;
//
//const std::string SettingsFileName = "settings.json";
//const std::string AppFolderName = "glassvr";
//
//static std::string g_settingsContent;
//
//
//std::string GetFullSettingsPath() {
//    char* appDataPath = nullptr;
//    size_t len;
//    std::string fullPath;
//
//    if (_dupenv_s(&appDataPath, &len, "APPDATA") == 0 && appDataPath != nullptr) {
//
//        fullPath = std::string(appDataPath) + "\\" + AppFolderName + "\\" + SettingsFileName;
//
//        free(appDataPath);
//
//    }
//    else {
//        fullPath = SettingsFileName;
//    }
//
//    return fullPath;
//}
//
//std::string trim_value(const std::string& str) {
//    size_t start = str.find_first_not_of(" \t\n\r\"");
//    if (std::string::npos == start) {
//        return "";
//    }
//    size_t end = str.find_last_not_of(" \t\n\r\"");
//
//    return str.substr(start, (end - start + 1));
//}
//
//const std::string& GetSettings() {
//    if (!g_settingsContent.empty()) {
//        return g_settingsContent;
//    }
//
//    const std::string FullSettingsPath = GetFullSettingsPath();
//    if (FullSettingsPath.empty()) {
//        g_settingsContent = "";
//        return g_settingsContent;
//    }
//
//    std::ifstream file(FullSettingsPath);
//
//    if (file.is_open()) {
//        g_settingsContent.assign(
//            (std::istreambuf_iterator<char>(file)),
//            (std::istreambuf_iterator<char>())
//        );
//        file.close();
//    }
//    else {
//        g_settingsContent = "";
//    }
//
//    return g_settingsContent;
//}
//
//std::string GetValueStringFromContent_JSONLike(const std::string& key) {
//    const std::string& content = GetSettings();
//    if (content.empty()) {
//        return "";
//    }
//
//    std::string searchKey = "\"" + key + "\"";
//
//    size_t keyPos = content.find(searchKey);
//    if (keyPos == std::string::npos) {
//        return "";
//    }
//
//    size_t colonPos = content.find(':', keyPos + searchKey.length());
//    if (colonPos == std::string::npos) {
//        return "";
//    }
//
//    size_t valueStartPos = content.find_first_not_of(" \t\n\r", colonPos + 1);
//    if (valueStartPos == std::string::npos) {
//        return "";
//    }
//
//    size_t commaPos = content.find(',', valueStartPos);
//    size_t bracePos = content.find('}', valueStartPos);
//
//    size_t terminatorPos = std::min(commaPos, bracePos);
//
//    if (terminatorPos == std::string::npos) {
//        terminatorPos = content.length();
//    }
//
//    std::string rawValue = content.substr(valueStartPos, terminatorPos - valueStartPos);
//
//    return trim_value(rawValue);
//}
//
//std::string GetStringFromSettingsByKey(const std::string& key) {
//    std::string result = GetValueStringFromContent_JSONLike(key);
//    if (result.empty()) {
//    }
//    return result;
//}
//
//int GetIntFromSettingsByKey(const std::string& key) {
//    std::string valueStr = GetValueStringFromContent_JSONLike(key);
//    if (valueStr.empty()) {
//        return 0;
//    }
//
//    std::stringstream ss(valueStr);
//    int value;
//
//    if (!(ss >> value)) {
//        return 0;
//    }
//
//    char remaining;
//    if (ss >> remaining) {
//        return 0;
//    }
//
//    return value;
//}
//
//float GetFloatFromSettingsByKey(const std::string& key) {
//    std::string valueStr = GetValueStringFromContent_JSONLike(key);
//    if (valueStr.empty()) {
//        return std::numeric_limits<float>::quiet_NaN();
//    }
//
//    std::stringstream ss(valueStr);
//    float value;
//
//    if (!(ss >> value)) {
//        return std::numeric_limits<float>::quiet_NaN();
//    }
//
//    char remaining;
//    if (ss >> remaining) {
//        return std::numeric_limits<float>::quiet_NaN();
//    }
//
//    return value;
//}
//
//bool GetBoolFromSettingsByKey(const std::string& key) {
//    std::string normalizedContent = GetValueStringFromContent_JSONLike(key);
//
//    std::transform(normalizedContent.begin(), normalizedContent.end(), normalizedContent.begin(), ::tolower);
//
//    if (normalizedContent == "true" || normalizedContent == "1") {
//        return true;
//    }
//    else {
//        return false;
//    }
//}









































#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include "csampledevicedriver.h"

#include "basics.h"
#include <math.h>

#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

#include <windows.h>

#include <string>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;

const std::string SettingsFileName = "settings.json";
const std::string AppFolderName = "glassvr";

std::string g_settingsContent;


std::string GetFullSettingsPath() {
    char* appDataPath = nullptr;
    size_t len;
    std::string fullPath;

    if (_dupenv_s(&appDataPath, &len, "APPDATA") == 0 && appDataPath != nullptr) {

        fullPath = std::string(appDataPath) + "\\" + AppFolderName + "\\" + SettingsFileName;

        free(appDataPath);

    }
    else {
        fullPath = SettingsFileName;
    }

    return fullPath;
}

std::string trim_value(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r\"");
    if (std::string::npos == start) {
        return "";
    }
    size_t end = str.find_last_not_of(" \t\n\r\"");

    return str.substr(start, (end - start + 1));
}

//const std::string& GetSettings() {
//    if (!g_settingsContent.empty()) {
//        return g_settingsContent;
//    }
//
//    const std::string FullSettingsPath = GetFullSettingsPath();
//    if (FullSettingsPath.empty()) {
//        g_settingsContent = "";
//        return g_settingsContent;
//    }
//
//    std::ifstream file(FullSettingsPath);
//
//    if (file.is_open()) {
//        g_settingsContent.assign(
//            (std::istreambuf_iterator<char>(file)),
//            (std::istreambuf_iterator<char>())
//        );
//        file.close();
//    }
//    else {
//        g_settingsContent = "";
//    }
//
//    return g_settingsContent;
//}

#include <chrono>

std::chrono::steady_clock::time_point g_lastLoadTime;
const int REFRESH_INTERVAL_MS = 1;//2000; // Check for updates every 2 seconds

const std::string& GetSettings() {
    auto currentTime = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - g_lastLoadTime).count();

    // If interval has passed, clear cache to force a reload
    if (duration > REFRESH_INTERVAL_MS) {
        g_settingsContent = "";
        g_lastLoadTime = currentTime;
    }

    if (!g_settingsContent.empty()) {
        return g_settingsContent;
    }

    const std::string FullSettingsPath = GetFullSettingsPath();
    std::ifstream file(FullSettingsPath);

    if (file.is_open()) {
        g_settingsContent.assign(
            (std::istreambuf_iterator<char>(file)),
            (std::istreambuf_iterator<char>())
        );
        file.close();
    }
    return g_settingsContent;
}

std::string GetValueStringFromContent_JSONLike(const std::string& key) {
    const std::string& content = GetSettings();
    if (content.empty()) return "";

    std::string searchKey = "\"" + key + "\"";
    size_t keyPos = content.find(searchKey);
    if (keyPos == std::string::npos) return ""; // Key not found

    size_t colonPos = content.find(':', keyPos + searchKey.length());
    if (colonPos == std::string::npos) return "";

    size_t valueStartPos = content.find_first_not_of(" \t\n\r", colonPos + 1);
    if (valueStartPos == std::string::npos) return "";

    size_t commaPos = content.find(',', valueStartPos);
    size_t bracePos = content.find('}', valueStartPos);
    size_t terminatorPos = std::min(commaPos, bracePos);

    if (terminatorPos == std::string::npos) {
        terminatorPos = content.length();
    }

    std::string rawValue = content.substr(valueStartPos, terminatorPos - valueStartPos);
    return trim_value(rawValue);
}

std::string GetStringFromSettingsByKey(const std::string& key) {
    return GetValueStringFromContent_JSONLike(key);
}

int GetIntFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) return 0; // Default fallback

    try {
        return std::stoi(valueStr);
    }
    catch (...) {
        return 0;
    }
}

float GetFloatFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) return 0.0f; // Default fallback for missing offsets

    try {
        return std::stof(valueStr);
    }
    catch (...) {
        // If it's not a standard float, check for scientific notation or return 0
        std::stringstream ss(valueStr);
        float value;
        if (ss >> value) return value;
        return 0.0f;
    }
}

bool GetBoolFromSettingsByKey(const std::string& key) {
    std::string val = GetValueStringFromContent_JSONLike(key);
    if (val.empty()) return false; // Default fallback

    std::transform(val.begin(), val.end(), val.begin(), ::tolower);
    return (val == "true" || val == "1");
}