# -*- coding: utf-8 -*-
"""StackWalk64 真栈回溯 —— 独立验证件（先验证内核能力，再接入候选件）。

双架构：
  32 位目标（charmap.exe 等）→ IMAGE_FILE_MACHINE_I386(0x14c) + WOW64_CONTEXT
  64 位目标（python 等）    → IMAGE_FILE_MACHINE_AMD64(0x8664) + CONTEXT_AMD64

依赖 dbghelp.dll（系统自带）：
  SymInitialize / SymCleanup
  SymFunctionTableAccess64 / SymGetModuleBase64
  StackWalk64

关键点：
  - 必须先 SuspendThread 再取上下文（Win32 要求）
  - STACKFRAME64 需按架构填 AddrPC/AddrFrame/AddrStack
  - 32 位目标的 StackWalk64 需传 WOW64_CONTEXT 作 ContextRecord
  - 必须给 ReadMemoryRoutine（跨进程读栈），否则 dbghelp 用内部读取可能失败
  - 模块名+偏移用 SymFromAddr；无符号时仍可用 SymGetModuleBase64 算 module+offset
"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
OUT = REPO / "lead" / "re_d13_ruling_20261112"

# ---------------------------------------------------------------- 常量
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_FILE_MACHINE_AMD64 = 0x8664

WOW64_CONTEXT_i386 = 0x00010000
WOW64_CONTEXT_CONTROL = WOW64_CONTEXT_i386 | 0x00000001
CONTEXT_AMD64 = 0x00100000
CONTEXT_AMD64_CONTROL = CONTEXT_AMD64 | 0x00000001

AddrModeFlat = 3
MAX_FRAMES = 32
_LAST_WALK_ERR = []


# ---------------------------------------------------------------- 结构
class ADDRESS64(ctypes.Structure):
    _fields_ = [("Offset", ctypes.c_uint64),
                ("Segment", wt.WORD),
                ("Mode", ctypes.c_uint32)]


class KDHELP64(ctypes.Structure):
    _fields_ = [("Thread", ctypes.c_uint64),
                ("ThCallbackStack", wt.DWORD),
                ("ThCallbackBStore", wt.DWORD),
                ("NextCallback", wt.DWORD),
                ("FramePointer", wt.DWORD),
                ("KiCallUserMode", ctypes.c_uint64),
                ("KeUserCallbackDispatcher", ctypes.c_uint64),
                ("SystemRangeStart", ctypes.c_uint64),
                ("KiUserExceptionDispatcher", ctypes.c_uint64),
                ("StackBase", ctypes.c_uint64),
                ("StackLimit", ctypes.c_uint64),
                ("BuildVersion", wt.DWORD),
                ("RetpolineStub", wt.DWORD),
                ("Reserved", ctypes.c_uint64 * 4)]


class STACKFRAME64(ctypes.Structure):
    _fields_ = [("AddrPC", ADDRESS64),
                ("AddrReturn", ADDRESS64),
                ("AddrFrame", ADDRESS64),
                ("AddrStack", ADDRESS64),
                ("AddrBStore", ADDRESS64),
                ("FuncTableEntry", ctypes.c_void_p),
                ("Params", ctypes.c_uint64 * 4),
                ("Far", wt.BOOL),
                ("Virtual", wt.BOOL),
                ("Reserved", ctypes.c_uint64 * 3),
                ("KdHelp", KDHELP64)]


class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("ContextFlags", wt.DWORD),
        ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
        ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
        ("FloatSave", ctypes.c_byte * 112),
        ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
        ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
        ("Ecx", wt.DWORD), ("Eax", wt.DWORD),
        ("Ebp", wt.DWORD), ("Eip", wt.DWORD), ("SegCs", wt.DWORD), ("EFlags", wt.DWORD),
        ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
        ("ExtendedRegisters", ctypes.c_byte * 512),
    ]


class CONTEXT_AMD64_S(ctypes.Structure):
    _fields_ = ([("P%dHome" % i, ctypes.c_uint64) for i in range(1, 7)] +
                [("ContextFlags", wt.DWORD), ("MxCsr", wt.DWORD),
                 ("SegCs", wt.WORD), ("SegDs", wt.WORD), ("SegEs", wt.WORD),
                 ("SegFs", wt.WORD), ("SegGs", wt.WORD), ("SegSs", wt.WORD),
                 ("EFlags", wt.DWORD),
                 ("Dr0", ctypes.c_uint64), ("Dr1", ctypes.c_uint64),
                 ("Dr2", ctypes.c_uint64), ("Dr3", ctypes.c_uint64),
                 ("Dr6", ctypes.c_uint64), ("Dr7", ctypes.c_uint64),
                 ("Rax", ctypes.c_uint64), ("Rcx", ctypes.c_uint64),
                 ("Rdx", ctypes.c_uint64), ("Rbx", ctypes.c_uint64),
                 ("Rsp", ctypes.c_uint64), ("Rbp", ctypes.c_uint64),
                 ("Rsi", ctypes.c_uint64), ("Rdi", ctypes.c_uint64),
                 ("R8", ctypes.c_uint64), ("R9", ctypes.c_uint64),
                 ("R10", ctypes.c_uint64), ("R11", ctypes.c_uint64),
                 ("R12", ctypes.c_uint64), ("R13", ctypes.c_uint64),
                 ("R14", ctypes.c_uint64), ("R15", ctypes.c_uint64),
                 ("Rip", ctypes.c_uint64),
                 ("_tail", ctypes.c_byte * 976)])


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", wt.LONG), ("tpDeltaPri", wt.LONG), ("dwFlags", wt.DWORD)]


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                ("ProccntUsage", wt.DWORD), ("modBaseAddr", ctypes.c_void_p),
                ("modBaseSize", wt.DWORD), ("hModule", wt.HMODULE),
                ("szModule", wt.CHAR * 256), ("szExePath", wt.CHAR * 260)]


TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010


# ---------------------------------------------------------------- 绑定
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.SuspendThread.restype = wt.DWORD
k32.SuspendThread.argtypes = [wt.HANDLE]
k32.ResumeThread.restype = wt.DWORD
k32.ResumeThread.argtypes = [wt.HANDLE]
k32.GetThreadContext.restype = wt.BOOL
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Wow64GetThreadContext.restype = wt.BOOL
k32.Wow64GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.IsWow64Process.restype = wt.BOOL
k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Thread32First.restype = wt.BOOL
k32.Thread32First.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Thread32Next.restype = wt.BOOL
k32.Thread32Next.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Module32First.restype = wt.BOOL
k32.Module32First.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Module32Next.restype = wt.BOOL
k32.Module32Next.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

dbg.SymInitialize.restype = wt.BOOL
dbg.SymInitialize.argtypes = [wt.HANDLE, wt.LPCSTR, wt.BOOL]
dbg.SymCleanup.restype = wt.BOOL
dbg.SymCleanup.argtypes = [wt.HANDLE]
dbg.SymSetOptions.restype = wt.DWORD
dbg.SymSetOptions.argtypes = [wt.DWORD]
dbg.SymFunctionTableAccess64.restype = ctypes.c_void_p
dbg.SymFunctionTableAccess64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbg.SymGetModuleBase64.restype = ctypes.c_uint64
dbg.SymGetModuleBase64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbg.StackWalk64.restype = wt.BOOL
dbg.StackWalk64.argtypes = [wt.DWORD, wt.HANDLE, wt.HANDLE,
                            ctypes.POINTER(STACKFRAME64), ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p]

# 回调类型 —— ★ 必须是 5 个参数：
#   PREAD_PROCESS_MEMORY_ROUTINE64(HANDLE hProcess, DWORD64 qwBaseAddress,
#                                  PVOID lpBuffer, DWORD nSize, LPDWORD lpNumberOfBytesRead)
# 曾漏掉 nSize 参数 ⇒ 每次回调抛 TypeError ⇒ StackWalk64 读不到父帧 ⇒ 只回 1 帧。
PREADPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HANDLE, ctypes.c_uint64,
                               ctypes.c_void_p, wt.DWORD,
                               ctypes.POINTER(wt.DWORD))


def read_mem_cb(hProcess, qwBaseAddress, lpBuffer, nSize, lpNumberOfBytesRead):
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hProcess, ctypes.c_void_p(qwBaseAddress),
                               lpBuffer, nSize, ctypes.byref(n))
    if lpNumberOfBytesRead:
        lpNumberOfBytesRead[0] = n.value
    return bool(ok)


_READ_CB = PREADPROC(read_mem_cb)


def modules_of(pid):
    """枚举目标模块 → [(base, size, name)]，供 module+offset 命名。"""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    out = []
    if not snap or snap == -1:
        return out
    try:
        me = MODULEENTRY32()
        me.dwSize = ctypes.sizeof(MODULEENTRY32)
        ok = k32.Module32First(snap, ctypes.byref(me))
        while ok:
            name = bytes(me.szModule).split(b"\x00")[0].decode("latin1", "replace")
            out.append((int(me.modBaseAddr or 0), int(me.modBaseSize), name))
            me.dwSize = ctypes.sizeof(MODULEENTRY32)
            ok = k32.Module32Next(snap, ctypes.byref(me))
    finally:
        k32.CloseHandle(snap)
    return out


def mod_name(mods, addr):
    for base, size, name in mods:
        if base <= addr < base + size:
            return "%s+0x%x" % (name, addr - base)
    return None


def threads_of(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    out = []
    if not snap or snap == -1:
        return out
    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(THREADENTRY32)
        ok = k32.Thread32First(snap, ctypes.byref(te))
        while ok:
            if te.th32OwnerProcessID == pid:
                out.append(int(te.th32ThreadID))
            te.dwSize = ctypes.sizeof(THREADENTRY32)
            ok = k32.Thread32Next(snap, ctypes.byref(te))
    finally:
        k32.CloseHandle(snap)
    return out


def walk_thread(hproc, tid, is32, mods, max_frames=MAX_FRAMES):
    """对单线程做 StackWalk64 回溯。返回 (frames, err)。

    frames: [{"addr":int, "name":str|None}] —— 逐帧指令地址
    """
    th = k32.OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                        THREAD_QUERY_INFORMATION, False, tid)
    if not th:
        return ([], "open_thread_fail:%d" % ctypes.get_last_error())
    suspended = False
    try:
        prev = k32.SuspendThread(th)
        if prev in (0xFFFFFFFF, -1):
            return ([], "suspend_fail")
        suspended = True

        sf = STACKFRAME64()
        ctypes.memset(ctypes.byref(sf), 0, ctypes.sizeof(sf))
        sf.AddrPC.Mode = AddrModeFlat
        sf.AddrFrame.Mode = AddrModeFlat
        sf.AddrStack.Mode = AddrModeFlat

        if is32:
            ctx = WOW64_CONTEXT()
            ctx.ContextFlags = WOW64_CONTEXT_CONTROL
            if not k32.Wow64GetThreadContext(th, ctypes.byref(ctx)):
                return ([], "wow64_get_context_fail")
            machine = IMAGE_FILE_MACHINE_I386
            sf.AddrPC.Offset = ctx.Eip
            sf.AddrFrame.Offset = ctx.Ebp
            sf.AddrStack.Offset = ctx.Esp
            ctx_ptr = ctypes.byref(ctx)
        else:
            ctx = CONTEXT_AMD64_S()
            ctx.ContextFlags = CONTEXT_AMD64_CONTROL
            if not k32.GetThreadContext(th, ctypes.byref(ctx)):
                return ([], "get_context_fail")
            machine = IMAGE_FILE_MACHINE_AMD64
            sf.AddrPC.Offset = ctx.Rip
            sf.AddrFrame.Offset = ctx.Rbp
            sf.AddrStack.Offset = ctx.Rsp
            ctx_ptr = ctypes.byref(ctx)

        frames = []
        for _ in range(max_frames):
            ok = dbg.StackWalk64(machine, hproc, th, ctypes.byref(sf), ctx_ptr,
                                 ctypes.cast(_READ_CB, ctypes.c_void_p),
                                 ctypes.cast(dbg.SymFunctionTableAccess64, ctypes.c_void_p),
                                 ctypes.cast(dbg.SymGetModuleBase64, ctypes.c_void_p),
                                 None)
            if not ok:
                _LAST_WALK_ERR.append(ctypes.get_last_error())
                break
            pc = int(sf.AddrPC.Offset)
            if pc == 0:
                break
            frames.append({"addr": pc, "name": mod_name(mods, pc)})
            # 防止同址重复（回溯异常时不动）
            if len(frames) >= 2 and frames[-1]["addr"] == frames[-2]["addr"]:
                break
        return (frames, None)
    finally:
        if suspended:
            try:
                k32.ResumeThread(th)
            except Exception:                          # noqa: BLE001
                pass
        k32.CloseHandle(th)


def check(name, cond, ev=""):
    print("[%s] %-54s %s" % ("OK" if cond else "RED", name, ev))
    return cond


def main():
    fails = []
    n = {"v": 0}

    def t(name, cond, ev=""):
        n["v"] += 1
        if not check(name, cond, ev):
            fails.append(name)

    print("=" * 78)
    print("StackWalk64 真栈回溯验证（双架构，对受控目标）")
    print("=" * 78)

    targets = [
        ("32 位", r"C:\Windows\SysWOW64\charmap.exe", True),
        ("64 位", sys.executable, False),
    ]
    # 64 位目标需要一个长驻进程
    sleep_script = OUT / "_sleep_target.py"
    sleep_script.write_text("import time\nfor _ in range(600): time.sleep(1)\n",
                            encoding="utf-8")

    for label, exe, expect32 in targets:
        print("\n" + "=" * 78)
        print("目标: %s (%s)" % (label, Path(exe).name))
        print("=" * 78)
        if Path(exe) == Path(sys.executable):
            proc = subprocess.Popen([exe, str(sleep_script)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            proc = subprocess.Popen([exe], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        print("pid=%d" % proc.pid)
        try:
            time.sleep(1.2)
            hproc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                                    False, proc.pid)
            t("%s OpenProcess 成功" % label, bool(hproc), "h=%r" % hproc)
            if not hproc:
                continue
            try:
                flag = wt.BOOL(0)
                k32.IsWow64Process(hproc, ctypes.byref(flag))
                t("%s 位宽判定正确 (expect 32=%s)" % (label, expect32),
                  bool(flag.value) == expect32, "is32=%s" % bool(flag.value))
                is32 = bool(flag.value)

                # SymInitialize
                dbg.SymSetOptions(0x00000002 | 0x00000004)   # UNDNAME|DEFERRED_LOADS
                # ★ fInvadeProcess = TRUE：让 dbghelp 自己枚举目标已加载模块并建符号表，
                #   否则拿不到 .pdata/FPO 表 ⇒ StackWalk64 第 2 帧就失败（只回 1 帧）。
                okinit = dbg.SymInitialize(hproc, None, True)
                t("%s SymInitialize(invade=TRUE) 成功" % label, bool(okinit),
                  "err=%d" % ctypes.get_last_error())
                try:
                    mods = modules_of(proc.pid)
                    t("%s 枚举到模块" % label, len(mods) > 0, "n=%d" % len(mods))

                    tids = threads_of(proc.pid)
                    t("%s 枚举到线程" % label, len(tids) > 0, "n=%d" % len(tids))

                    best = None
                    for tid in tids[:8]:
                        frames, err = walk_thread(hproc, tid, is32, mods)
                        if frames and len(frames) >= 1:
                            if best is None or len(frames) > len(best[1]):
                                best = (tid, frames)
                        if len(tids) and err:
                            pass
                    t("%s 至少一个线程回溯成功" % label, best is not None)
                    if best:
                        tid, frames = best
                        t("%s 回溯帧数 > 1（真回溯，非单帧）" % label,
                          len(frames) > 1, "tid=%d frames=%d" % (tid, len(frames)))
                        named = [f for f in frames if f["name"]]
                        t("%s 至少一帧能命名到模块+偏移" % label,
                          len(named) > 0, "named=%d/%d" % (len(named), len(frames)))
                        print("    tid=%d 栈（前 8 帧）:" % tid)
                        for i, f in enumerate(frames[:8]):
                            print("      #%d 0x%x  %s" % (i, f["addr"],
                                                          f["name"] or "<unknown>"))
                        t("%s 帧地址全部非零" % label,
                          all(f["addr"] != 0 for f in frames))
                finally:
                    dbg.SymCleanup(hproc)
            finally:
                k32.CloseHandle(hproc)

            t("%s 目标进程仍存活" % label, proc.poll() is None, "poll=%r" % proc.poll())
        finally:
            try:
                proc.terminate(); proc.wait(timeout=5)
                print("已终止目标 rc=%r" % proc.returncode)
            except Exception as e:                      # noqa: BLE001
                print("终止失败: %s" % e)
        # 清理可能残留的挂起（安全断言）
        time.sleep(0.2)

    try:
        sleep_script.unlink()
    except Exception:                                   # noqa: BLE001
        pass

    print("\n" + "=" * 78)
    print("结果：%d 项检查，%d 项失败%s" % (n["v"], len(fails),
                                     "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
