# -*- coding: utf-8 -*-
"""Dump a vtable from gamemd.exe read-only, and resolve each slot to a function
atlas entry. Reuses the v2 slot-counting rule from R11_COMMON 3.1.
Usage: python dumppvt.py <va_hex> [<va_hex> ...]
"""
import sys, json, struct, csv, os

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas")
IB = 0x400000

img = open(EXE, "rb").read()

# section table (hardcoded from PE header read, verified by pe_sections.py output)
SECTIONS = [
    (".text",   0x001000, 0x3DF38D, 0x001000),
    (".rdata",  0x3E1000, 0x030074, 0x3E1000),
    (".data",   0x412000, 0x367BE4, 0x412000),
    (".rsrc",   0x47E000, 0x018128, 0x47E000),
    (".detour", 0x497000, 0x002718, 0x497000),
]
# NOTE: Misc_VirtualSize listed; raw sizes may be smaller but file is not packed for these

CLUSTER_CONSTS = {0x404E0000, 0xA2529D39, 0x3F91DF46}


def rd(va, n=4):
    rva = va - IB
    for name, rva0, vsz, raw in SECTIONS:
        if rva0 <= rva < rva0 + max(vsz, 0x1000):
            off = raw + (rva - rva0)
            if off + n > len(img):
                return None
            return img[off:off + n]
    return None


def dword(va):
    b = rd(va, 4)
    if b is None or len(b) < 4:
        return None
    return struct.unpack("<I", b)[0]


# ---- function atlas: name/size by address ----
funcs = {}
with open(os.path.join(ATLAS, "function_atlas.tsv"), "r", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f, delimiter="\t")
    cols = r.fieldnames
    for row in r:
        try:
            a = int(row["entry"], 16)
        except Exception:
            continue
        funcs[a] = row

# ---- valid COLs ----
vts = json.load(open(os.path.join(ATLAS, "vtables_canonical.json"), encoding="utf-8"))["vtables"]
cols = {}
for v in vts:
    cols.setdefault(v["col"], []).append(v)

# .text range
TEXT_LO, TEXT_HI = IB + 0x1000, IB + 0x1000 + 0x3DF38D


def is_code(p):
    return p is not None and TEXT_LO <= p < TEXT_HI


def resolve(p):
    """attribute a code ptr: exact function start, or nearest preceding start"""
    if p in funcs:
        return p, 0
    best = None
    for a in funcs:
        if a <= p:
            row = funcs[a]
            try:
                size = int(row.get("size") or 0)
            except Exception:
                size = 0
            if a + size > p:
                if best is None or a > best:
                    best = a
    return best, (p - best) if best else None


def dump(va, label=""):
    print("=" * 100)
    print("VTABLE %s  %s" % (hex(va), label))
    print("%-4s %-8s %-10s %-12s %s" % ("slot", "off", "ptr", "func", "note"))
    prev = va
    n = 0
    while True:
        p = dword(va + 4 * n)
        if p is None:
            print("  [end-of-map at slot %d]" % n)
            break
        note = ""
        owner = cols.get(p)
        if p in CLUSTER_CONSTS:
            note = "CLUSTER_CONST -> stop"
            print("%-4d 0x%04X 0x%08X  %-12s %s" % (n, 4 * n, p, "-", note))
            break
        if owner:
            note = "COL for %s (offsets %s) -> stop" % (
                owner[0]["class"], ",".join(str(o["col_offset"]) for o in owner))
            print("%-4d 0x%04X 0x%08X  %-12s %s" % (n, 4 * n, p, "-", note))
            break
        if not is_code(p):
            if p == 0:
                note = "NULL -> stop"
            else:
                note = "non-code non-zero (section %s) -> stop" % sec_of(p)
            print("%-4d 0x%04X 0x%08X  %-12s %s" % (n, 4 * n, p, "-", note))
            break
        fs, delta = resolve(p)
        row = funcs.get(fs, {})
        sz = row.get("size", "?")
        nm = row.get("name", row.get("func", "")) or ""
        print("%-4d 0x%04X 0x%08X  0x%08X   size=%-6s %s%s" % (
            n, 4 * n, p, fs, sz, nm[:40],
            (" +0x%X" % delta) if delta else ""))
        n += 1
        if n > 400:
            print("  [safety cap]")
            break
    print("  slots=%d  end_va=%s" % (n, hex(va + 4 * n)))
    return n


def sec_of(va):
    rva = va - IB
    for name, rva0, vsz, raw in SECTIONS:
        if rva0 <= rva < rva0 + max(vsz, 0x1000):
            return name
    return "?"


# ---- minimal x86 length decoder using capstone to show first insn of whatami slots
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    HAVE_CS = True
except Exception:
    HAVE_CS = False


def show_first(va, nbytes=16):
    b = rd(va, nbytes)
    if b is None or not HAVE_CS:
        return ""
    out = []
    for ins in md.disasm(b, va):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
        break
    return " | ".join(out)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        va = int(a, 16)
        dump(va)
        # print first instruction of each code slot for identification
        print("  -- first insn per code slot --")
        n = 0
        while True:
            p = dword(va + 4 * n)
            if p is None or p in CLUSTER_CONSTS or p in cols or not is_code(p):
                break
            print("   slot%-3d 0x%04X 0x%08X : %s" % (n, 4 * n, p, show_first(p)))
            n += 1
        print()
