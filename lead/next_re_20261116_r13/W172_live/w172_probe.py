#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W172 探针：真机 EIP 分桶 + 四个标量。

目的（两个，一次采样同时回答）：
  A. ① 的"98% 预算去哪了"：把每帧 CPU 时间按 EIP 落在哪个已证代码区间来分桶。
  B. ②-b 的 `[+0x81]` 语义：观察目标建筑在建造过程中 [+0x81] / [+0x74] 的变化。

全部只读：OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + ReadProcessMemory
          + Wow64GetThreadContext（32 位线程必须用它）+ GetProcessTimes。
未写目标进程内存、未注入、未 attach 调试器。

EIP 区间（全部来自已证结论，见 R13_COMMON）：
  A* 核心循环   0x429D6D..0x42A3D8   (fn 0x429A90 内的轮体，544 指令)
  寻路链路      0x4D3920, 0x4CBBA0, 0x42C900
  路径推进      0x4B2630, 0x4B0F20
  Drive 本体    0x4B0500..0x4B0AD6
  FootClass::AI 0x4DA530..0x4DAF00
  全对象派发    0x55AFB0..0x55B71D
  每帧更新      0x55D360..0x55DF3C
  CRT/heap     0x7C8B00..0x7D1000  (缓存失效/分配候选)
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
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.GetProcessTimes.argtypes = [wt.HANDLE, ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME),
                                ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]

A_FRAME, A_MODE, A_BULLETS, A_ABSTRACT, A_LOGIC = 0x00A8ED84, 0x00A8B238, 0x00A8ED50, 0x00B0F730, 0x0087F778
OFF_LOCO, OFF_LOCO_TGT, OFF_LOCO_MOVING = 0x674, 0x54, 0x5F

REGIONS = [
    ("astar_core",     0x429D6D, 0x42A3D8),
    ("pathfind_chain", 0x4D3920, 0x4D3F00),
    ("pathfind_sub",   0x4CBBA0, 0x4CBC40),
    ("pathfind_2",     0x42C900, 0x42CCD0),
    ("path_advance",   0x4B2630, 0x4B4740),
    ("drive_body",     0x4B0500, 0x4B0AD6),
    ("loco_misc",      0x4B0F20, 0x4B25B0),
    ("foot_ai",        0x4DA530, 0x4DAF00),
    ("dispatch_all",   0x55AFB0, 0x55B71D),
    ("perframe",       0x55D360, 0x55DF3C),
    ("crt_heap",       0x7C8B00, 0x7D1000),
    ("crashterm_429A90", 0x429A90, 0x42A460),   # 含 astar 的整个函数
]


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


class Mem:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")
        self._b4 = ctypes.create_string_buffer(4)
        self._b1 = ctypes.create_string_buffer(1)
        self._g = ctypes.c_size_t(0)

    def u32(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self._b4, 4, ctypes.byref(self._g)) and self._g.value == 4:
            return struct.unpack("<I", self._b4.raw)[0]
        return None

    def u8(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self._b1, 1, ctypes.byref(self._g)) and self._g.value == 1:
            return self._b1.raw[0]
        return None


class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD), ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD),
                ("Dr3", wt.DWORD), ("Dr6", wt.DWORD), ("Dr7", wt.DWORD), ("FloatSave", wt.BYTE * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", wt.BYTE * 512)]


def list_threads(pid):
    TH32CS_SNAPTHREAD = 0x4

    class TE32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                    ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", wt.LONG),
                    ("tpDeltaPri", wt.LONG), ("dwFlags", wt.DWORD)]

    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    te = TE32()
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
    h = k32.OpenThread(0x0008 | 0x0040, False, tid)
    if not h:
        return None
    ctx = WOW64_CONTEXT()
    ctx.ContextFlags = 0x00010001
    try:
        return ctx.Eip if k32.Wow64GetThreadContext(h, ctypes.byref(ctx)) else None
    finally:
        k32.CloseHandle(h)


def ft2ms(ft):
    return (((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10000.0)


def proc_cpu_ms(h):
    c, e, k, u = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return ft2ms(k) + ft2ms(u)
    return None


def scalars(m):
    rec = dict(frame=m.u32(A_FRAME), mode=m.u32(A_MODE), bullets=m.u32(A_BULLETS),
               objects=m.u32(A_ABSTRACT))
    items = m.u32(A_LOGIC + 4)
    count = m.u32(A_LOGIC + 0x10)
    rec["lc_count"] = count
    moving = with_loco = has_tgt = scanned = 0
    if items and count and 0 < count < 5000:
        for i in range(count):
            obj = m.u32(items + 4 * i)
            scanned += 1
            if not obj:
                continue
            loco = m.u32(obj + OFF_LOCO)
            if not loco:
                continue
            with_loco += 1
            t = m.u32(loco + OFF_LOCO_TGT)
            mv = m.u8(loco + OFF_LOCO_MOVING)
            if t is None or mv is None:
                continue
            if t != 0xFFFFFFFF:
                has_tgt += 1
                if mv != 0:
                    moving += 1
    rec.update(scanned=scanned, with_loco=with_loco, has_target=has_tgt, moving=moving)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=120.0)
    ap.add_argument("--out", default="w172.ndjson")
    ap.add_argument("--eip-burst", type=int, default=400, help="每次标量采样后连续采多少 EIP")
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = Mem(pid)
    ph = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    tids = [t for t in list_threads(pid) if eip_of(t) is not None]
    print("pid=%d threads=%d" % (pid, len(tids)))
    print("first scalars: %s" % json.dumps(scalars(m)))

    t0 = time.perf_counter()
    n = 0
    eip_total = 0
    eip_in_text = 0
    buckets = {name: 0 for name, _, _ in REGIONS}
    with open(a.out, "w", encoding="utf-8") as f:
        while time.perf_counter() - t0 < a.secs:
            t = time.perf_counter() - t0
            rec = scalars(m)
            rec["t"] = round(t, 4)
            rec["cpu_ms"] = proc_cpu_ms(ph)
            # EIP 爆发采样
            cnt = 0
            for _ in range(a.eip_burst):
                for tid in tids:
                    e = eip_of(tid)
                    if e is None:
                        continue
                    cnt += 1
                    eip_total += 1
                    if 0x401000 <= e < 0x7E1000:
                        eip_in_text += 1
                    for name, lo, hi in REGIONS:
                        if lo <= e < hi:
                            buckets[name] += 1
                            break
            rec["eip_n"] = cnt
            f.write(json.dumps(rec) + "\n")
            n += 1
            time.sleep(0.05)
    k32.CloseHandle(ph)
    print("samples=%d -> %s" % (n, a.out))
    print("EIP total=%d  in .text=%d (%.2f%%)"
          % (eip_total, eip_in_text, 100.0 * eip_in_text / max(1, eip_total)))
    print()
    print("%-20s %10s %8s" % ("region", "hits", "per-1e4 (.text)"))
    for name, lo, hi in REGIONS:
        h = buckets[name]
        print("%-20s %10d %8.2f" % (name, h, 10000.0 * h / max(1, eip_in_text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
