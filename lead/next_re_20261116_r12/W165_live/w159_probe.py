#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W159 真机探针：只读内存 + （可选）合成输入。

三个子命令：
  arm    —— 对照臂/观测臂：按固定间隔采 mode/frame/bullets 等计数器，写 NDJSON
  eip    —— EIP 采样：反复读所有 gamemd 线程的 EIP，统计命中若干候选区间的次数
            用于判定 §891-8 的未证项：0x55B8F0（11 路派发阶梯）与 0x7D02BE 到底活不活
  geo    —— DPI-aware 几何读数（每次输入动作前都要重测）

纪律：
  * 只 OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)，只 ReadProcessMemory
  * 不写目标进程内存、不注入 DLL、不 attach 调试器
  * EIP 采样用 GetThreadContext（不 SuspendThread，避免扰动调度）
"""
import argparse
import ctypes
import json
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
u32 = ctypes.windll.user32

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [wt.HANDLE]

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040

G = {
    "frame":   0x00A8ED84,
    "bullets": 0x00A8ED50,
    "mode":    0x00A8B238,
    "abstract": 0x00B0F730,
    "foot":    0x008B3DD0,
    "units":   0x008B4118,
    "infantry": 0x00A83DF8,
    "aircraft": 0x00A8E3A0,
    "building": 0x00A8EB50,
    "techno":  0x00A8EC88,
    "runflag": 0x00ABCE08,     # W157 的一次性写档标志
    "b0b59c":  0x00B0B59C,     # W150 的候选
    "a8db30":  0x00A8DB30,
}

# EIP 命中判定区间（[lo, hi)）——这些是要回答的对象
REGIONS = {
    "orphan_ladder_55B8F0": (0x55B8F0, 0x55BAA0),   # §891-3 的 11 路阶梯（零静态引用）
    "live_dispatch_55AFB0": (0x55AFB0, 0x55B71D),   # 正对照：已知每帧函数
    "perframe_55D360":      (0x55D360, 0x55DF3C),   # 正对照：每帧更新
    "mainloop_48CCC0":      (0x48CCC0, 0x48D000),   # 正对照：主循环
    "orphan_crt_7D02BE":    (0x7D02BE, 0x7D038F),   # §891-8 提到的零引用 CRT 块
    "serialize_67D300":     (0x67D300, 0x67E438),   # W157 判定：只在 mode==0 跑一次
    "ai_bullet_4666E0":     (0x4666E0, 0x467FF2),   # BulletClass::AI
}


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


class Mem:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed err=%d" % ctypes.get_last_error())
        self.buf = ctypes.create_string_buffer(4)
        self.got = ctypes.c_size_t(0)

    def rd(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self.buf, 4, ctypes.byref(self.got)) \
                and self.got.value == 4:
            return struct.unpack("<I", self.buf.raw)[0]
        return None


# ---------- thread EIP sampling ----------
class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD),
                ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
                ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
                ("FloatSave", wt.BYTE * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", wt.BYTE * 512)]


CONTEXT_i386 = 0x00010000
CONTEXT_CONTROL = CONTEXT_i386 | 0x00000001


def list_threads(pid):
    """返回该 pid 的所有线程 id。"""
    TH32CS_SNAPTHREAD = 0x00000004

    class THREADENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                    ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", wt.LONG),
                    ("tpDeltaPri", wt.LONG), ("dwFlags", wt.DWORD)]

    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap == wt.HANDLE(-1).value:
        return []
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(te)
    out = []
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def eip_of(tid):
    """读线程 EIP（32 位线程 ⇒ 必须用 Wow64GetThreadContext）。"""
    h = k32.OpenThread(THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, False, tid)
    if not h:
        return None
    ctx = WOW64_CONTEXT()
    ctx.ContextFlags = CONTEXT_CONTROL
    try:
        if k32.Wow64GetThreadContext(h, ctypes.byref(ctx)):
            return ctx.Eip
        return None
    finally:
        k32.CloseHandle(h)


def cmd_geo(a):
    print("=== DPI-aware geometry ===")
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    hwnds = []

    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == a.pid and u32.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)

    class POINT(ctypes.Structure):
        _fields_ = [("x", wt.LONG), ("y", wt.LONG)]

    for hwnd in hwnds:
        r = wt.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        cl = wt.RECT()
        u32.GetClientRect(hwnd, ctypes.byref(cl))
        pt = POINT(0, 0)
        u32.ClientToScreen(hwnd, ctypes.byref(pt))
        buf = ctypes.create_string_buffer(256)
        u32.GetWindowTextA(hwnd, buf, 256)
        try:
            dpi = u32.GetDpiForWindow(hwnd)
        except Exception:
            dpi = -1
        print("  hwnd=0x%X title=%r" % (hwnd, buf.value.decode("latin-1", "replace")))
        print("      window=(%d,%d) %dx%d   client=(%d,%d) %dx%d   dpi=%s"
              % (r.left, r.top, r.right - r.left, r.bottom - r.top,
                 pt.x, pt.y, cl.right - cl.left, cl.bottom - cl.top, dpi))
    return 0


def cmd_arm(a):
    m = Mem(a.pid)
    rows = []
    t0 = time.perf_counter()
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        while time.perf_counter() - t0 < a.secs:
            t = round(time.perf_counter() - t0, 4)
            rec = {"t": t}
            for k, va in G.items():
                rec[k] = m.rd(va)
            f.write(json.dumps(rec) + "\n")
            n += 1
            time.sleep(a.interval)
    print("samples=%d -> %s" % (n, a.out))
    rows = [json.loads(l) for l in open(a.out, encoding="utf-8")]
    print("  mode set      : %s" % sorted({r["mode"] for r in rows if r["mode"] is not None}))
    print("  frame first/last: %s / %s" % (rows[0]["frame"], rows[-1]["frame"]))
    fr = [r["frame"] for r in rows if r["frame"] is not None]
    print("  frame min/max : %s / %s" % (min(fr), max(fr)))
    bl = [r["bullets"] for r in rows if r["bullets"] is not None]
    if bl:
        print("  bullets min/max/mean: %s / %s / %.2f" % (min(bl), max(bl), sum(bl) / len(bl)))
    print("  runflag set   : %s" % sorted({r["runflag"] for r in rows if r["runflag"] is not None}))
    return 0


def cmd_eip(a):
    m = Mem(a.pid)
    tids = list_threads(a.pid)
    print("threads of pid %d : %s" % (a.pid, tids))
    hits = {k: 0 for k in REGIONS}
    samples = 0
    in_text = 0
    hot = {}
    per_thread = {}
    eip_zero = 0
    TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < a.secs:
        for tid in tids:
            eip = eip_of(tid)
            if eip is None:
                continue
            samples += 1
            per_thread[tid] = per_thread.get(tid, 0) + 1
            if eip == 0:
                eip_zero += 1
                continue
            if TEXT_LO <= eip < TEXT_HI:
                in_text += 1
            hot[eip] = hot.get(eip, 0) + 1
            for name, (lo, hi) in REGIONS.items():
                if lo <= eip < hi:
                    hits[name] += 1
    dur = time.perf_counter() - t0
    print()
    print("EIP samples = %d over %.1f s  (%.0f samples/s)   eip==0: %d"
          % (samples, dur, samples / dur, eip_zero))
    print("EIP inside .text [%08X,%08X) : %d  (%.2f%% of all samples)"
          % (TEXT_LO, TEXT_HI, in_text, 100.0 * in_text / max(1, samples)))
    print("distinct EIP values: %d" % len(hot))
    print()
    print("top 12 hottest EIP:")
    for eip, c in sorted(hot.items(), key=lambda t: -t[1])[:12]:
        tag = [n for n, (lo, hi) in REGIONS.items() if lo <= eip < hi]
        print("   %08X  %8d  %6.2f%%  %s" % (eip, c, 100.0 * c / samples, tag or ""))
    print()
    print("%-26s %-18s %8s %9s" % ("region", "range", "hits", "per-1k"))
    for name, (lo, hi) in REGIONS.items():
        h = hits[name]
        print("%-26s %08X-%08X %8d %9.3f" % (name, lo, hi, h, 1000.0 * h / max(1, samples)))
    print()
    pos = hits["live_dispatch_55AFB0"] + hits["perframe_55D360"] + hits["mainloop_48CCC0"]
    print("verdict:")
    print("  .text 命中率 = %.2f%%  ⇒ %s"
          % (100.0 * in_text / max(1, samples),
             "采样有效" if in_text > 0.01 * samples else "**采样可能无效**"))
    print("  正对照（55AFB0+55D360+48CCC0）命中 = %d（菜单期/等消息期可能为 0，属正常）" % pos)
    print("  orphan_ladder_55B8F0 = %d" % hits["orphan_ladder_55B8F0"])
    print("  orphan_crt_7D02BE    = %d" % hits["orphan_crt_7D02BE"])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["arm", "eip", "geo"])
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--secs", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--out", default="arm.ndjson")
    ap.add_argument("--stop-when-frame", action="store_true")
    a = ap.parse_args()
    if a.pid is None:
        a.pid = pid_of()
        if not a.pid:
            print("gamemd not running")
            return 2
    print("pid = %d" % a.pid)
    return {"arm": cmd_arm, "eip": cmd_eip, "geo": cmd_geo}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
