#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W174 dirty-flag write-point scanner.

Goal: full-image scan for writes to byte [reg+0x80] (mov byte [reg+0x80], src).
Dual channel:
  Channel A (primary, ATLAS-INDEPENDENT): linear disasm of entire .text with capstone skipdata=True,
              collect instructions whose op0 is X86_OP_MEM with disp==0x80 and byte size.
  Channel B (cross-check): raw byte-pattern scan for the disp32=0x80 encodings of
              `mov r/m8,imm8` (C6 /0) and `mov r/m8,r8` (88 /r) with mod=10 disp32,
              then verify each candidate is a real instruction boundary by decoding at
              the candidate address; compare set against Channel A.

Site attribution uses FUNCTION INTERVAL CONTAINMENT from function_atlas.tsv (NOT entry_at_or_before).
Writes whose address is inside no atlas interval are flagged ATLAS_GAP / UNATTRIBUTED.

No conclusions are written here; this script only emits raw evidence.
"""
import os
import sys
import json
import struct

import pefile
import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUTDIR = os.path.join(HERE, "..", "EVIDENCE")
os.makedirs(OUTDIR, exist_ok=True)

TARGET_DISP = 0x80

# ---------------- binary ----------------
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SEC = {}
for s in pe.sections:
    name = s.Name.decode(errors="replace").rstrip("\x00")
    va = IB + s.VirtualAddress
    SEC[name] = dict(va=va, vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rawsize=s.SizeOfRawData)
T = SEC[".text"]
TEXT_BYTES = pe.__data__[T["raw"]:T["raw"] + T["rawsize"]]
TEXT_VA = T["va"]

def read_va(va, n):
    for name, s in SEC.items():
        if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
            off = s["raw"] + (va - s["va"])
            return pe.__data__[off:off + n]
    raise ValueError("VA %08X+%d not in any raw section" % (va, n))

# ---------------- atlas (interval containment) ----------------
rows = []
with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
    header = f.readline().rstrip("\n").split("\t")
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        try:
            entry = int(parts[0], 16)
            size = int(parts[1])  # decimal, per §863
        except Exception:
            continue
        rows.append((entry, size, parts))
rows.sort()
intervals = [(e, e + s, e, s) for (e, s, _) in rows]  # (lo, hi, entry, size)
entries_sorted = [e for (e, _, _) in rows]

import bisect
def attribute_site(va):
    """Interval containment: find function whose [entry, entry+size) contains va.
    Scan backwards over a window; do NOT stop early on a short interval, because
    an earlier (larger) function may still contain va (nested/overlapping atlas rows)."""
    los = [iv[0] for iv in intervals]
    i = bisect.bisect_right(los, va) - 1
    # scan backwards over a generous window; pick the closest entry that contains va
    for j in range(i, max(-1, i - 256), -1):
        lo, hi, ent, sz = intervals[j]
        if lo <= va < hi:
            return ent, sz, "interval"
    return None, None, "UNATTRIBUTED"

# ---------------- disasm helpers ----------------
def md(skip=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = skip
    return m

MD = md(True)

def fmt_insn(insn):
    return "%08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)

def mem_info(op):
    return dict(base=op.mem.base, index=op.mem.index, scale=op.mem.scale,
                disp=op.mem.disp, segment=op.mem.segment, size=op.size)

def regname(insn, rid):
    return insn.reg_name(rid) if rid else ""

def classify_src(insn, ops):
    """Return (kind, value) where kind in {imm,reg,mem,other}."""
    if len(ops) < 2:
        return ("none", None)
    s = ops[1]
    if s.type == X86_OP_IMM:
        return ("imm", s.imm)
    if s.type == X86_OP_REG:
        return ("reg", regname(insn, s.reg))
    if s.type == X86_OP_MEM:
        return ("mem", "%s [base=%s index=%s disp=0x%X]" % (
            insn.mnemonic, regname(insn, s.mem.base), regname(insn, s.mem.index), s.mem.disp & 0xFFFFFFFF))
    return ("other", s.type)

def is_byte_write_to_80(insn):
    """True if insn writes a byte to [base+0x80] (op0 is mem, disp==0x80, size==1)."""
    ops = insn.operands
    if not ops:
        return False
    op0 = ops[0]
    if op0.type != X86_OP_MEM:
        return False
    if op0.mem.disp != TARGET_DISP:
        return False
    if op0.size != 1:
        return False
    return True

# ---------------- Channel A: full linear disasm ----------------
writesA = []      # list of dicts
all_disp80 = []   # any instruction referencing mem disp 0x80 (any operand, any size)
n_insn = 0
n_skip = 0
for insn in MD.disasm(TEXT_BYTES, TEXT_VA):
    if insn.id == 0:
        n_skip += insn.size
        continue
    n_insn += 1
    ops = insn.operands
    # collect any mem disp 0x80 reference
    for idx, op in enumerate(ops):
        if op.type == X86_OP_MEM and op.mem.disp == TARGET_DISP:
            all_disp80.append(dict(va=insn.address, op_index=idx, mnemonic=insn.mnemonic,
                                   op_str=insn.op_str, size=op.size,
                                   base=regname(insn, op.mem.base),
                                   index=regname(insn, op.mem.index),
                                   segment=op.mem.segment, id=insn.id))
    if insn.mnemonic == "mov" and is_byte_write_to_80(insn):
        ent, sz, how = attribute_site(insn.address)
        kind, val = classify_src(insn, ops)
        writesA.append(dict(va=insn.address, fn=ent, fn_size=sz, how=how,
                            base=regname(insn, ops[0].mem.base),
                            index=regname(insn, ops[0].mem.index),
                            segment=ops[0].mem.segment,
                            src_kind=kind, src=val,
                            mnemonic=insn.mnemonic, op_str=insn.op_str,
                            insn_bytes=insn.bytes.hex(), size=insn.size))

writesA.sort(key=lambda d: d["va"])

# ---------------- Channel B: raw byte pattern scan ----------------
# We look for the 4-byte disp32 = 80 00 00 00. For each occurrence at raw index p,
# the disp32 starts at VA p+TEXT_VA. Candidate instruction starts:
#   (1) p-2: C6/88, ModRM mod=10, rm != 4 (no SIB)
#   (2) p-3: C6/88, ModRM mod=10 rm==4, SIB byte
#   (3) p-3 with a 1-byte prefix at p-3 and opcode at p-2 (rare)
# For each candidate, decode at that VA and require first insn == mov byte [..+0x80], ..
PAT = bytes([0x80, 0x00, 0x00, 0x00])
prefixes = set([0x2e,0x36,0x3e,0x26,0x64,0x65,0x66,0x67,0xf0,0xf2,0xf3])
candidates = set()
p = 0
while True:
    i = TEXT_BYTES.find(PAT, p)
    if i < 0:
        break
    p = i + 1
    # case 1: opcode at i-2, modrm at i-1, disp at i
    if i >= 2:
        opc = TEXT_BYTES[i-2]; modrm = TEXT_BYTES[i-1]
        if opc in (0xC6, 0x88) and (modrm & 0xC0) == 0x80 and (modrm & 0x07) != 4:
            candidates.add(TEXT_VA + i - 2)
    # case 2: opcode at i-3, modrm at i-2, sib at i-1, disp at i
    if i >= 3:
        opc = TEXT_BYTES[i-3]; modrm = TEXT_BYTES[i-2]; sib = TEXT_BYTES[i-1]
        if opc in (0xC6, 0x88) and (modrm & 0xC0) == 0x80 and (modrm & 0x07) == 4:
            candidates.add(TEXT_VA + i - 3)
    # case 3: prefix at i-3, opcode at i-2, modrm at i-1, disp at i
    if i >= 3:
        pre = TEXT_BYTES[i-3]; opc = TEXT_BYTES[i-2]; modrm = TEXT_BYTES[i-1]
        if pre in prefixes and opc in (0xC6, 0x88) and (modrm & 0xC0) == 0x80 and (modrm & 0x07) != 4:
            candidates.add(TEXT_VA + i - 3)

# verify each candidate by decoding at that exact VA
writesB = []
for va in sorted(candidates):
    try:
        data = read_va(va, 16)
    except Exception:
        continue
    got = None
    for insn in MD.disasm(data, va):
        got = insn
        break
    if got is None or got.address != va:
        continue
    if got.mnemonic != "mov" or not is_byte_write_to_80(got):
        continue
    kind, val = classify_src(got, got.operands)
    writesB.append(dict(va=va, mnemonic=got.mnemonic, op_str=got.op_str,
                        base=regname(got, got.operands[0].mem.base),
                        src_kind=kind, src=val, insn_bytes=got.bytes.hex()))

setA = set(d["va"] for d in writesA)
setB = set(d["va"] for d in writesB)

# ---------------- emit ----------------
def w(path, text):
    with open(os.path.join(OUTDIR, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

lines = []
lines.append("W174 channel A: full .text linear disasm skipdata=True")
lines.append("text_va=%08X text_rawsize=0x%X (0x%X bytes)" % (TEXT_VA, T["rawsize"], T["rawsize"]))
lines.append("insns(decoded)=%d skipped_bytes=%d" % (n_insn, n_skip))
lines.append("channel A mov byte [reg+0x80] writes = %d" % len(writesA))
lines.append("channel B raw-pattern candidates verified = %d" % len(writesB))
lines.append("setA==setB? %s   A_only=%d B_only=%d" % (
    setA == setB, len(setA - setB), len(setB - setA)))
lines.append("A_only addrs: %s" % " ".join("%08X" % x for x in sorted(setA - setB)))
lines.append("B_only addrs: %s" % " ".join("%08X" % x for x in sorted(setB - setA)))
lines.append("")
lines.append("=== per-function counts (interval containment) ===")
from collections import Counter, defaultdict
fncount = Counter(d["fn"] for d in writesA)
fnaddrs = sorted([k for k in fncount if k is not None])
lines.append("distinct functions (attributed) = %d ; unattributed sites = %d" % (
    len(fnaddrs), fncount.get(None, 0)))
for fn in fnaddrs:
    sites = [d for d in writesA if d["fn"] == fn]
    vals = Counter((d["src_kind"], str(d["src"])) for d in sites)
    vstr = ", ".join("%s=%d" % (("%s:%s" % k), v) for k, v in sorted(vals.items()))
    lines.append("fn=%08X size=%-5d n=%-3d vals: %s" % (fn, sites[0]["fn_size"], fncount[fn], vstr))

w("w174_scan_summary.txt", "\n".join(lines) + "\n")

# full write list
wl = []
wl.append("va\tfn\tsrc_kind\tsrc\tbase\tindex\tmnemonic\top_str\tbytes\thow")
for d in writesA:
    wl.append("%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
        d["va"], ("%08X" % d["fn"]) if d["fn"] else "UNATTR",
        d["src_kind"], d["src"], d["base"], d["index"] or "",
        d["mnemonic"], d["op_str"], d["insn_bytes"], d["how"]))
w("w174_writes.tsv", "\n".join(wl) + "\n")

# all mem disp 0x80 references (context for exclusions / non-mov writes)
al = []
al.append("va\top_index\tmnemonic\tsize\tbase\tindex\tsegment\top_str")
for d in sorted(all_disp80, key=lambda x: x["va"]):
    al.append("%08X\t%d\t%s\t%d\t%s\t%s\t%d\t%s" % (
        d["va"], d["op_index"], d["mnemonic"], d["size"], d["base"], d["index"] or "", d["segment"], d["op_str"]))
w("w174_all_disp80.tsv", "\n".join(al) + "\n")

# channel B raw list
bl = []
bl.append("va\tbase\tsrc_kind\tsrc\top_str\tbytes")
for d in writesB:
    bl.append("%08X\t%s\t%s\t%s\t%s\t%s" % (d["va"], d["base"], d["src_kind"], d["src"], d["op_str"], d["insn_bytes"]))
w("w174_channelB_writes.tsv", "\n".join(bl) + "\n")

# write JSON for downstream scripts
with open(os.path.join(OUTDIR, "w174_writes.json"), "w", encoding="utf-8") as f:
    json.dump(dict(n_insn=n_insn, n_skip=n_skip, text_va=TEXT_VA, text_size=T["rawsize"],
                   writesA=writesA, writesB=writesB,
                   setA_only=sorted(setA-setB), setB_only=sorted(setB-setA)),
              f, indent=1)

print("Channel A writes:", len(writesA))
print("Channel B writes:", len(writesB))
print("A==B:", setA == setB, "A_only", len(setA-setB), "B_only", len(setB-setA))
print("Distinct attributed functions:", len(fnaddrs), "unattributed sites:", fncount.get(None,0))
print("Summary written to", os.path.join(OUTDIR, "w174_scan_summary.txt"))
