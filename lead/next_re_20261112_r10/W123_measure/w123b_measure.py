#!/usr/bin/env python3
"""W123b: two-tier read-only sampler.
 high freq: frame counter 0x00A8ED84 -> tick intervals
 low freq : census of cell-chain nodes (proxy for registered entity count)
Pairs each tick interval with the most recent census. READ-ONLY.
"""
import ctypes, struct, sys, time, statistics
from ctypes import wintypes as wt

FRAME = 0x00A8ED84
TABLE = 0x0087F924
ROWS = COLS = 512
CELL_A, NODE_NEXT = 0xE4, 0x30

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")
        self.fails = 0

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n); g = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n, ctypes.byref(g)) or g.value != n:
            self.fails += 1
            return None
        return b.raw

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def census(mem, tbl):
    """returns (n_cells_nonempty, n_nodes)"""
    blob = mem.rd(tbl, ROWS * COLS * 4)
    if blob is None:
        return None
    ent = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
    seen = set(); ncell = 0; nnode = 0
    for cell in ent:
        if not cell or cell in seen:
            continue
        seen.add(cell)
        h = mem.u32(cell + CELL_A)
        if not h or h < 0x10000:
            continue
        ncell += 1
        node = h; k = 0; cyc = set()
        while node and node >= 0x10000 and k < 32 and node not in cyc:
            cyc.add(node); k += 1; nnode += 1
            node = mem.u32(node + NODE_NEXT)
    return (ncell, nnode)


def main(pid, secs, out):
    m = Mem(pid)
    t0 = time.time(); tbl = None
    while time.time() - t0 < 180:
        tbl = m.u32(TABLE)
        if tbl and tbl > 0x10000:
            break
        time.sleep(0.3)
    print("pid=%d table=0x%08X" % (pid, tbl or 0))
    f = open(out, "w", encoding="utf-8") if out else None
    if f:
        f.write("t_wall\tframe\tncell\tnnode\n")
    last = m.u32(FRAME)
    prev = time.perf_counter()
    cur_cell, cur_node = 0, 0
    last_census = 0.0
    samples = []      # (interval_ms, nnode)
    n = 0
    t_start = time.perf_counter()
    while time.perf_counter() - t_start < secs:
        fr = m.u32(FRAME)
        nowp = time.perf_counter()
        if fr is not None and last is not None and fr != last:
            dt = (nowp - prev) * 1000.0
            samples.append((dt, cur_node))
            prev = nowp
            last = fr
            n += 1
            if f:
                f.write("%.3f\t%d\t%d\t%d\n" % (time.time(), fr, cur_cell, cur_node))
        if nowp - last_census > 6.0:
            t_c = time.perf_counter()
            c = census(m, tbl)
            if c:
                cur_cell, cur_node = c
                last_census = time.perf_counter()
                print("  census @%.1fs cells=%d nodes=%d (cost %.1f ms)"
                      % (time.perf_counter() - t_start, cur_cell, cur_node,
                         (last_census - t_c) * 1000.0))
        time.sleep(0.002)
    if f:
        f.close()
    print("frame advances: %d" % n)
    if samples:
        ds = [d for d, _ in samples]
        print("interval ms: mean=%.2f median=%.2f p95=%.2f max=%.1f"
              % (statistics.mean(ds), statistics.median(ds),
                 sorted(ds)[int(len(ds) * .95)], max(ds)))
        by = {}
        for d, nn in samples:
            by.setdefault(nn // 100 * 100, []).append(d)
        print("\nnnodes_bucket -> samples, median_interval_ms, mean_ms")
        for k in sorted(by):
            v = by[k]
            print("  %6d -> %5d   med=%.2f  mean=%.2f" % (k, len(v), statistics.median(v), statistics.mean(v)))
    return 0


if __name__ == "__main__":
    a = sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a) > 2 else 120.0, a[3] if len(a) > 3 else None))