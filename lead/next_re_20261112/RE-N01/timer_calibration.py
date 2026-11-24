# -*- coding: utf-8 -*-
"""RE-N01 / timer_calibration.py —— 宿主机计时器分辨率实测（零真机）。

只查询**本机计时器**：QueryPerformanceFrequency 是对本机 kernel32 的频率查询，
不打开任何目标进程、不 attach、不 ReadProcessMemory、不 SuspendThread。
其余测量全部是 CPython 的 time.perf_counter_ns() / time.monotonic()。

输出：out/timer_calibration_raw.txt
"""
from __future__ import annotations

import ctypes
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "timer_calibration_raw.txt"


def qpc_frequency():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    fn = k32.QueryPerformanceFrequency
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.POINTER(ctypes.c_int64)]
    v = ctypes.c_int64(0)
    ok = fn(ctypes.byref(v))
    return int(ok), int(v.value)


def measure(fn, n=200000, scale=1.0):
    """返回 (最小非零间隔 ns, 非零间隔中位 ns, 非零个数, 零个数)。"""
    prev = fn()
    diffs = []
    zeros = 0
    for _ in range(n):
        cur = fn()
        d = (cur - prev) * scale
        if d > 0:
            diffs.append(d)
        else:
            zeros += 1
        prev = cur
    if not diffs:
        return (None, None, 0, zeros)
    return (min(diffs), statistics.median(diffs), len(diffs), zeros)


def main():
    lines = []
    lines.append("=" * 78)
    lines.append("RE-N01 计时器分辨率实测（零真机；只查询本机计时器）")
    lines.append("python=%s" % sys.version.split()[0])
    lines.append("=" * 78)
    ok, freq = qpc_frequency()
    lines.append("QueryPerformanceFrequency: ok=%d freq=%d Hz" % (ok, freq))
    if freq > 0:
        lines.append("  1 tick = %.9f s = %.3f ns = %.6f us"
                     % (1.0 / freq, 1e9 / freq, 1e6 / freq))
    for label in ("perf_counter", "monotonic", "time"):
        info = time.get_clock_info(label)
        lines.append("time.get_clock_info(%s): resolution=%r s (%.3f ns) "
                     "monotonic=%s adjustable=%s implementation=%r"
                     % (label, info.resolution, info.resolution * 1e9,
                        info.monotonic, info.adjustable, info.implementation))

    n = 200000
    pmin, pmed, pn, pz = measure(time.perf_counter_ns, n)
    lines.append("")
    lines.append("time.perf_counter_ns() 连续 %d 次取样：" % n)
    lines.append("  min_nonzero_delta=%s ns  median_nonzero=%s ns  "
                 "nonzero=%d  zero=%d"
                 % (pmin, pmed, pn, pz))
    pmin2, pmed2, pn2, pz2 = measure(lambda: time.perf_counter(),
                                     n, scale=1e9)
    lines.append("time.perf_counter()   → ns 换算：min_nonzero=%.3f ns  "
                 "median_nonzero=%.3f ns  nonzero=%d  zero=%d"
                 % (pmin2 or float("nan"), pmed2 or float("nan"), pn2, pz2))
    mmin, mmed, mn, mz = measure(lambda: time.monotonic(), n, scale=1e9)
    lines.append("time.monotonic()      → ns 换算：min_nonzero=%.3f ns  "
                 "median_nonzero=%.3f ns  nonzero=%d  zero=%d"
                 % (mmin or float("nan"), mmed or float("nan"), mn, mz))
    lines.append("")
    lines.append("结论口径：")
    lines.append("  * perf_counter_ns() 的**可分辨最小非零间隔**是上面 min_nonzero，")
    lines.append("    不是 1 ns；任何 < 该值的耗时都可能读到 0。")
    lines.append("  * 报告中 _hl_match_14412.json 的 paused_ms=0.0 表示该次耗时")
    lines.append("    **低于当时测量精度 / 被四舍五入到 0.1 ms**，不是零开销。")
    lines.append("  * 因此不能据此声称「采样零扰动」「无挂起开销」，也不能声称")
    lines.append("    亚微秒级逐帧精度；详见 TIMER_CALIBRATION.md / SAMPLER_CONTRACT.md。")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
