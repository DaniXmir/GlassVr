#pragma once

#include <string>
#include <limits>

extern const std::string SettingsFileName;
extern const std::string AppFolderName;

extern std::string g_settingsContent;

std::string GetFullSettingsPath();
std::string trim_value(const std::string& str);
const std::string& GetSettings();
std::string GetValueStringFromContent_JSONLike(const std::string& key);

std::string GetStringFromSettingsByKey(const std::string& key);
int GetIntFromSettingsByKey(const std::string& key);
float GetFloatFromSettingsByKey(const std::string& key);
bool GetBoolFromSettingsByKey(const std::string& key);