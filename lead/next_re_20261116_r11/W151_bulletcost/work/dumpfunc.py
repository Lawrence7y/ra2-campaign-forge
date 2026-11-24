# -*- coding: utf-8 -*-
"""W151: disassemble an address range / named functions from gamemd.exe (read-only).
Usage:
  python dumpfunc.py fn 0x466380 0x466560            # whole functions (size from atlas)
  python dumpfunc.py range 0x466380 0x4664C0         # explicit range
  python dumpfunc.py raw 0xA8ED3C 0x40               # raw bytes/dwords in file image
"""
import os, sys, csv, struct, bisect

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas")
IB = 0x400000
SECTIONS = [(".text", 0x001000, 0x3DF38D, 0x001000),
            (".rdata", 0x3E1000, 0x030074, 0x3E1000),
            (".data", 0x412000, 0x367BE4, 0x412000),
            (".rsrc", 0x47E000, 0x018128, 0x47E000),
            (".detour", 0x497000, 0x002718, 0x497000)]
img = open(EXE, "rb").read()


def fileoff(va):
    rva = va - IB
    for name, rva0, vsz, raw in SECTIONS:
        if rva0 <= rva < rva0 + vsz:
            return raw + (rva - rva0)
    return None


def secname(va):
    rva = va - IB
    for name, rva0, vsz, raw in SECTIONS:
        if rva0 <= rva < rva0 + vsz:
            return name
    return "?"


funcs = {}
starts = []
with open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        try:
            e = int(row["entry"], 16); s = int(row["size"])
        except Exception:
            continue
        funcs[e] = (s, row)
starts = sorted(funcs)


def containing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    e = starts[i]
    s = funcs[e][0]
    return (e, s) if e <= va < e + s else None


from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def dis(lo, hi, annotate=True):
    off = fileoff(lo)
    n = hi - lo
    code = img[off:off + n]
    for ins in md.disasm(code, lo):
        if ins.address >= hi:
            break
        ann = ""
        if annotate:
            bits = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp:
                    d = op.mem.disp & 0xFFFFFFFF
                    bits.append("[%s %s]" % (hex(d), secname(d)))
                if op.type == X86_OP_IMM:
                    t = op.imm
                    if t >= IB and secname(t) == ".text":
                        c = containing(t)
                        if c and c[0] == t:
                            bits.append("->fn_%08x(size=%d)" % (t, c[1]))
            ann = "   ; " + " ".join(bits) if bits else ""
        print("%08x  %-30s %-32s%s" % (ins.address, ins.bytes.hex(),
                                       ins.mnemonic + " " + ins.op_str, ann))


def rawdump(lo, n):
    off = fileoff(lo)
    b = img[off:off + n]
    for i in range(0, n, 16):
        chunk = b[i:i + 16]
        hexs = " ".join("%02x" % c for c in chunk)
        dws = []
        for j in range(0, len(chunk), 4):
            if j + 4 <= len(chunk):
                dws.append("%08X" % struct.unpack("<I", chunk[j:j + 4])[0])
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        print("%08x  %-47s  %-35s  %s" % (lo + i, hexs, " ".join(dws), txt))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "fn":
        for a in sys.argv[2:]:
            va = int(a, 16)
            if va not in funcs:
                c = containing(va)
                print("!! %s is not a function entry; containing=%s" % (a, c))
                continue
            s = funcs[va][0]
            print("=" * 110)
            print("FUNCTION %08x  size=%d  end=%08x" % (va, s, va + s))
            dis(va, va + s)
    elif mode == "range":
        lo, hi = int(sys.argv[2], 16), int(sys.argv[3], 16)
        print("=" * 110)
        print("RANGE %08x..%08x" % (lo, hi))
        dis(lo, hi)
    elif mode == "raw":
        rawdump(int(sys.argv[2], 16), int(sys.argv[3], 16))
