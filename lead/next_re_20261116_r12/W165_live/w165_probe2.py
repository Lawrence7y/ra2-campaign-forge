"""W165 探针 v2：在原 5 个读数之外，再采**进程 CPU 时间**（GetProcessTimes 内核+用户）。

为什么要它：本轮实测 ms/frame 全程钉在 32 ms（帧限速地板），
所以"帧时间不变"不能区分「成本本来就不变」与「成本变了但被地板掩盖」。
用 CPU 时间可以直接看"在算多少"。

只读：OpenProcess(VM_READ|QUERY_INFORMATION) + ReadProcessMemory + GetProcessTimes。
"""
import argparse
import ctypes
import json
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

import w165_probe as W

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.GetProcessTimes.argtypes = [wt.HANDLE, ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME),
                                ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]


def ft2ms(ft):
    v = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return v / 10000.0  # 100ns -> ms


def proc_cpu_ms(h):
    c, e, k, u = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return ft2ms(k) + ft2ms(u)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=120.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--out", default="w165v2.ndjson")
    a = ap.parse_args()

    pid = W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = W.Mem(pid)
    h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    print("pid=%d interval=%.3fs secs=%.0f" % (pid, a.interval, a.secs))

    t0 = time.perf_counter()
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        while time.perf_counter() - t0 < a.secs:
            t = time.perf_counter() - t0
            rec = W.snapshot(m)
            rec["t"] = round(t, 4)
            rec["cpu_ms"] = proc_cpu_ms(h)
            f.write(json.dumps(rec) + "\n")
            n += 1
            time.sleep(a.interval)
    k32.CloseHandle(h)
    print("samples=%d -> %s" % (n, a.out))

    rows = [json.loads(l) for l in open(a.out, encoding="utf-8") if json.loads(l).get("cpu_ms")]
    print("  frame: %s -> %s" % (rows[0]["frame"], rows[-1]["frame"]))
    for k in ("objects", "lc_count", "with_loco", "has_target", "moving", "bullets"):
        vals = [r[k] for r in rows if r[k] is not None]
        if vals:
            print("  %-10s min %-4d med %-6.1f max %-4d" % (k, min(vals), sorted(vals)[len(vals) // 2], max(vals)))
    print("  cpu_ms   : %.1f -> %.1f  (Δ%.1f)" % (rows[0]["cpu_ms"], rows[-1]["cpu_ms"],
                                                  rows[-1]["cpu_ms"] - rows[0]["cpu_ms"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
