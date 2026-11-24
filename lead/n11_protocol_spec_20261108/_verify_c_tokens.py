# _verify_c_tokens.py — 禁用记号独立扫描（含伪代码级 API 变体），并检查代码围栏内容
import io, re, os

P = r"D:\Project\ra2-campaign-forge\lead\n11_protocol_spec_20261108\_ps_N11_MIN_OBS_PROTOCOL_SPEC.md"

# 铁律禁令记号 + 伪代码级变体 + 动态解析/工具链痕迹
TOKENS = [
    "hook", "Hook", "HOOK",
    "MiniDump", "SuspendThread", "StackWalk", "StackCapture",
    "ctypes", "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
    "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHookEx", "TerminateProcess",
    "注入", "探针",
    # 变体/底层痕迹（防动态解析、伪代码规避）
    "LoadLibrary", "GetProcAddress", "kernel32", "ntdll", "psapi", "dbghelp",
    "CreateToolhelp32Snapshot", "EnumProcessModules", "Module32First",
    "DebugActiveProcess", "IsDebuggerPresent", "CheckRemoteDebuggerPresent",
    "NtQueryInformationProcess", "ZwQueryInformation",
    "RtlCaptureStack", "CaptureStackBackTrace", "SymFromAddr", "SymGetLine",
    "capstone", "distorm", "keystone", "unicorn",
    "WriteProcessMemory", "VirtualProtectEx", "CreateProcessA", "CreateProcessW",
    "SetThreadContext", "GetThreadContext", "ResumeThread", "TerminateThread",
    "WaitForSingleObject", "DuplicateHandle", "imp_", "!papi", "pdbs",
    "ReadFile", "WriteFile", "DeviceIoControl",
    # 内存/句柄操作话术
    "句柄获取", "内存读取", "内存写入", "内存注入", "代码洞", "shellcode",
    "import ctypes", "wintypes", "windll", "cdll",
]

with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

hits = []
for i, ln in enumerate(lines, 1):
    for t in TOKENS:
        if t in ln:
            hits.append((i, t))

print("== 禁用记号命中（行号, 记号）==")
for i, t in hits:
    print(f"  L{i}: [{t}]")
uniq_lines = sorted(set(i for i, _ in hits))
print("命中行合计:", uniq_lines)

# 每个命中行打印上下文，供人工判定肯定式/否定式
print("\n== 命中行原文 ==")
for i in uniq_lines:
    print(f"L{i}: {lines[i-1]}")

# 代码围栏检查：``` 块内容（防伪代码藏 API）
print("\n== 代码围栏（```）块 ==")
in_fence = False
fence_start = 0
for i, ln in enumerate(lines, 1):
    if ln.strip().startswith("```"):
        if not in_fence:
            in_fence = True
            fence_start = i
            print(f"  fence open  L{i}: {ln.strip()[:60]}")
        else:
            in_fence = False
            print(f"  fence close L{i} (block {fence_start}-{i})")
if in_fence:
    print("  [WARN] 未闭合围栏")

# 可执行痕迹：管道/调用式语句（如 python -c、os.system、subprocess）
print("\n== 进程执行/管道式语句扫描 ==")
for i, ln in enumerate(lines, 1):
    if re.search(r"(os\.system|subprocess|popen|Popen|os\.exec|&\s*gamemd|ra2loader|YURI\.exe|taskkill)", ln):
        print(f"  L{i}: {ln.strip()[:120]}")
print("== done ==")
