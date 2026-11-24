#!/usr/bin/env python3
"""W123: paired read-only sampler. Reads the logic frame counter and a candidate
object-count global, timestamps each frame advance, so we can relate
units-vs-tick-interval WITHIN ONE session (ratio, not absolute rate).

READ-ONLY. No writes, no debugger.
"""
import ctypes, struct, sys, time, statistics
from ctypes import wintypes as wt

FRAME = 0x00A8ED84        # ledger: 32ms logic tick counter
COUNT = 0x00A8E714        # candidate: DAT_00a8b230 + 0x34E4 (compared vs 1/0)
TABLE = 0x0087F924

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n); g = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n, ctypes.byref(g)):
            return None
        return b.raw if g.value == n else None

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def main(pid, secs, out):
    m = Mem(pid)
    t0 = time.time()
    tbl = None
    while time.time() - t0 < 180:
        tbl = m.u32(TABLE)
        if tbl and tbl > 0x10000:
            break
        time.sleep(0.3)
    print("pid=%d table=0x%08X" % (pid, tbl or 0))
    print("sampling %ds  FRAME=0x%08X COUNT=0x%08X" % (secs, FRAME, COUNT))
    rec = open(out, "w", encoding="utf-8") if out else None
    rec and rec.write("t_wall\tframe\tcount\ttable_nonnull\n")
    last = m.u32(FRAME)
    prev_frame_t = time.perf_counter()
    intervals = []           # (interval_ms, count_at_that_time)
    n = 0
    t_start = time.perf_counter()
    cur_count = m.u32(COUNT)
    while time.perf_counter() - t_start < secs:
        f = m.u32(FRAME)
        c = m.u32(COUNT)
        if c is not None:
            cur_count = c
        if f is not None and last is not None and f != last:
            now = time.perf_counter()
            dt = (now - prev_frame_t) * 1000.0
            intervals.append((dt, cur_count))
            prev_frame_t = now
            last = f
            n += 1
            if rec:
                rec.write("%.3f\t%d\t%s\n" % (time.time(), f, cur_count))
        time.sleep(0.002)
    if rec:
        rec.close()
    print("frame advances observed: %d" % n)
    if intervals:
        ds = [d for d, _ in intervals]
        print("interval ms: n=%d mean=%.2f median=%.2f p95=%.2f max=%.2f"
              % (len(ds), statistics.mean(ds), statistics.median(ds),
                 sorted(ds)[int(len(ds) * 0.95)], max(ds)))
        byc = {}
        for d, c in intervals:
            k = (c or 0) // 10 * 10
            byc.setdefault(k, []).append(d)
        print("\ncount_bucket -> n, median_interval_ms")
        for k in sorted(byc):
            v = byc[k]
            print("  %5d -> %4d  %.2f" % (k, len(v), statistics.median(v)))
    return 0


if __name__ == "__main__":
    a = sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a) > 2 else 120.0,
                  a[3] if len(a) > 3 else None))