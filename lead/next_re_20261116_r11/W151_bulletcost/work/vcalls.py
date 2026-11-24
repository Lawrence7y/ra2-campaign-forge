# -*- coding: utf-8 -*-
"""W151: find all virtual-dispatch call sites for a given vtable byte offset.
Scans every atlas function with capstone, records `call dword ptr [reg + DISP]`.
Usage: python vcalls.py 0x5c [0x114 ...]
Output: stdout, one line per (site, func, insn), grouped by disp.
"""
import os, sys, csv, collections

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


from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_INS_CALL
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

want = set(int(a, 16) for a in sys.argv[1:])
funcs = []
with open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        try:
            funcs.append((int(row["entry"], 16), int(row["size"])))
        except Exception:
            pass

hits = collections.defaultdict(list)
for e, s in sorted(funcs):
    off = fileoff(e)
    if off is None:
        continue
    for ins in md.disasm(img[off:off + s], e):
        if ins.address - e >= s:
            break
        if ins.id != X86_INS_CALL:
            continue
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.disp in want:
                hits[op.mem.disp].append((e, ins.address, ins.mnemonic + " " + ins.op_str))
for d in sorted(hits):
    print("### disp=%s  sites=%d  funcs=%d" % (hex(d), len(hits[d]), len(set(h[0] for h in hits[d]))))
    for e, site, txt in sorted(hits[d]):
        print("   func=%08x site=%08x  %s" % (e, site, txt))
