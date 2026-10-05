#ifndef GLASSVR_HOOKING_H
#define GLASSVR_HOOKING_H

#include "MinHooK/MinHook.h"
#include <openvr_driver.h>
#include <cstdio>
#include <cstdarg>

namespace glassvr {

    bool InitHookingLibrary();
    void CleanupHookingLibrary();

    inline void* GetVTableEntry(void* pInstance, int index)
    {
        if (!pInstance) return nullptr;
        void** vtable = *reinterpret_cast<void***>(pInstance);
        return vtable[index];
    }

    inline void** GetVTable(void* pInstance)
    {
        if (!pInstance) return nullptr;
        return *reinterpret_cast<void***>(pInstance);
    }

    void HookLog(const char* fmt, ...);

    template <class FT>
    class Hook
    {
    public:
        explicit Hook(const char* name) : m_name(name) {}

        bool CreateFromVTable(void* pInstance, int slot, void* pDetour)
        {
            void* pTarget = GetVTableEntry(pInstance, slot);
            if (!pTarget) {
                HookLog("[hooks] %s: null vtable entry (slot %d)", m_name, slot);
                return false;
            }
            return CreateFromAddress(pTarget, pDetour);
        }

        bool CreateFromAddress(void* pTarget, void* pDetour)
        {
            MH_STATUS s = MH_CreateHook(pTarget, pDetour,
                reinterpret_cast<LPVOID*>(&originalFunc));
            if (s == MH_ERROR_ALREADY_CREATED) {
                HookLog("[hooks] %s: already hooked by someone else", m_name);
                return false;
            }
            if (s != MH_OK) {
                HookLog("[hooks] %s: MH_CreateHook failed (%d)", m_name, (int)s);
                return false;
            }
            if (MH_EnableHook(pTarget) != MH_OK) {
                HookLog("[hooks] %s: MH_EnableHook failed", m_name);
                MH_RemoveHook(pTarget);
                originalFunc = nullptr;
                return false;
            }
            m_target = pTarget;
            m_enabled = true;
            HookLog("[hooks] %s: installed at %p", m_name, pTarget);
            return true;
        }

        void Destroy()
        {
            if (!m_enabled) return;
            MH_DisableHook(m_target);
            MH_RemoveHook(m_target);
            m_enabled = false;
            m_target = nullptr;
            originalFunc = nullptr;
        }

        bool IsEnabled() const { return m_enabled; }
        const char* Name() const { return m_name; }

        FT originalFunc = nullptr;

    private:
        const char* m_name;
        void* m_target = nullptr;
        bool m_enabled = false;
    };

}

#endif