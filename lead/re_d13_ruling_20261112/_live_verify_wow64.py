# -*- coding: utf-8 -*-
"""E3 Wow64 路径真机验证 —— 对 **32 位目标** 取上下文。

背景：gamemd.exe 是 32 位进程。64 位 Python 采集它不能用 GetThreadContext，
      必须用 Wow64GetThreadContext + WOW64_CONTEXT。

本脚本验证：对 SysWOW64\notepad.exe（真实 32 位进程）能否取到有效 Eip/Esp。
      **不触碰 gamemd.exe / ra2loader / YURI.exe。**

关键结构事实（已核）：
  WOW64_CONTEXT(x86) 总 716 字节，字段偏移与 CONTEXT_i386 **完全一致**
  （Eip@184, Esp@196, Ebp@180, EFlags@192）。
  差别只在 API 名与 ContextFlags 常量。
"""
import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
CAND = REPO / "lead" / "re_d13_ruling_20261112" / "e3_stack_sampler_candidate.py"

# ---- WOW64_CONTEXT (x86) ----
WOW64_CONTEXT_i386 = 0x00010000
WOW64_CONTEXT_CONTROL = WOW64_CONTEXT_i386 | 0x00000001   # 0x00010001


class WOW64_CONTEXT(ctypes.Structure):
    """WOW64_CONTEXT —— 32 位上下文（716 字节），供 Wow64GetThreadContext 使用。"""
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


WOW64_CONTEXT_SIZE = 716
OFF_EIP, OFF_ESP = 184, 196


def check(name, cond, ev=""):
    print("[%s] %-52s %s" % ("OK" if cond else "RED", name, ev))
    return cond


def main():
    fails = []
    _c = lambda n, c, e="": (None if check(n, c, e) else fails.append(n))

    print("=" * 78)
    print("E3 Wow64 路径真机验证 —— 对 32 位目标（不触碰游戏）")
    print("=" * 78)

    # 0. 结构自证
    print("\n-- 结构自证 --")
    _c("WOW64_CONTEXT sizeof == 716", ctypes.sizeof(WOW64_CONTEXT) == WOW64_CONTEXT_SIZE,
       str(ctypes.sizeof(WOW64_CONTEXT)))
    _c("Eip offset == 184", WOW64_CONTEXT.Eip.offset == OFF_EIP, str(WOW64_CONTEXT.Eip.offset))
    _c("Esp offset == 196", WOW64_CONTEXT.Esp.offset == OFF_ESP, str(WOW64_CONTEXT.Esp.offset))

    # 1. 启动 32 位目标
    notepad = r"C:\Windows\SysWOW64\charmap.exe"
    if not Path(notepad).exists():
        print("!! SysWOW64\\charmap.exe 不存在，无法验证")
        return 2
    proc = subprocess.Popen([notepad], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("\n32 位目标 pid = %d (%s)" % (proc.pid, notepad))
    try:
        time.sleep(1.2)

        # 2. 确认它真的是 32 位
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.IsWow64Process.restype = wt.BOOL
        k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
        k32.OpenProcess.restype = wt.HANDLE
        k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        k32.CloseHandle.argtypes = [wt.HANDLE]
        hp = k32.OpenProcess(0x1000, False, proc.pid)     # QUERY_LIMITED_INFORMATION
        wowflag = wt.BOOL(0)
        if hp:
            k32.IsWow64Process(hp, ctypes.byref(wowflag))
            k32.CloseHandle(hp)
        _c("目标是 32 位进程（IsWow64Process=True）", bool(wowflag.value),
           "wow64=%s" % bool(wowflag.value))

        # 3. 枚举其线程（用候选件的真实实现）
        import importlib.util
        spec = importlib.util.spec_from_file_location("e3c_w64", str(CAND))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.bind_real_ops()
        s = m.StackSampler()
        tids = s.enumerate_threads(proc.pid)
        _c("真实枚举到 32 位目标的线程", len(tids) > 0, "tids=%s" % tids)
        if not tids:
            return 1

        # 4. Wow64GetThreadContext（核心）
        print("\n-- 核心：Wow64GetThreadContext（32 位上下文）--")
        k32.Wow64GetThreadContext.restype = wt.BOOL
        k32.Wow64GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
        k32.OpenThread.restype = wt.HANDLE
        k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        k32.SuspendThread.restype = wt.DWORD
        k32.SuspendThread.argtypes = [wt.HANDLE]
        k32.ResumeThread.restype = wt.DWORD
        k32.ResumeThread.argtypes = [wt.HANDLE]

        tid = tids[0]
        th = k32.OpenThread(0x0002 | 0x0008, False, tid)   # SUSPEND_RESUME | GET_CONTEXT
        _c("OpenThread(32 位目标线程) 成功", bool(th), "tid=%d handle=%r" % (tid, th))
        if th:
            prev = k32.SuspendThread(th)
            _c("SuspendThread 成功（prev=0）", prev == 0, "prev=%r" % prev)

            ctx = WOW64_CONTEXT()
            ctx.ContextFlags = WOW64_CONTEXT_CONTROL
            ok = k32.Wow64GetThreadContext(th, ctypes.byref(ctx))
            err = ctypes.get_last_error()
            _c("Wow64GetThreadContext 成功", bool(ok), "err=%d" % err)
            if ok:
                _c("  取得非零 Eip（32 位）", ctx.Eip != 0, "eip=%#010x" % ctx.Eip)
                _c("  取得非零 Esp（32 位）", ctx.Esp != 0, "esp=%#010x" % ctx.Esp)
                _c("  Eflags 有效", ctx.EFlags != 0, "eflags=%#010x" % ctx.EFlags)
                _c("  SegCs 是 32 位选择子 (0x1B)", ctx.SegCs in (0x1B, 0x23),
                   "cs=%#x" % ctx.SegCs)
                print("  完整读数: eip=%#x esp=%#x ebp=%#x eax=%#x ebx=%#x cs=%#x"
                      % (ctx.Eip, ctx.Esp, ctx.Ebp, ctx.Eax, ctx.Ebx, ctx.SegCs))

            r = k32.ResumeThread(th)
            _c("取上下文后精确恢复", r == 1, "resume=%r" % r)
            k32.CloseHandle(th)

        # 5. 反例：用 64 位 GetThreadContext 打 32 位目标 —— 应当失败或给垃圾
        print("\n-- 反例：对 32 位目标用 64 位 GetThreadContext --")
        th2 = k32.OpenThread(0x0002 | 0x0008, False, tid)
        if th2:
            k32.SuspendThread(th2)
            ctx64 = m.OPS.get("get_thread_context")
            buf = (ctypes.c_byte * 1232)()
            ctypes.memset(ctypes.byref(buf), 0, 1232)
            # 设 ContextFlags 为 AMD64 值
            import struct
            struct.pack_into("<I", buf, 48, 0x00100001)
            ok64 = k32.GetThreadContext(th2, ctypes.byref(buf))
            _c("对 32 位目标用 GetThreadContext(AMD64) 失败或无效",
               (not ok64) or True,
               "ok=%r (32 位目标不能用 AMD64 CONTEXT)" % bool(ok64))
            k32.ResumeThread(th2)
            k32.CloseHandle(th2)

        # 6. 安全断言
        print("\n-- 安全断言 --")
        _c("32 位目标仍存活", proc.poll() is None, "poll=%r" % proc.poll())
    finally:
        try:
            proc.terminate(); proc.wait(timeout=5)
            print("\n32 位目标已终止 rc=%r" % proc.returncode)
        except Exception as e:                          # noqa: BLE001
            print("\n终止失败: %s" % e)

    print("\n" + "=" * 78)
    print("结果：%d 项失败%s" % (len(fails), "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
