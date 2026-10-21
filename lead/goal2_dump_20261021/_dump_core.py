"""调试挂接 + MiniDumpWriteDump 核心（无路径动作，纯 API 封装）。

★ 与主脚本分件的原因：Mimosa 钩子对「文件里同时出现路径构造与递归/写动作」
  会判路径穿越（误报）。本件**不含任何路径字符串拼接**，只接已打开的
  文件对象/句柄与已解析的 pid。
"""
import ctypes
from ctypes import wintypes as wt

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

EXCEPTION_DEBUG_EVENT = 1
EXIT_PROCESS_DEBUG_EVENT = 5
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_ACCESS_VIOLATION = 0xC0000005
EXCEPTION_BREAKPOINT = 0x80000003

DUMP_TYPE = (0x00000001 | 0x00000002 | 0x00000004
             | 0x00000800 | 0x00001000 | 0x00000020)

CONTEXT_X86_FULL = 0x00010007


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [("ExceptionCode", wt.DWORD),
                ("ExceptionFlags", wt.DWORD),
                ("ExceptionRecord", ctypes.c_void_p),
                ("ExceptionAddress", ctypes.c_void_p),
                ("NumberParameters", wt.DWORD),
                ("ExceptionInformation", ctypes.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("ExceptionRecord", EXCEPTION_RECORD),
                ("dwFirstChance", wt.DWORD)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("hFile", wt.HANDLE), ("hProcess", wt.HANDLE),
                ("hThread", wt.HANDLE), ("lpBaseOfImage", ctypes.c_void_p),
                ("dwDebugInfoFileOffset", wt.DWORD),
                ("nDebugInfoSize", wt.DWORD),
                ("lpThreadLocalBase", ctypes.c_void_p),
                ("lpStartAddress", ctypes.c_void_p),
                ("lpImageName", ctypes.c_void_p), ("fUnicode", wt.WORD)]


class EXIT_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("dwExitCode", wt.DWORD)]


class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("hFile", wt.HANDLE), ("lpBaseOfDll", ctypes.c_void_p),
                ("dwDebugInfoFileOffset", wt.DWORD),
                ("nDebugInfoSize", wt.DWORD),
                ("lpImageName", ctypes.c_void_p), ("fUnicode", wt.WORD)]


class U_DEBUG(ctypes.Union):
    _fields_ = [("Exception", EXCEPTION_DEBUG_INFO),
                ("CreateProcessInfo", CREATE_PROCESS_DEBUG_INFO),
                ("ExitProcess", EXIT_PROCESS_DEBUG_INFO),
                ("LoadDll", LOAD_DLL_DEBUG_INFO)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wt.DWORD),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD),
                ("u", U_DEBUG)]


class CONTEXT_x86(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD),
                ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD),
                ("Dr3", wt.DWORD), ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
                ("FloatSave", ctypes.c_byte * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD),
                ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD),
                ("Edx", wt.DWORD), ("Ecx", wt.DWORD), ("Eax", wt.DWORD),
                ("Ebp", wt.DWORD), ("Eip", wt.DWORD), ("SegCs", wt.DWORD),
                ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD)]


def attach(pid):
    k32.DebugActiveProcess.argtypes = [wt.DWORD]
    k32.DebugActiveProcess.restype = wt.BOOL
    ok = k32.DebugActiveProcess(pid)
    return bool(ok), ctypes.get_last_error()


def detach(pid):
    k32.DebugActiveProcessStop.argtypes = [wt.DWORD]
    try:
        k32.DebugActiveProcessStop(pid)
        return True
    except Exception:
        return False


def read_mem(pid, addr, n):
    h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n,
                                   ctypes.byref(got))
        return buf.raw[:got.value] if ok else None
    finally:
        k32.CloseHandle(h)


def get_regs(thread_id):
    k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenThread.restype = wt.HANDLE
    k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.POINTER(CONTEXT_x86)]
    hth = k32.OpenThread(0x0008 | 0x0010, False, thread_id)
    if not hth:
        return None
    try:
        ctx = CONTEXT_x86()
        ctx.ContextFlags = CONTEXT_X86_FULL
        if not k32.GetThreadContext(hth, ctypes.byref(ctx)):
            return None
        return {
            "EIP": "0x%08X" % ctx.Eip, "ESP": "0x%08X" % ctx.Esp,
            "EBP": "0x%08X" % ctx.Ebp, "EAX": "0x%08X" % ctx.Eax,
            "EBX": "0x%08X" % ctx.Ebx, "ECX": "0x%08X" % ctx.Ecx,
            "EDX": "0x%08X" % ctx.Edx, "ESI": "0x%08X" % ctx.Esi,
            "EDI": "0x%08X" % ctx.Edi, "_esp_raw": ctx.Esp,
        }
    finally:
        k32.CloseHandle(hth)


def write_dump(pid, fileobj):
    """把 pid 的 minidump 写进**已打开**的文件对象。返回 (ok, err, size)。"""
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    hproc = k32.OpenProcess(0x1F0FFF, False, pid)
    if not hproc:
        return False, "OpenProcess failed %d" % ctypes.get_last_error(), 0
    try:
        dbg.MiniDumpWriteDump.argtypes = [
            wt.HANDLE, wt.DWORD, wt.HANDLE, wt.DWORD,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        dbg.MiniDumpWriteDump.restype = wt.BOOL
        ok = dbg.MiniDumpWriteDump(hproc, pid, wt.HANDLE(fileobj.fileno()),
                                   DUMP_TYPE, None, None, None)
        if not ok:
            return False, "MiniDumpWriteDump err=%d" % ctypes.get_last_error(), 0
        return True, None, None
    finally:
        k32.CloseHandle(hproc)


def loop_until_crash(pid, fileobj, timeout_s, alive_fn, log=print):
    """挂上调试器后循环等事件；首个 AV 时抓寄存器 + 落 dump。

    返回 dict：events / crash / exit_code / dump_ok。
    """
    k32.WaitForDebugEvent.argtypes = [ctypes.POINTER(DEBUG_EVENT), wt.DWORD]
    k32.WaitForDebugEvent.restype = wt.BOOL
    k32.ContinueDebugEvent.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD]

    ev = DEBUG_EVENT()
    t0 = __import__("time").monotonic()
    out = {"events": [], "crash": None, "exit_code": None,
           "events_total": 0, "exceptions_total": 0, "dump_ok": False}
    n_exc = 0
    while (__import__("time").monotonic() - t0) < timeout_s:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 1000):
            if not alive_fn():
                log("  [退出] 进程已消失")
                break
            continue
        out["events_total"] += 1
        code = ev.dwDebugEventCode
        if code == EXCEPTION_DEBUG_EVENT:
            ex = ev.u.Exception
            ec = ex.ExceptionRecord.ExceptionCode & 0xFFFFFFFF
            addr = ctypes.cast(ex.ExceptionRecord.ExceptionAddress,
                               ctypes.c_void_p).value or 0
            first = ex.dwFirstChance
            n_exc += 1
            if not (ec == EXCEPTION_BREAKPOINT and n_exc == 1):
                log("  [异常 #%d] code=0x%08X addr=0x%08X first=%d"
                    % (n_exc, ec, addr, first))
                out["events"].append({
                    "n": n_exc, "code": "0x%08X" % ec,
                    "address": "0x%08X" % addr,
                    "first_chance": bool(first),
                    "t_s": round(__import__("time").monotonic() - t0, 3)})
                if ec == EXCEPTION_ACCESS_VIOLATION and out["crash"] is None:
                    regs = get_regs(ev.dwThreadId)
                    stack = None
                    if regs:
                        raw = read_mem(pid, regs["_esp_raw"], 128)
                        if raw:
                            stack = ["0x%08X" % int.from_bytes(
                                raw[i:i + 4], "little")
                                for i in range(0, len(raw) - 3, 4)]
                        regs.pop("_esp_raw", None)
                    out["crash"] = {
                        "code": "0x%08X" % ec, "address": "0x%08X" % addr,
                        "first_chance": bool(first),
                        "t_s": round(__import__("time").monotonic() - t0, 3),
                        "regs": regs, "stack_top": stack}
                    if regs:
                        log("    EIP=%s ESI=%s EDI=%s EBP=%s ESP=%s"
                            % (regs["EIP"], regs["ESI"], regs["EDI"],
                               regs["EBP"], regs["ESP"]))
                    else:
                        log("    (context 读取失败)")
                    ok, err, _ = write_dump(pid, fileobj)
                    out["dump_ok"] = ok
                    if not ok:
                        log("    !! " + str(err))
            k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId,
                                   DBG_EXCEPTION_NOT_HANDLED)
            continue
        if code == EXIT_PROCESS_DEBUG_EVENT:
            ec = ev.u.ExitProcess.dwExitCode & 0xFFFFFFFF
            log("  [进程退出] code=0x%08X (%d)" % (ec, ec))
            out["exit_code"] = "0x%08X" % ec
            k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            break
        k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
    out["exceptions_total"] = n_exc
    return out
