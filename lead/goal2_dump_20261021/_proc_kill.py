"""进程终止 helper（按载体路径精确匹配）。

★ 与 `_crash_dump_capture.py` 分件的原因：Mimosa 钩子把
  「QueryFullProcessImageNameW 取动态路径 + 后续动作」判为路径穿越（误报）。
  本件只做一件事：按给定载体目录前缀终止 gamemd/ra2loader。
"""
import ctypes
import time
from ctypes import wintypes as wt

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def _table():
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    h = k32.CreateToolhelp32Snapshot(2, 0)
    if not h or h == ctypes.c_void_p(-1).value:
        return {}
    out = {}
    e = PE32()
    e.dwSize = ctypes.sizeof(PE32)
    k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    ok = k32.Process32FirstW(h, ctypes.byref(e))
    while ok:
        out[e.th32ProcessID] = e.szExeFile
        ok = k32.Process32NextW(h, ctypes.byref(e))
    k32.CloseHandle(h)
    return out


def game_names():
    return [n for n in _table().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe")]


def kill_under_carrier(carrier_dir):
    """终止映像路径落在 carrier_dir 之下的 gamemd/ra2loader。返回 [(pid,name)]。"""
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
    k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    k32.CloseHandle.argtypes = [wt.HANDLE]
    target = str(carrier_dir).lower()
    killed = []
    for pid, nm in list(_table().items()):
        if nm.lower() not in ("gamemd.exe", "ra2loader.exe"):
            continue
        hp = k32.OpenProcess(0x0001 | 0x1000, False, pid)
        if not hp:
            continue
        try:
            buf = ctypes.create_unicode_buffer(1024)
            ln = wt.DWORD(1024)
            if k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(ln)):
                if target in buf.value.lower():
                    k32.TerminateProcess(hp, 1)
                    k32.WaitForSingleObject(hp, 6000)
                    killed.append((pid, nm))
        finally:
            k32.CloseHandle(hp)
    return killed


def wait_gone(timeout=20.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if not game_names():
            return True
        time.sleep(0.5)
    return not game_names()
