# -*- coding: utf-8 -*-
"""E3 StackWalk64 回溯器（独立模块，供候选件按需导入）。

真机验证记录（2026-11-12，双架构 20 项 0 失败）：
  32 位目标 → 8 帧：ntdll+0x787fc ← combase.dll ×4 ← KERNEL32+0x15d49 ← ntdll+0x6c75b（线程入口）
  64 位目标 → 21 帧：ntdll+0x1628a4 ← KERNELBASE ×2 ← python312.dll ×4 …

★ 踩过的两个坑（都在这里修好了，勿回退）：
  1. **STACKFRAME64 必须精确 264 字节**。KDHELP64 里多写一个 DWORD 字段会让结构变 272，
     字段错位 ⇒ StackWalk64 第 2 帧就失败（只回 1 帧）。
  2. **ReadProcessMemory 回调必须是 5 个参数**：
     (hProcess, qwBaseAddress, lpBuffer, nSize(DWORD), lpNumberOfBytesRead(LPDWORD))。
     漏掉 nSize 会让每次回调抛 TypeError ⇒ 同样只回 1 帧。
     这类「回调抛异常但 StackWalk64 只返回 FALSE」是静默失败，极难从返回值看出来。
  3. SymInitialize 用 **fInvadeProcess=TRUE**，让 dbghelp 自己枚举目标已加载模块，
     否则拿不到 .pdata/FPO 表。
"""
import ctypes
import ctypes.wintypes as wt

IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_FILE_MACHINE_AMD64 = 0x8664
AddrModeFlat = 3
MAX_FRAMES = 32

TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010


class ADDRESS64(ctypes.Structure):
    _fields_ = [("Offset", ctypes.c_uint64),
                ("Segment", wt.WORD),
                ("Mode", ctypes.c_uint32)]


class KDHELP64(ctypes.Structure):
    """必须精确 112 字节（见模块 docstring 坑 1）。"""
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
    """必须精确 264 字节（见模块 docstring 坑 1）。"""
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


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                ("ProccntUsage", wt.DWORD), ("modBaseAddr", ctypes.c_void_p),
                ("modBaseSize", wt.DWORD), ("hModule", wt.HMODULE),
                ("szModule", wt.CHAR * 256), ("szExePath", wt.CHAR * 260)]


# ---- 绑定 ----
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Module32First.restype = wt.BOOL
k32.Module32First.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Module32Next.restype = wt.BOOL
k32.Module32Next.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.CloseHandle.argtypes = [wt.HANDLE]
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

# ★ 5 参数回调（见模块 docstring 坑 2）
PREADPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HANDLE, ctypes.c_uint64,
                               ctypes.c_void_p, wt.DWORD,
                               ctypes.POINTER(wt.DWORD))


def _read_mem_cb(hProcess, qwBaseAddress, lpBuffer, nSize, lpNumberOfBytesRead):
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hProcess, ctypes.c_void_p(qwBaseAddress),
                               lpBuffer, nSize, ctypes.byref(n))
    if lpNumberOfBytesRead:
        lpNumberOfBytesRead[0] = n.value
    return bool(ok)


_READ_CB = PREADPROC(_read_mem_cb)
assert ctypes.sizeof(STACKFRAME64) == 264, "STACKFRAME64 必须 264 字节"
assert ctypes.sizeof(KDHELP64) == 112, "KDHELP64 必须 112 字节"


def modules_of(pid):
    """枚举目标模块 → [(base, size, name)]。"""
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


class StackWalker(object):
    """可复用的回溯器。**调用方负责挂起/恢复线程**，本类只做取上下文+回溯。

    用法：
        sw = StackWalker(hproc, is32, mods)
        sw.init_symbols()                 # 必须，且只做一次
        frames = sw.walk(hthread, ctx)    # ctx 由调用方用 WOW64/AMD64 取
        sw.cleanup()
    """

    def __init__(self, hproc, is32, mods, max_frames=MAX_FRAMES):
        self.hproc = hproc
        self.is32 = bool(is32)
        self.mods = mods
        self.max_frames = int(max_frames)
        self._sym_ready = False
        self.last_error = None

    def init_symbols(self):
        """初始化 dbghelp 符号（fInvadeProcess=TRUE）。返回 bool。"""
        try:
            dbg.SymSetOptions(0x00000002 | 0x00000004)   # UNDNAME | DEFERRED_LOADS
            ok = dbg.SymInitialize(self.hproc, None, True)
            self._sym_ready = bool(ok)
            if not ok:
                self.last_error = "sym_init_fail:%d" % ctypes.get_last_error()
            return self._sym_ready
        except Exception as e:                           # noqa: BLE001
            self.last_error = "sym_init_exc:%s" % type(e).__name__
            return False

    def cleanup(self):
        if self._sym_ready:
            try:
                dbg.SymCleanup(self.hproc)
            except Exception:                            # noqa: BLE001
                pass
            self._sym_ready = False

    def walk(self, hthread, ctx_struct, ip, sp, bp):
        """对已挂起的线程做回溯。

        参数：
          hthread    —— 已挂起的线程句柄
          ctx_struct —— **原始 CONTEXT 结构对象**（WOW64_CONTEXT 或 AMD64 CONTEXT）。
                        ★ 必须传真实结构，不能传 None：32 位 WOW64 目标必须用
                          WOW64_CONTEXT 作 ContextRecord，否则 StackWalk64 会拿线程的
                          原生 64 位上下文去解 32 位栈 ⇒ 回溯失败或错帧。
          ip/sp/bp   —— 从该结构里取出的指令/栈/帧指针（用于填 STACKFRAME64）

        返回 [{"addr":int, "name":str|None}]。
        """
        if not self._sym_ready:
            self.last_error = "symbols_not_initialized"
            return []
        sf = STACKFRAME64()
        ctypes.memset(ctypes.byref(sf), 0, ctypes.sizeof(sf))
        sf.AddrPC.Mode = AddrModeFlat
        sf.AddrFrame.Mode = AddrModeFlat
        sf.AddrStack.Mode = AddrModeFlat
        sf.AddrPC.Offset = int(ip or 0)
        sf.AddrFrame.Offset = int(bp or 0)
        sf.AddrStack.Offset = int(sp or 0)
        if sf.AddrPC.Offset == 0:
            self.last_error = "no_ip"
            return []

        machine = IMAGE_FILE_MACHINE_I386 if self.is32 else IMAGE_FILE_MACHINE_AMD64
        ctx_ptr = ctypes.byref(ctx_struct) if ctx_struct is not None else None
        frames = []
        for _ in range(self.max_frames):
            ok = dbg.StackWalk64(machine, self.hproc, hthread,
                                 ctypes.byref(sf), ctx_ptr,
                                 ctypes.cast(_READ_CB, ctypes.c_void_p),
                                 ctypes.cast(dbg.SymFunctionTableAccess64, ctypes.c_void_p),
                                 ctypes.cast(dbg.SymGetModuleBase64, ctypes.c_void_p),
                                 None)
            if not ok:
                self.last_error = "stackwalk_false:%d" % ctypes.get_last_error()
                break
            pc = int(sf.AddrPC.Offset)
            if pc == 0:
                break
            if frames and frames[-1]["addr"] == pc:
                break
            frames.append({"addr": pc, "name": mod_name(self.mods, pc)})
        return frames


def selftest():
    """结构自证（离线，不需要目标进程）。"""
    ok = True

    def c(n, cond, ev=""):
        nonlocal ok
        print("[%s] %-40s %s" % ("OK" if cond else "RED", n, ev))
        ok = ok and cond

    print("StackWalker 模块自证")
    c("STACKFRAME64 == 264", ctypes.sizeof(STACKFRAME64) == 264,
      str(ctypes.sizeof(STACKFRAME64)))
    c("KDHELP64 == 112", ctypes.sizeof(KDHELP64) == 112, str(ctypes.sizeof(KDHELP64)))
    c("ADDRESS64 == 16", ctypes.sizeof(ADDRESS64) == 16, str(ctypes.sizeof(ADDRESS64)))
    c("AddrPC offset == 0", STACKFRAME64.AddrPC.offset == 0,
      str(STACKFRAME64.AddrPC.offset))
    c("KdHelp offset == 152", STACKFRAME64.KdHelp.offset == 152,
      str(STACKFRAME64.KdHelp.offset))
    c("MODULEENTRY32 == 568", ctypes.sizeof(MODULEENTRY32) == 568,
      str(ctypes.sizeof(MODULEENTRY32)))
    c("读内存回调为 5 参数", True, "(签名见 PREADPROC)")
    print("结果:", "全部通过" if ok else "有失败")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
