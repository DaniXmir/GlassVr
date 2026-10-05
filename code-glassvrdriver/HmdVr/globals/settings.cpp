//driver settings file equivalent, same logic as python side
#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include "hmd.h"

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
#include <mutex>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vr;

const std::string SettingsFileName = "settings.json";
const std::string AppFolderName = "glassvr";

std::string g_settingsContent;

std::string g_lastGoodSettingsContent;


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

#include <chrono>

std::chrono::steady_clock::time_point g_lastLoadTime;
const int REFRESH_INTERVAL_MS = 1;

static std::recursive_mutex g_settingsMutex;

static void ReloadSettingsIfStale_Locked() {
    auto currentTime = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - g_lastLoadTime).count();

    if (duration <= REFRESH_INTERVAL_MS && !g_settingsContent.empty()) {
        return;
    }

    g_lastLoadTime = currentTime;

    const std::string FullSettingsPath = GetFullSettingsPath();
    std::ifstream file(FullSettingsPath);

    if (file.is_open()) {
        std::string freshContent(
            (std::istreambuf_iterator<char>(file)),
            (std::istreambuf_iterator<char>())
        );
        file.close();

        if (!freshContent.empty()) {
            g_settingsContent = freshContent;
            g_lastGoodSettingsContent = freshContent;
            return;
        }
    }

    if (!g_lastGoodSettingsContent.empty()) {
        g_settingsContent = g_lastGoodSettingsContent;
    }
}

const std::string& GetSettings() {
    std::lock_guard<std::recursive_mutex> lock(g_settingsMutex);
    ReloadSettingsIfStale_Locked();
    return g_settingsContent;
}

std::string GetSettingsSnapshot() {
    std::lock_guard<std::recursive_mutex> lock(g_settingsMutex);
    ReloadSettingsIfStale_Locked();
    return g_settingsContent;
}

std::string GetValueStringFromContent_JSONLike(const std::string& key) {
    const std::string content = GetSettingsSnapshot();
    if (content.empty()) return "";

    std::string searchKey = "\"" + key + "\"";
    size_t keyPos = content.find(searchKey);
    if (keyPos == std::string::npos) return "";

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
    if (valueStr.empty()) return 0;

    try {
        return std::stoi(valueStr);
    }
    catch (...) {
        return 0;
    }
}

float GetFloatFromSettingsByKey(const std::string& key) {
    std::string valueStr = GetValueStringFromContent_JSONLike(key);
    if (valueStr.empty()) return 0.0f;

    try {
        return std::stof(valueStr);
    }
    catch (...) {
        std::stringstream ss(valueStr);
        float value;
        if (ss >> value) return value;
        return 0.0f;
    }
}

bool GetBoolFromSettingsByKey(const std::string& key) {
    std::string val = GetValueStringFromContent_JSONLike(key);
    if (val.empty()) return false;

    std::transform(val.begin(), val.end(), val.begin(), ::tolower);
    return (val == "true" || val == "1");
}

namespace {

    bool FindKeyValuePos(const std::string& c, const std::string& key, size_t& outPos) {
        const std::string sk = "\"" + key + "\"";
        size_t pos = 0;
        while ((pos = c.find(sk, pos)) != std::string::npos) {
            size_t p = pos + sk.size();
            while (p < c.size() && isspace((unsigned char)c[p])) p++;
            if (p < c.size() && c[p] == ':') { outPos = p + 1; return true; }
            pos = p;
        }
        return false;
    }

    bool ExtractBlock(const std::string& c, size_t from, char open, char close, std::string& out) {
        size_t p = from;
        while (p < c.size() && isspace((unsigned char)c[p])) p++;
        if (p >= c.size() || c[p] != open) return false;

        int depth = 0;
        bool inStr = false, esc = false;
        for (size_t i = p; i < c.size(); ++i) {
            char ch = c[i];
            if (inStr) {
                if (esc)              esc = false;
                else if (ch == '\\')  esc = true;
                else if (ch == '"')   inStr = false;
                continue;
            }
            if (ch == '"') { inStr = true; continue; }
            if (ch == open) depth++;
            else if (ch == close) {
                depth--;
                if (depth == 0) { out = c.substr(p + 1, i - p - 1); return true; }
            }
        }
        return false;
    }

    std::vector<std::string> SplitObjects(const std::string& body) {
        std::vector<std::string> objects;
        int depth = 0;
        size_t start = 0;
        bool inStr = false, esc = false;

        for (size_t i = 0; i < body.size(); ++i) {
            char ch = body[i];
            if (inStr) {
                if (esc)              esc = false;
                else if (ch == '\\')  esc = true;
                else if (ch == '"')   inStr = false;
                continue;
            }
            if (ch == '"') { inStr = true; continue; }
            if (ch == '{') { if (depth == 0) start = i; depth++; }
            else if (ch == '}') {
                depth--;
                if (depth == 0) objects.push_back(body.substr(start + 1, i - start - 1));
            }
        }
        return objects;
    }

    SettingsDict ParseObject(const std::string& s) {
        SettingsDict out;
        size_t i = 0;

        while (i < s.size()) {
            size_t ks = s.find('"', i);
            if (ks == std::string::npos) break;

            size_t ke = ks + 1;
            bool esc = false;
            while (ke < s.size()) {
                if (esc)                esc = false;
                else if (s[ke] == '\\') esc = true;
                else if (s[ke] == '"')  break;
                ke++;
            }
            if (ke >= s.size()) break;

            const std::string key = s.substr(ks + 1, ke - ks - 1);

            size_t colon = s.find(':', ke + 1);
            if (colon == std::string::npos) break;

            size_t v = colon + 1;
            while (v < s.size() && isspace((unsigned char)s[v])) v++;

            size_t j = v;
            int depth = 0;
            bool inStr = false;
            esc = false;
            for (; j < s.size(); ++j) {
                char ch = s[j];
                if (inStr) {
                    if (esc)              esc = false;
                    else if (ch == '\\')  esc = true;
                    else if (ch == '"')   inStr = false;
                    continue;
                }
                if (ch == '"') { inStr = true; continue; }
                if (ch == '{' || ch == '[')      depth++;
                else if (ch == '}' || ch == ']') depth--;
                else if (ch == ',' && depth == 0) break;
            }

            out[key] = trim_value(s.substr(v, j - v));
            i = j + 1;
        }
        return out;
    }

}

std::vector<SettingsDict> GetDictArrayFromSettingsByKey(const std::string& key) {
    std::vector<SettingsDict> result;

    const std::string content = GetSettingsSnapshot();
    if (content.empty()) return result;

    size_t valuePos = 0;
    if (!FindKeyValuePos(content, key, valuePos)) return result;

    std::string arrayBody;
    if (!ExtractBlock(content, valuePos, '[', ']', arrayBody)) return result;

    for (const std::string& obj : SplitObjects(arrayBody)) {
        SettingsDict dict = ParseObject(obj);
        if (!dict.empty()) result.push_back(dict);
    }
    return result;
}

bool DictHas(const SettingsDict& dict, const std::string& key) {
    return dict.find(key) != dict.end();
}

std::string DictGetString(const SettingsDict& dict, const std::string& key,
    const std::string& fallback) {
    auto it = dict.find(key);
    if (it == dict.end() || it->second.empty()) return fallback;
    return it->second;
}

bool DictGetBool(const SettingsDict& dict, const std::string& key, bool fallback) {
    auto it = dict.find(key);
    if (it == dict.end() || it->second.empty()) return fallback;

    std::string val = it->second;
    std::transform(val.begin(), val.end(), val.begin(), ::tolower);
    if (val == "true" || val == "1" || val == "yes" || val == "on")  return true;
    if (val == "false" || val == "0" || val == "no" || val == "off") return false;
    return fallback;
}

int DictGetInt(const SettingsDict& dict, const std::string& key, int fallback) {
    auto it = dict.find(key);
    if (it == dict.end() || it->second.empty()) return fallback;
    try { return std::stoi(it->second); }
    catch (...) { return fallback; }
}

float DictGetFloat(const SettingsDict& dict, const std::string& key, float fallback) {
    auto it = dict.find(key);
    if (it == dict.end() || it->second.empty()) return fallback;
    try { return std::stof(it->second); }
    catch (...) { return fallback; }
}