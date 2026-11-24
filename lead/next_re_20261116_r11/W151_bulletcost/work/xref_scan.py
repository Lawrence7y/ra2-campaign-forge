# -*- coding: utf-8 -*-
"""W151: whole-.text static scan with capstone.

Per function (entry,size from W130 function_atlas.tsv):
  - instruction count
  - back edges (jmp/jcc whose target is inside the function and <= site)  -> loop count
  - loop headers = distinct back-edge targets
  - absolute memory operands (base==0 and index==0)  -> data xrefs
  - direct call targets

Emits:
  work/absref.tsv      addr<TAB>func<TAB>site<TAB>insn
  work/fnloops.tsv     entry<TAB>size<TAB>ninsn<TAB>nedges_back<TAB>nloops<TAB>callers<TAB>callees
Read-only over gamemd.exe.
"""
import os, sys, csv, struct, collections

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


def fileoff(va, n=1):
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
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_INS_CALL, X86_INS_JMP, X86_INS_RET

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

TEXT_LO = IB + 0x1000
TEXT_HI = TEXT_LO + 0x3DF38D

funcs = []
with open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        try:
            e = int(row["entry"], 16)
            s = int(row["size"])
        except Exception:
            continue
        if s <= 0:
            continue
        funcs.append((e, s, row))
funcs.sort()
starts = [e for e, s, r in funcs]
import bisect


def containing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    e, s, r = funcs[i]
    return (e, s, r) if e <= va < e + s else None


absref = collections.defaultdict(list)   # dataaddr -> [(func, site, text)]
fnstat = {}
edges = collections.Counter()   # (caller,callee) count of sites

for e, s, row in funcs:
    off = fileoff(e, s)
    if off is None:
        continue
    code = img[off:off + s]
    ninsn = 0
    nback = 0
    headers = set()
    prev3 = False
    for ins in md.disasm(code, e):
        ninsn += 1
        if ins.address - e >= s:
            break
        # back edge
        if ins.mnemonic.startswith("j") or ins.mnemonic == "loop":
            for op in ins.operands:
                if op.type == X86_OP_IMM:
                    t = op.imm
                    if e <= t < e + s and t <= ins.address:
                        nback += 1
                        headers.add(t)
        # absolute data operand
        for op in ins.operands:
            if op.type == X86_OP_MEM:
                m = op.mem
                if m.base == 0 and m.index == 0 and m.disp != 0:
                    d = m.disp & 0xFFFFFFFF
                    nm = secname(d) if d >= 0x400000 else "?"
                    absref[d].append((e, ins.address, "%s %s [%s=%s]" % (
                        ins.mnemonic, ins.op_str, hex(d), nm)))
        # direct call
        if ins.id == X86_INS_CALL:
            for op in ins.operands:
                if op.type == X86_OP_IMM:
                    c = containing(op.imm)
                    if c:
                        edges[(e, c[0])] += 1
    fnstat[e] = (s, ninsn, nback, len(headers))

with open(os.path.join(OUT, "absref.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("data_addr\tsection\tfunc\tsite\tinsn\n")
    for d in sorted(absref):
        for (fn, site, txt) in absref[d]:
            f.write("%08x\t%s\t%08x\t%08x\t%s\n" % (d, secname(d) if d >= 0x400000 else "?", fn, site, txt))

with open(os.path.join(OUT, "fnloops.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsize\tninsn\tnback\tnloops\n")
    for e, s, row in funcs:
        st = fnstat.get(e)
        if not st:
            continue
        f.write("%08x\t%d\t%d\t%d\t%d\n" % (e, st[0], st[1], st[2], st[3]))

with open(os.path.join(OUT, "edges_scan.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("caller\tcallee\tsites\n")
    for (a, b), n in sorted(edges.items()):
        f.write("%08x\t%08x\t%d\n" % (a, b, n))

print("funcs scanned:", len(fnstat))
print("distinct data addrs:", len(absref))
print("total absref rows:", sum(len(v) for v in absref.values()))
print("call edges:", len(edges))
