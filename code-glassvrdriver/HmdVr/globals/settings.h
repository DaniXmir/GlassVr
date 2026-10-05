#pragma once

#include <string>
#include <limits>
#include <map>
#include <vector>

extern const std::string SettingsFileName;
extern const std::string AppFolderName;

extern std::string g_settingsContent;

std::string GetFullSettingsPath();
std::string trim_value(const std::string& str);

const std::string& GetSettings();

std::string GetSettingsSnapshot();

std::string GetValueStringFromContent_JSONLike(const std::string& key);

std::string GetStringFromSettingsByKey(const std::string& key);
int GetIntFromSettingsByKey(const std::string& key);
float GetFloatFromSettingsByKey(const std::string& key);
bool GetBoolFromSettingsByKey(const std::string& key);

typedef std::map<std::string, std::string> SettingsDict;

std::vector<SettingsDict> GetDictArrayFromSettingsByKey(const std::string& key);

std::string DictGetString(const SettingsDict& dict, const std::string& key,
    const std::string& fallback = "");
bool  DictGetBool(const SettingsDict& dict, const std::string& key, bool  fallback = false);
int   DictGetInt(const SettingsDict& dict, const std::string& key, int   fallback = 0);
float DictGetFloat(const SettingsDict& dict, const std::string& key, float fallback = 0.0f);
bool  DictHas(const SettingsDict& dict, const std::string& key);