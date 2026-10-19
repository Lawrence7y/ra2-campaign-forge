#define _CRT_SECURE_NO_WARNINGS
#include "ra2render.h"

static FILE *s_pLogFile = nullptr;

void LogMessage(const char *fmt, ...) {
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    OutputDebugStringA(buf);
    OutputDebugStringA("\n");

    if (!s_pLogFile) {
        s_pLogFile = fopen("ra2render.log", "a");
    }
    if (s_pLogFile) {
        fprintf(s_pLogFile, "%s\n", buf);
        fflush(s_pLogFile);
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved) {
    switch (fdwReason) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hinstDLL);
        LogMessage("==================================================");
        LogMessage("[ra2render] 模块已成功注入到目标进程 (PID: %lu)", GetCurrentProcessId());
        InstallVTableHooks();
        EnableLowFragmentationHeap();
        if (g_highPrecisionTimer) {
            timeBeginPeriod(1);
            LogMessage("[ra2render] 系统时钟: 已将系统调度周期锁定为 1ms 高精度");
        }
        break;

    case DLL_PROCESS_DETACH:
        LogMessage("[ra2render] 模块正在卸载...");
        if (g_highPrecisionTimer) {
            timeEndPeriod(1);
        }
        RemoveVTableHooks();
        if (s_pLogFile) {
            fclose(s_pLogFile);
            s_pLogFile = nullptr;
        }
        break;
    }
    return TRUE;
}
