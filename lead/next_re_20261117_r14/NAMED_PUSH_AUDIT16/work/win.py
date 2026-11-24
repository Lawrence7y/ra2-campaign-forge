"""Window dump + RTTI debug helpers."""
import sys
from pe import (BY_ADDR, TEXT_LO, TEXT_HI, u32, read, cstr, fmt, find_imm32_occurrences,
                rtti_of_table, slots_of_table)


def dump(lo, hi):
    print("--- window %08X..%08X ---" % (lo, hi))
    a = lo
    while a < hi:
        i = BY_ADDR.get(a)
        if i is None:
            b = read(a, 1)
            print("   %08X  %-20s DB %s" % (a, (b or b'??').hex(), b))
            a += 1
            continue
        print("   " + fmt(i))
        a += i.size


def rtti_debug(vt):
    print("--- RTTI debug for vt=%08X ---" % vt)
    col = u32(vt - 4)
    print("  [vt-4] = %s" % (("0x%08X" % col) if col is not None else "unread"))
    if col is None:
        return
    print("  [COL+0x00] sig = %s" % (("0x%08X" % u32(col)) if u32(col) is not None else "unread"))
    print("  [COL+0x04] = 0x%08X   [COL+0x08] = 0x%08X   [COL+0x0C] = 0x%08X   [COL+0x10] = 0x%08X" % (
        u32(col + 4) or 0, u32(col + 8) or 0, u32(col + 0xC) or 0, u32(col + 0x10) or 0))
    td = u32(col + 0xC)
    if td:
        print("  TD=%08X  [TD+0x00]=0x%08X [TD+0x04]=0x%08X ncols [TD+0x08]=0x%08X" % (
            td, u32(td) or 0, u32(td + 4) or 0, u32(td + 8) or 0))
        np = u32(td + 8)
        if np:
            print("  name   = %r" % cstr(np, 300))
    print("  raw bytes vt-16..vt+64:")
    b = read(vt - 16, 80)
    print("   ", b.hex() if b else None)


def slots(vt, n=40):
    print("--- slots of vt=%08X ---" % vt)
    for k in range(n):
        p = u32(vt + 4 * k)
        mark = ""
        if p is not None and TEXT_LO <= p < TEXT_HI:
            mark = "  <-- code"
        print("   slot%-3d @%08X = %s%s" % (k, vt + 4 * k, ("%08X" % p) if p is not None else "unread", mark))


def occ(v):
    print("--- occurrences of %08X as dword ---" % v)
    for p in find_imm32_occurrences(v):
        print("   %08X" % p)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "w":
        dump(int(sys.argv[2], 16), int(sys.argv[3], 16))
    elif cmd == "r":
        for a in sys.argv[2:]:
            rtti_debug(int(a, 16))
    elif cmd == "s":
        for a in sys.argv[2:]:
            slots(int(a, 16))
    elif cmd == "o":
        for a in sys.argv[2:]:
            occ(int(a, 16))
