//#pragma once
//
//#include <iostream>        // For std::cout, std::cerr, std::endl
//#include <string>          // For std::string, std::stoi, std::stof
//#include <fstream>         // For std::ifstream (file input stream)
//#include <algorithm>       // For std::min and std::transform
//#include <limits>          // For std::numeric_limits
//#include <stdlib.h>        // For _dupenv_s and free (Windows-specific environment access)
//#include <cstdio>          // For size_t
//#include <streambuf>       // For std::istreambuf_iterator
//
//const std::string SettingsFileName = "settings.json";
//const std::string AppFolderName = "glassvr";
//
//// Global cache for settings content
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
//        // %APPDATA%\\glassvr\\driver settings.json
//        fullPath = std::string(appDataPath) + "\\" + AppFolderName + "\\" + SettingsFileName;
//
//        free(appDataPath);
//
//    }
//    else {
//        std::cerr << "CRITICAL ERROR: Failed to retrieve APPDATA path. Defaulting to current directory." << std::endl;
//        fullPath = SettingsFileName; // Fallback
//    }
//
//    return fullPath;
//}
//
//// Simple trim function (removes leading/trailing whitespace and quotes)
//// Essential for cleaning the value string from JSON extraction
//std::string trim_value(const std::string& str) {
//    size_t start = str.find_first_not_of(" \t\n\r\"");
//    if (std::string::npos == start) {
//        return "";
//    }
//    size_t end = str.find_last_not_of(" \t\n\r\"");
//    return str.substr(start, (end - start + 1));
//}
//
//
//// --- 1. GetSettings() ---
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
//        std::cout << "Loading settings from file: " << FullSettingsPath << std::endl;
//
//        g_settingsContent.assign(
//            (std::istreambuf_iterator<char>(file)),
//            (std::istreambuf_iterator<char>())
//        );
//        file.close();
//    }
//    else {
//        std::cerr << "Settings file not found at " << FullSettingsPath << ". Returning empty content." << std::endl;
//        g_settingsContent = "";
//    }
//
//    return g_settingsContent;
//}
//
//
//// --- Generic Value Extraction Function (Internal Helper) ---
//std::string GetValueStringFromContent_JSONLike(const std::string& key) {
//    const std::string& content = GetSettings();
//    if (content.empty()) {
//        return "";
//    }
//
//    // 1. Construct the search key: "key" (JSON standard)
//    std::string searchKey = "\"" + key + "\"";
//
//    // 2. Find the position of the key
//    size_t keyPos = content.find(searchKey);
//    if (keyPos == std::string::npos) {
//        // Key not found
//        return "";
//    }
//
//    // 3. Find the colon (':') which must follow the key
//    size_t colonPos = content.find(':', keyPos + searchKey.length());
//    if (colonPos == std::string::npos) {
//        std::cerr << "Colon separator not found after key: " << key << std::endl;
//        return "";
//    }
//
//    // 4. Find the beginning of the value (after the colon and any whitespace)
//    size_t valueStartPos = content.find_first_not_of(" \t\n\r", colonPos + 1);
//    if (valueStartPos == std::string::npos) {
//        return "";
//    }
//
//    // 5. Find the end of the value (comma ',' or closing brace '}')
//    // Note: This relies on the file being clean/unformatted JSON.
//    size_t commaPos = content.find(',', valueStartPos);
//    size_t bracePos = content.find('}', valueStartPos);
//
//    // Get the earliest valid JSON terminator
//    size_t valueEndPos = std::min(commaPos, bracePos);
//
//    if (valueEndPos == std::string::npos) {
//        valueEndPos = content.length();
//    }
//
//    // Extract the raw value string
//    std::string rawValue = content.substr(valueStartPos, valueEndPos - valueStartPos);
//
//    // Trim whitespace and quotation marks
//    return trim_value(rawValue);
//}
//
//
//// --- 2. GetStringFromSettingsByKey(const std::string& key) ---
//std::string GetStringFromSettingsByKey(const std::string& key) {
//    std::string result = GetValueStringFromContent_JSONLike(key);
//    if (result.empty()) {
//        std::cerr << "Warning: Key '" << key << "' not found or value empty in settings." << std::endl;
//    }
//    return result;
//}
//
//// --- GetIntFromSettingsByKey(const std::string& key) ---
//int GetIntFromSettingsByKey(const std::string& key) {
//    std::string valueStr = GetValueStringFromContent_JSONLike(key);
//    if (valueStr.empty()) {
//        return 0;
//    }
//
//    try {
//        return std::stoi(valueStr);
//    }
//    catch (const std::exception& e) {
//        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to int: " << e.what() << std::endl;
//        return 0;
//    }
//}
//
//// --- 3. GetFloatFromSettingsByKey(const std::string& key) ---
//float GetFloatFromSettingsByKey(const std::string& key) {
//    std::string valueStr = GetValueStringFromContent_JSONLike(key);
//    if (valueStr.empty()) {
//        return std::numeric_limits<float>::quiet_NaN();
//    }
//
//    try {
//        return std::stof(valueStr);
//    }
//    catch (const std::exception& e) {
//        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to float: " << e.what() << std::endl;
//        return std::numeric_limits<float>::quiet_NaN();
//    }
//}
//
//// --- 4. GetBoolFromSettingsByKey(const std::string& key) ---
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
#include <sstream> // Used for robust number conversion

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;

const std::string SettingsFileName = "settings.json";
const std::string AppFolderName = "glassvr";

// Global cache for settings content
static std::string g_settingsContent;

// --- Directory Creation Utility (REMOVED) ---
// bool EnsureDirectoryExists(const std::string& path) { ... }

std::string GetFullSettingsPath() {
    char* appDataPath = nullptr;
    size_t len;
    std::string fullPath;

    // Retrieve APPDATA path
    if (_dupenv_s(&appDataPath, &len, "APPDATA") == 0 && appDataPath != nullptr) {

        // %APPDATA%\\glassvr\\settings.json
        fullPath = std::string(appDataPath) + "\\" + AppFolderName + "\\" + SettingsFileName;

        free(appDataPath);

    }
    else {
        // Fallback: This is only used if APPDATA is inaccessible.
        std::cerr << "CRITICAL ERROR: Failed to retrieve APPDATA path. Defaulting to current directory." << std::endl;
        fullPath = SettingsFileName; // Fallback
    }

    return fullPath;
}

// Simple trim function (removes leading/trailing whitespace and quotes)
std::string trim_value(const std::string& str) {
    // Find the first character that is NOT whitespace or a quote
    size_t start = str.find_first_not_of(" \t\n\r\"");
    if (std::string::npos == start) {
        return ""; // Empty or only contains stripped characters
    }
    // Find the last character that is NOT whitespace or a quote
    size_t end = str.find_last_not_of(" \t\n\r\"");

    // Extract the substring
    return str.substr(start, (end - start + 1));
}


// --- 1. GetSettings() ---
const std::string& GetSettings() {
    if (!g_settingsContent.empty()) {
        return g_settingsContent;
    }

    const std::string FullSettingsPath = GetFullSettingsPath();
    if (FullSettingsPath.empty()) {
        g_settingsContent = "";
        return g_settingsContent;
    }

    std::ifstream file(FullSettingsPath);

    if (file.is_open()) {
        std::cout << "Loading settings from file: " << FullSettingsPath << std::endl;

        // Read entire file content into g_settingsContent
        g_settingsContent.assign(
            (std::istreambuf_iterator<char>(file)),
            (std::istreambuf_iterator<char>())
        );
        file.close();
    }
    else {
        // THIS IS THE MOST LIKELY FAILURE POINT. Check console output for this message.
        std::cerr << "Settings file not found at " << FullSettingsPath << ". Returning empty content." << std::endl;
        g_settingsContent = "";
    }

    return g_settingsContent;
}


// --- Generic Value Extraction Function (Internal Helper) ---
std::string GetValueStringFromContent_JSONLike(const std::string& key) {
    const std::string& content = GetSettings();
    if (content.empty()) {
        return "";
    }

    // 1. Construct the search key: "key"
    std::string searchKey = "\"" + key + "\"";

    // 2. Find the position of the key
    size_t keyPos = content.find(searchKey);
    if (keyPos == std::string::npos) {
        return "";
    }

    // 3. Find the colon (':')
    size_t colonPos = content.find(':', keyPos + searchKey.length());
    if (colonPos == std::string::npos) {
        std::cerr << "Colon separator not found after key: " << key << std::endl;
        return "";
    }

    // 4. Find the beginning of the value (after the colon and any whitespace/newline)
    size_t valueStartPos = content.find_first_not_of(" \t\n\r", colonPos + 1);
    if (valueStartPos == std::string::npos) {
        return "";
    }

    // 5. Find the end of the value (comma ',' or closing brace '}')
    size_t commaPos = content.find(',', valueStartPos);
    size_t bracePos = content.find('}', valueStartPos);

    // Get the earliest valid JSON terminator position
    size_t terminatorPos = std::min(commaPos, bracePos);

    if (terminatorPos == std::string::npos) {
        terminatorPos = content.length();
    }

    // Extract the raw value string
    std::string rawValue = content.substr(valueStartPos, terminatorPos - valueStartPos);

    // Trim whitespace and quotation marks
    return trim_value(rawValue);
}

// --- 2. GetStringFromSettingsByKey(const std::string& key) ---
std::string GetStringFromSettingsByKey(const std::string& key) {
    std::string result = GetValueStringFromContent_JSONLike(key);
    if (result.empty()) {
        std::cerr << "Warning: Key '" << key << "' not found or value empty in settings." << std::endl;
    }
    return result;
}

// --- GetIntFromSettingsByKey(const std::string& key) - **IMPROVED ROBUSTNESS** ---
int GetIntFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) {
        return 0;
    }

    // Use stringstream for safer conversion and error checking
    std::stringstream ss(valueStr);
    int value;

    if (!(ss >> value)) {
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to int (Stream failure)." << std::endl;
        return 0;
    }

    // Check if there are any remaining non-whitespace characters (e.g., unexpected trailing comma)
    char remaining;
    if (ss >> remaining) {
        // This means the stream read the number, but there's garbage data remaining.
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to int (Trailing data)." << std::endl;
        return 0;
    }

    return value;
}

// --- 3. GetFloatFromSettingsByKey(const std::string& key) - **IMPROVED ROBUSTNESS** ---
float GetFloatFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) {
        return std::numeric_limits<float>::quiet_NaN();
    }

    // Use stringstream for safer conversion and error checking
    std::stringstream ss(valueStr);
    float value;

    if (!(ss >> value)) {
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to float (Stream failure)." << std::endl;
        return std::numeric_limits<float>::quiet_NaN();
    }

    // Check if there are any remaining non-whitespace characters
    char remaining;
    if (ss >> remaining) {
        std::cerr << "Error converting '" << valueStr << "' for key '" << key << "' to float (Trailing data)." << std::endl;
        return std::numeric_limits<float>::quiet_NaN();
    }

    return value;
}

// --- 4. GetBoolFromSettingsByKey(const std::string& key) (No changes needed) ---
bool GetBoolFromSettingsByKey(const std::string& key) {
    std::string normalizedContent = GetValueStringFromContent_JSONLike(key);

    std::transform(normalizedContent.begin(), normalizedContent.end(), normalizedContent.begin(), ::tolower);

    if (normalizedContent == "true" || normalizedContent == "1") {
        return true;
    }
    else {
        return false;
    }
}