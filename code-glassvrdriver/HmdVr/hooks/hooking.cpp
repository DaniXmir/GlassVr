#include "hooking.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <atomic>

namespace glassvr {

    static std::atomic<int> g_refCount{ 0 };

    bool InitHookingLibrary()
    {
        if (g_refCount.fetch_add(1) == 0) {
            MH_STATUS s = MH_Initialize();
            if (s != MH_OK && s != MH_ERROR_ALREADY_INITIALIZED) {
                HookLog("[hooks] MH_Initialize failed (%d)", (int)s);
                g_refCount.fetch_sub(1);
                return false;
            }
            HookLog("[hooks] MinHook initialized");
        }
        return true;
    }

    void CleanupHookingLibrary()
    {
        if (g_refCount.fetch_sub(1) == 1) {
            MH_DisableHook(MH_ALL_HOOKS);
            MH_Uninitialize();
            HookLog("[hooks] MinHook uninitialized");
        }
    }

    void HookLog(const char* fmt, ...)
    {
        char buf[1024];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buf, sizeof(buf) - 2, fmt, args);
        va_end(args);

        size_t len = strlen(buf);
        if (len + 2 < sizeof(buf)) {
            buf[len] = '\n';
            buf[len + 1] = '\0';
        }

        if (vr::VRDriverLog())
            vr::VRDriverLog()->Log(buf);

        OutputDebugStringA(buf);
    }

}