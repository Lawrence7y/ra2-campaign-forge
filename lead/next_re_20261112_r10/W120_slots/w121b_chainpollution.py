#!/usr/bin/env python3
"""W121b: for every cell chain with >=2 nodes, test EACH node's occupancy of that cell.

Occupancy criterion by type (fixes the W121 defect):
  - BuildingClass (has [+0x520] and [[+0x520]+0xDFC] valid) -> footprint covers the cell
  - otherwise -> (trunc([obj+0x9C]/256), trunc([obj+0xA0]/256)) == cell
READ-ONLY.
"""
import ctypes, struct, sys, time
from ctypes import wintypes as wt

TABLE = 0x0087F924
ROWS = COLS = 512
CELL_A, NODE_NEXT = 0xE4, 0x30
TYPE_DFC, WX, WY = 0xDFC, 0x9C, 0xA0

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n); got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n, ctypes.byref(got)):
            return None
        return b.raw if got.value == n else None

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def trunc_div256(v):
    v &= 0xFFFFFFFF
    if v & 0x80000000:
        v -= 0x100000000
    return v >> 8 if v >= 0 else -((-v) >> 8)


def footprint_of(mem, obj):
    typ = mem.u32(obj + 0x520)
    if not typ:
        return None
    fp = mem.u32(typ + TYPE_DFC)
    if not fp or not (0x10000 < fp < 0x7FFFFFFF):
        return None
    buf = mem.rd(fp, 0x100)
    if not buf:
        return None
    out = []
    for i in range(0, len(buf), 4):
        x, y = struct.unpack_from("<hh", buf, i)
        if x == 0x7FFF and y == 0x7FFF:
            break
        out.append((x, y))
    wx, wy = mem.u32(obj + WX), mem.u32(obj + WY)
    if wx is None or wy is None:
        return None
    ax, ay = trunc_div256(wx), trunc_div256(wy)
    return [(ax + cx, ay + cy) for cx, cy in out]


def occupancy(mem, obj, cell):
    """returns (on_cell, kind)"""
    fp = footprint_of(mem, obj)
    if fp is not None:
        return ((cell in fp), "Building/sub%d" % len(fp))
    wx, wy = mem.u32(obj + WX), mem.u32(obj + WY)
    if wx is None or wy is None:
        return (None, "unreadable")
    return (((trunc_div256(wx), trunc_div256(wy)) == cell), "single")


def main(pid):
    mem = Mem(pid)
    t0 = time.time(); tbl = None
    while time.time() - t0 < 180:
        tbl = mem.u32(TABLE)
        if tbl and tbl > 0x10000:
            break
        time.sleep(0.3)
    if not tbl:
        print("table never appeared"); return 2
    print("pid=%d table=0x%08X" % (pid, tbl))
    blob = mem.rd(tbl, ROWS * COLS * 4)
    entries = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
    seen = set(); chains = 0; viol = 0; two_buildings = 0
    for idx, cell in enumerate(entries):
        if not cell or cell in seen:
            continue
        seen.add(cell)
        h = mem.u32(cell + CELL_A)
        if not h or h < 0x10000:
            continue
        nodes = []; node = h; k = 0; cyc = set()
        while node and node >= 0x10000 and k < 32 and node not in cyc:
            cyc.add(node); nodes.append(node); k += 1
            node = mem.u32(node + NODE_NEXT)
        if len(nodes) < 2:
            continue
        chains += 1
        x, y = idx % COLS, idx // COLS
        info = []
        nbuild = 0
        for nd in nodes:
            on, kind = occupancy(mem, nd, (x, y))
            if kind.startswith("Building"):
                nbuild += 1
            info.append((nd, on, kind))
        off = [t for t in info if t[1] is False]
        if off:
            viol += 1
        if nbuild >= 2:
            two_buildings += 1
        print("  (%3d,%3d) len=%d %s" % (x, y, len(nodes), "VIOLATION" if off else "ok"))
        for nd, on, kind in info:
            print("        0x%08X onCell=%-5s %s" % (nd, on, kind))
    print("\n== SUMMARY: chains>=2 = %d | chains with an OFF-CELL node = %d | chains with >=2 buildings = %d =="
          % (chains, viol, two_buildings))
    if viol:
        print("   -> POLLUTION CONFIRMED: some node does not occupy the cell it is chained on")
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1])))