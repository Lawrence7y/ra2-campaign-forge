#!/usr/bin/env python3
"""W121: does a chain's 2nd node actually occupy that cell? (closes the last [unproven] item)

For every cell whose chain A has >=2 nodes, print:
  cell coords | head obj | 2nd obj | head footprint covers cell? | 2nd footprint covers cell?
READ-ONLY.
"""
import ctypes, struct, sys, time
from ctypes import wintypes as wt

TABLE = 0x0087F924
ROWS = COLS = 512
CELL_A, NODE_NEXT = 0xE4, 0x30
TYPE_DFC = 0xDFC
WX, WY = 0x9C, 0xA0

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


def coords_of(mem, obj):
    typ = mem.u32(obj + 0x520)
    if not typ:
        return None, None
    fp = mem.u32(typ + TYPE_DFC)
    if not fp or not (0x10000 < fp < 0x7FFFFFFF):
        return None, typ
    buf = mem.rd(fp, 0x100)
    if not buf:
        return None, typ
    out = []
    for i in range(0, len(buf), 4):
        if i + 4 > len(buf):
            break
        x, y = struct.unpack_from("<hh", buf, i)
        if x == 0x7FFF and y == 0x7FFF:
            break
        out.append((x, y))
    wx = mem.u32(obj + WX)
    wy = mem.u32(obj + WY)
    if wx is None or wy is None:
        return None, typ
    ax, ay = trunc_div256(wx), trunc_div256(wy)
    return ([(ax + cx, ay + cy) for cx, cy in out], (ax, ay)), typ


def main(pid):
    mem = Mem(pid)
    t0 = time.time()
    tbl = None
    while time.time() - t0 < 180:
        tbl = mem.u32(TABLE)
        if tbl and tbl > 0x10000:
            break
        time.sleep(0.3)
    if not tbl:
        print("table never appeared"); return 2
    print("pid=%d table=0x%08X" % (pid, tbl))
    blob = mem.rd(tbl, ROWS * COLS * 4)
    if not blob:
        print("table unreadable"); return 2
    entries = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
    seen = set()
    multi = 0
    verdict_polluted = verdict_ok = 0
    rows = []
    for idx, cell in enumerate(entries):
        if not cell or cell in seen:
            continue
        seen.add(cell)
        h = mem.u32(cell + CELL_A)
        if not h or h < 0x10000:
            continue
        nx = mem.u32(h + NODE_NEXT)
        if not nx or nx < 0x10000:
            continue
        multi += 1
        x, y = idx % COLS, idx // COLS
        hf, _ = coords_of(mem, h)
        nf, _ = coords_of(mem, nx)
        head_ok = hf is not None and (x, y) in hf
        next_ok = nf is not None and (x, y) in nf
        if head_ok and next_ok:
            verdict_ok += 1
            tag = "BOTH-ON-CELL (legit multi-occupant)"
        elif head_ok and not next_ok:
            verdict_polluted += 1
            tag = "*** POLLUTED: 2nd node is NOT on this cell ***"
        else:
            tag = "head not on cell (unexpected)"
        rows.append((x, y, h, nx, head_ok, next_ok, tag))
    print("cells with chain len>=2 : %d" % multi)
    for x, y, h, nx, ho, no, tag in rows[:24]:
        print("  (%3d,%3d) head=0x%08X next=0x%08X headOnCell=%-5s nextOnCell=%-5s %s"
              % (x, y, h, nx, ho, no, tag))
    print("\n== VERDICT: legit=%d  POLLUTED=%d ==" % (verdict_ok, verdict_polluted))
    if verdict_polluted:
        print("   -> A->next points to an object that does NOT occupy that cell")
        print("   -> confirms the single-`next`-shared-across-chains defect (S685)")
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1])))