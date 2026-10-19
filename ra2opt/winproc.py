"""Windows 进程创建：`CreateProcessW` 薄封装，用于启动游戏并设定优先级/亲和性。

为什么不用 `subprocess`：

1. **没有命令行解析**。这里把 exe 完整路径放在 `lpApplicationName`，并让
   `lpCommandLine` 为 NULL——不构造命令行字符串，也就不存在参数/引号层面的
   注入与转义问题（`subprocess` 在 Windows 上最终仍要拼一条命令行交给 CRT 解析）。
2. **可以先设优先级再让它跑**。以 `CREATE_SUSPENDED` 创建，等
   `SetPriorityClass` / `SetProcessAffinityMask` 都设置好再 `ResumeThread`，
   避免"先以普通优先级跑起来再改"的竞态。

调用方负责传入已经校验过的绝对路径（来自 `safewrite.resolve_within`）。
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from dataclasses import dataclass, field

CREATE_SUSPENDED = 0x00000004
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_UNICODE_ENVIRONMENT = 0x00000400

PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000

WAIT_TIMEOUT = 0x00000102
WAIT_OBJECT_0 = 0x00000000

PRIORITY_CLASSES = {
    "idle": 0x00000040,
    "below": 0x00004000,
    "normal": 0x00000020,
    "above": 0x00008000,
    "high": 0x00000080,
    "realtime": 0x00000100,
}


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


@dataclass
class SpawnedProcess:
    pid: int
    exe: str
    handle: int = 0
    thread_handle: int = 0
    priority_applied: bool = False
    affinity_applied: bool = False
    suspended: bool = False
    notes: list = field(default_factory=list)

    def alive(self) -> bool:
        if not self.handle:
            return False
        return _kernel32().WaitForSingleObject(self.handle, 0) == WAIT_TIMEOUT

    def terminate(self, exit_code: int = 0) -> bool:
        if not self.handle:
            return False
        k32 = _kernel32()
        ok = bool(k32.TerminateProcess(self.handle, exit_code))
        k32.WaitForSingleObject(self.handle, 5000)
        return ok

    def wait(self, timeout_ms: int = -1):
        """等待退出。返回退出码；超时返回 None。"""
        k32 = _kernel32()
        rc = k32.WaitForSingleObject(self.handle, timeout_ms)
        if rc == WAIT_TIMEOUT:
            return None
        code = wintypes.DWORD(0)
        k32.GetExitCodeProcess(self.handle, ctypes.byref(code))
        return code.value

    def close(self) -> None:
        k32 = _kernel32()
        if self.thread_handle:
            k32.CloseHandle(self.thread_handle)
            self.thread_handle = 0
        if self.handle:
            k32.CloseHandle(self.handle)
            self.handle = 0


def _kernel32():
    if not sys.platform.startswith("win"):
        raise RuntimeError("本功能仅支持 Windows")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not getattr(k32, "_ra2opt_typed", False):
        k32.CreateProcessW.argtypes = [
            wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
            wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
            ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION),
        ]
        k32.CreateProcessW.restype = wintypes.BOOL
        k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.ResumeThread.argtypes = [wintypes.HANDLE]
        k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k32._ra2opt_typed = True
    return k32


def spawn(exe_path, *, cwd: str | None = None, priority: str = "normal",
          affinity: int | None = None, suspended_until_configured: bool = True) -> SpawnedProcess:
    """以 `CreateProcessW` 启动 exe。

    `exe_path` 必须是已校验的绝对路径；不传任何命令行参数。
    """
    exe = os.path.abspath(os.fspath(exe_path))
    if not os.path.isfile(exe):
        raise FileNotFoundError(f"可执行文件不存在：{exe}")
    workdir = cwd or os.path.dirname(exe)

    k32 = _kernel32()
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "winsta0\\default"
    pi = PROCESS_INFORMATION()

    flags = CREATE_UNICODE_ENVIRONMENT | CREATE_NEW_PROCESS_GROUP
    if suspended_until_configured:
        flags |= CREATE_SUSPENDED

    ok = k32.CreateProcessW(
        exe,               # lpApplicationName：完整路径，不参与命令行解析
        None,              # lpCommandLine：留空，不构造命令行
        None, None,        # 进程/线程安全属性：不继承
        False,             # bInheritHandles
        flags,
        None,              # 环境块沿用父进程
        workdir,           # 工作目录 = 游戏目录
        ctypes.byref(si),
        ctypes.byref(pi),
    )
    if not ok:
        err = ctypes.get_last_error()
        raise OSError(f"CreateProcessW 失败（错误码 {err}）")

    proc = SpawnedProcess(pid=int(pi.dwProcessId), exe=exe,
                          handle=int(pi.hProcess), thread_handle=int(pi.hThread),
                          suspended=bool(suspended_until_configured))

    if priority in PRIORITY_CLASSES:
        proc.priority_applied = bool(k32.SetPriorityClass(proc.handle, PRIORITY_CLASSES[priority]))
        if not proc.priority_applied:
            proc.notes.append(f"设置优先级 {priority} 失败（错误码 {ctypes.get_last_error()}）")
    else:
        proc.notes.append(f"未知优先级 {priority}，已跳过")

    if affinity is not None:
        proc.affinity_applied = bool(k32.SetProcessAffinityMask(proc.handle, affinity))
        if not proc.affinity_applied:
            proc.notes.append(f"设置 CPU 亲和性 {affinity:#x} 失败")

    if proc.suspended:
        if not k32.ResumeThread(proc.thread_handle):
            proc.notes.append(f"ResumeThread 失败（错误码 {ctypes.get_last_error()}）")
        else:
            proc.suspended = False
    return proc


def cpu_mask(cpus) -> int:
    """把 CPU 序号列表（如 [0] 或 [0,1]）转成亲和性掩码。"""
    mask = 0
    for cpu in cpus:
        mask |= 1 << int(cpu)
    return mask
