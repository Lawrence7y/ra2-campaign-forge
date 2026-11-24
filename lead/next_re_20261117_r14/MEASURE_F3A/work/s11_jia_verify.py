# -*- coding: utf-8 -*-
"""MEASURE-F3A step 6: verify the 甲 bucket against bytes (census, not sample -
there are only 2 of them, so sampling >=10 is impossible and a full check is done).

甲 test: does the semantics column's own ③b material re-check against the exe?
We resolve each anchor the text names (member offsets, call targets, call sites).
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE, _MD, OP_MEM, OP_IMM

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
EV = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A\EVIDENCE")
pe = PE(EXE)
atlas = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas[r["entry"].upper()] = int(r["size"])


def body(entry):
    size = atlas[entry]
    code = pe.read(int(entry, 16), size)
    return list(_MD.disasm(code, int(entry, 16))), size


def find_disp(insns, disp):
    """instructions whose memory operand uses this displacement"""
    hit = []
    for ins in insns:
        for op in ins.operands:
            if op.type == OP_MEM and (op.mem.disp & 0xFFFFFFFF) == (disp & 0xFFFFFFFF):
                hit.append("%08X %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return hit


def find_call_imm(insns, target):
    hit = []
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == OP_IMM \
           and ins.operands[0].imm == target:
            hit.append("%08X call %08X" % (ins.address, target))
    return hit


def call_sites_to(target):
    """E8 rel32 scan across .text"""
    out = []
    lo, hi = 0x401000, 0x7D9000
    off = pe.va_to_off(lo)
    data = pe.buf
    for va in range(lo, hi - 5):
        o = pe.va_to_off(va)
        if o is None or o + 5 > len(data):
            continue
        if data[o] == 0xE8:
            rel = int.from_bytes(data[o + 1:o + 5], "little", signed=True)
            if (va + 5 + rel) & 0xFFFFFFFF == target:
                out.append(va)
    return out


def dump_ev(entry, tag):
    insns, size = body(entry)
    p = os.path.join(EV, "%s__%s.txt" % (entry, tag))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("# %s  %s\n# exe ra2youli\\gamemd.exe SHA256 73201CC0...F67476\n"
                 "# body = atlas [entry, entry+%d)\n\n" % (entry, tag, size))
        for ins in insns:
            raw = pe.read(ins.address, ins.size)
            fh.write("%08X  %-24s %-8s %s\n" % (ins.address, raw.hex(" "),
                                                ins.mnemonic, ins.op_str))
    return insns

# ================================================================ 00522340
print("=" * 78)
print("00522340  S10  InfantryClass::ApplyOccupantTargetMissionFallback_behavior")
insns = dump_ev("00522340", "JIA_rowproved")
claims = [
    ("member offset +0x2B4", 0x2B4), ("House flag +0x6E4", 0x6E4),
    ("House flag +0xEC8", 0xEC8), ("House flag +0x6AC", 0x6AC),
    ("vtable slot +0x558", 0x558),
]
for label, d in claims:
    h = find_disp(insns, d)
    print("  %-22s %-28s -> %d hit(s)" % (label, hex(d), len(h)))
    for x in h[:3]:
        print("       %s" % x)
print("  call 0x5B3A00 ->", find_call_imm(insns, 0x5B3A00) or "NOT FOUND in body")
print("  ring3 caller 004D473A:", call_sites_to(0x522340)[:5] or "none")
print("  ring4 ControlledByHuman 0x50B730 ->", find_call_imm(insns, 0x50B730) or "not in body")
print("  ring4 RandomRanged 0x65C7E0 ->", find_call_imm(insns, 0x65C7E0) or "not in body")

# ================================================================ 004C93D0
print("\n" + "=" * 78)
print("004C93D0  S18  FrameCRC_quant_helper")
insns2 = dump_ev("004C93D0", "JIA_rowproved")
for d in (0x388, 0x3A0, 0x10, 0x14):
    h = find_disp(insns2, d)
    print("  disp +%-6s -> %d hit(s)  %s" % (hex(d), len(h), h[:2]))
print("  call sites to 0x4C93D0:", [hex(x) for x in call_sites_to(0x4C93D0)][:8])
print("  caller claimed 0x64DAB0 in those sites:",
      0x64DAB0 in call_sites_to(0x4C93D0))
# is the caller 0x64DAB0 itself calling it?
if 0x64DAB0 in atlas:
    ci, _ = body("0064DAB0")
    print("  0x64DAB0 body calls 0x4C93D0 ->", find_call_imm(ci, 0x4C93D0) or "not found")
