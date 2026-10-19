#define WIN32_LEAN_AND_MEAN
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <cstdio>
#include <cstring>

int main(int argc, char* argv[]) {
    char exeDir[MAX_PATH];
    GetModuleFileNameA(NULL, exeDir, MAX_PATH);
    char* pLastSlash = strrchr(exeDir, '\\');
    if (pLastSlash) *pLastSlash = '\0';

    char gamePath[MAX_PATH];
    snprintf(gamePath, MAX_PATH, "%s\\gamemd.exe", exeDir);

    char dllPath[MAX_PATH];
    snprintf(dllPath, MAX_PATH, "%s\\ra2render.dll", exeDir);

    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    printf("==================================================\n");
    printf("[ra2loader] 尤里的复仇 L1/L2 现代化极速加载器\n");
    printf("[ra2loader] 工作目录: %s\n", exeDir);
    printf("[ra2loader] 目标可执行文件: %s\n", gamePath);
    printf("[ra2loader] 注入渲染扩展: %s\n", dllPath);
    printf("==================================================\n");

    char cmdLine[2048] = { 0 };
    snprintf(cmdLine, sizeof(cmdLine), "\"%s\"", gamePath);
    for (int i = 1; i < argc; ++i) {
        strncat(cmdLine, " ", sizeof(cmdLine) - strlen(cmdLine) - 1);
        strncat(cmdLine, argv[i], sizeof(cmdLine) - strlen(cmdLine) - 1);
    }

    if (!CreateProcessA(gamePath, cmdLine, NULL, NULL, FALSE, CREATE_SUSPENDED, NULL, exeDir, &si, &pi)) {
        printf("[错误] 无法启动 gamemd.exe (错误码 %lu)\n", GetLastError());
        return 1;
    }

    SetPriorityClass(pi.hProcess, HIGH_PRIORITY_CLASS);

    void* remoteMem = VirtualAllocEx(pi.hProcess, NULL, strlen(dllPath) + 1, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remoteMem) {
        printf("[错误] VirtualAllocEx 内存分配失败 (错误码 %lu)\n", GetLastError());
        ResumeThread(pi.hThread);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 1;
    }

    WriteProcessMemory(pi.hProcess, remoteMem, dllPath, strlen(dllPath) + 1, NULL);
    HMODULE hK32 = GetModuleHandleA("kernel32.dll");
    FARPROC pLoadLib = GetProcAddress(hK32, "LoadLibraryA");

    HANDLE hThread = CreateRemoteThread(pi.hProcess, NULL, 0, (LPTHREAD_START_ROUTINE)pLoadLib, remoteMem, 0, NULL);
    if (hThread) {
        WaitForSingleObject(hThread, 5000);
        CloseHandle(hThread);
        printf("[ra2loader] ra2render.dll 注入并初始化完成！\n");
    } else {
        printf("[错误] CreateRemoteThread 远程线程创建失败 (错误码 %lu)\n", GetLastError());
    }

    VirtualFreeEx(pi.hProcess, remoteMem, 0, MEM_RELEASE);

    printf("[ra2loader] 游戏主线程已恢复，进入战场！\n");
    ResumeThread(pi.hThread);
    CloseHandle(pi.hThread);

    // 守护游戏进程生命周期
    WaitForSingleObject(pi.hProcess, INFINITE);
    CloseHandle(pi.hProcess);
    return 0;
}
