"""Site enumeration for a vtable VA: every instruction in .text whose immediate is that VA,
with the enclosing function, and an atexit/dtors classification probe."""
import sys
from pe import (TEXT_LO, TEXT_HI, u32, read, fmt, dis, win, find_imm32, in_text, MDD,
                func_extent, BY, IMAGEBASE)

ATEXIT = 0x7C978A


def is_imm_operand(i, value):
    for op in i.operands:
        if op.type == 2 and op.imm == value:
            return True
    return False


def insn_with_imm(occ, value):
    """Find a real instruction inside a window whose immediate operand == value."""
    lo, hi = occ - 12, occ + 8
    for base in range(lo, hi):
        b = read(base, 16)
        if b is None:
            break
        for i in MDD.disasm(b, base):
            if i.address > occ:
                break
            if i.id == 0:
                continue
            if is_imm_operand(i, value):
                return i
    return None


def find_func_start(va, back=0x600):
    """Heuristic: walk back for 'int3'/'nop' padding or a known call target."""
    b = read(va - back, back)
    if b is None:
        return None
    # candidate: after CC / C3 padding
    best = None
    for off in range(len(b) - 1):
        if b[off:off + 2] in (b"\xcc\xcc", b"\xc3\xcc", b"\x90\x90"):
            cand = va - back + off + 1
            if cand > (best or 0):
                best = None
                # will refine below by disassembling forward
    return best


def sites(vtva):
    out = []
    for occ in find_imm32(vtva):
        if not in_text(occ):
            out.append(dict(at=occ, kind="DATA", ins=None))
            continue
        i = insn_with_imm(occ, vtva)
        out.append(dict(at=occ, kind="TEXT", ins=i))
    return out


def enclosing(va, maxback=0x2000):
    """Linear-scan back: find the nearest address A such that continuous decoding
    from A reaches va exactly. Practical approximation: scan candidate starts."""
    cands = []
    for back in range(1, maxback):
        a = va - back
        if a < TEXT_LO:
            break
        i = BY.get(a)
        if i is None:
            continue
        # quick reject: many starts decode but not exactly onto va
        ok = False
        cur = a
        n = 0
        while cur < va and n < 4000:
            j = BY.get(cur)
            if j is None:
                break
            cur += j.size
            n += 1
        if cur == va:
            cands.append(a)
    return cands


def shape(entry, name, vtva):
    print("=" * 100)
    print("VT %08X   row %s (%s)" % (vtva, entry, name))
    sl = []
    for k in range(200):
        p = u32(vtva + 4 * k)
        if p is None or not in_text(p):
            break
        sl.append(p)
    print("  slots(%d): %s" % (len(sl), " ".join("%d:%08X" % (k, v) for k, v in enumerate(sl))))
    print("  [sites] every occurrence of %08X in the image:" % vtva)
    for s in sites(vtva):
        print("     %s %08X  %s" % (s["kind"], s["at"], fmt(s["ins"]) if s["ins"] else "(data dword)"))
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    shape(args[0], args[1] if len(args) > 1 else "", int(args[2], 16))
