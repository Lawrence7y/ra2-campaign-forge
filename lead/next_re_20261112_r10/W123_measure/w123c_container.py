#!/usr/bin/env python3
"""W123c: sample frame counter + container count (0xB0C114) + container base/threshold.
Pairs each tick interval with the container count sampled just before it. READ-ONLY.
"""
import ctypes, struct, sys, time, statistics
from ctypes import wintypes as wt

FRAME = 0x00A8ED84
CONT  = 0x00B0C110
OFF_COUNT, OFF_BASE, OFF_THR = 0x14, 0x08, 0x0C

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n); g = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n, ctypes.byref(g)) or g.value != n:
            return None
        return b.raw

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def main(pid, secs, out):
    m = Mem(pid)
    t0 = time.time()
    while time.time() - t0 < 180:
        if m.u32(FRAME): break
        time.sleep(0.3)
    print("pid=%d sampling %ds" % (pid, secs))
    f = open(out, "w", encoding="utf-8") if out else None
    if f:
        f.write("t_wall\tframe\tcount\tbase\tthr\n")
    last = m.u32(FRAME)
    prev = time.perf_counter()
    samples = []          # (interval_ms, count_sampled_before)
    n = 0
    cur = 0
    t_start = time.perf_counter()
    last_cnt_t = 0.0
    while time.perf_counter() - t_start < secs:
        fr = m.u32(FRAME)
        nown = time.perf_counter()
        if nown - last_cnt_t > 0.05:
            c = m.u32(CONT + OFF_COUNT)
            if c is not None:
                cur = c
            last_cnt_t = nown
        if fr is not None and last is not None and fr != last:
            dt = (nown - prev) * 1000.0
            samples.append((dt, cur))
            prev = nown
            last = fr
            n += 1
            if f:
                f.write("%.4f\t%d\t%d\t%d\t%d\n" % (time.time(), fr, cur,
                        m.u32(CONT + OFF_BASE) or 0, m.u32(CONT + OFF_THR) or 0))
        time.sleep(0.002)
    if f:
        f.close()
    print("frame advances: %d" % n)
    if samples:
        # report container count range
        cs = [c for _, c in samples]
        print("container count: min=%d max=%d last=%d" % (min(cs), max(cs), cs[-1]))
        # correlate within short time windows to avoid time-confound:
        # split into 10s windows, report median count and median/p90 interval per window
        print("\nwin(s)  n   med_count  med_ms  p90_ms")
        W = 10.0
        for wi in range(0, int(secs) // 10 + 1):
            lo, hi = wi * W, (wi + 1) * W
            sub = [s for i, s in enumerate(samples) if lo <= i * (secs / max(1, len(samples))) < hi]
            if len(sub) < 20: continue
            c_med = statistics.median([c for _, c in sub])
            d_med = statistics.median([d for d, _ in sub])
            ds = sorted(d for d, _ in sub)
            p90 = ds[int(len(ds) * .9)]
            print("%5.0f  %5d  %8.0f  %6.2f  %6.2f" % (lo, len(sub), c_med, d_med, p90))
        by = {}
        for d, c in samples:
            by.setdefault(c // 50 * 50, []).append(d)
        print("\ncount_bucket  n     med_ms  p90_ms")
        for k in sorted(by):
            v = sorted(by[k])
            print("%12d %5d  %6.2f  %6.2f" % (k, len(v), statistics.median(v), v[int(len(v)*.9)]))
    return 0


if __name__ == "__main__":
    a = sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a) > 2 else 120.0, a[3] if len(a) > 3 else None))