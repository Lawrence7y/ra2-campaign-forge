# -*- coding: utf-8 -*-
"""W151 v2: whole-.text scan recording BOTH absolute memory operands AND immediate
operands that land in .rdata/.data, so `mov ecx, 0xA8ED40` / `push 0xA8ED40`
(passing &container) is not missed.

Emits work/absref2.tsv: kind<TAB>addr<TAB>section<TAB>func<TAB>site<TAB>insn
  kind = MEM (absolute memory operand) | IMM (immediate operand)
"""
import os, sys, csv, collections, bisect

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas")
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r11\W151_bulletcost\work")
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


from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

funcs = []
with open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        try:
            funcs.append((int(row["entry"], 16), int(row["size"])))
        except Exception:
            pass
funcs.sort()

rows = []
for e, s in funcs:
    off = fileoff(e)
    if off is None:
        continue
    for ins in md.disasm(img[off:off + s], e):
        if ins.address - e >= s:
            break
        seen = set()
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp:
                d = op.mem.disp & 0xFFFFFFFF
                if d >= IB and d not in seen:
                    seen.add(d)
                    rows.append(("MEM", d, secname(d), e, ins.address, ins.mnemonic + " " + ins.op_str))
            elif op.type == X86_OP_IMM:
                d = op.imm & 0xFFFFFFFF
                if d >= IB and d not in seen and secname(d) in (".rdata", ".data"):
                    seen.add(d)
                    rows.append(("IMM", d, secname(d), e, ins.address, ins.mnemonic + " " + ins.op_str))

with open(os.path.join(OUT, "absref2.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("kind\taddr\tsection\tfunc\tsite\tinsn\n")
    for r in rows:
        f.write("%s\t%08x\t%s\t%08x\t%08x\t%s\n" % r)
print("rows", len(rows))
print("distinct data addrs", len(set(r[1] for r in rows)))
