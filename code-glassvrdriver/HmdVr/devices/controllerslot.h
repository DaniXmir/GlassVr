#pragma once
#include <map>
#include <string>

class ControllerBase;

class ControllerSlot
{
public:
    explicit ControllerSlot(bool right);
    ~ControllerSlot();

    void Sync();

    void RunFrame();

    void Shutdown();

private:
    bool m_right;
    std::map<std::string, ControllerBase*> m_controllers;
    ControllerBase* m_active = nullptr;
    std::string m_activeType;
    std::string m_failedType;
};
