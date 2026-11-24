#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C09 独立复核核心数字（第三通道，与通道 B 不同实现），供审计对照。可复跑。

刻意不 import rtti_independent/sweep_independent/gap_full 的判定产物；只用：
  - 原始 function_atlas.tsv
  - 原始 gamemd.exe，经 pefile + capstone(detail=True) + op_str 解析
    （不同于通道 B 的 struct 手解 PE + insn.bytes[0]+struct.unpack rel 算法）
  - 交付产物 coverage_delta.tsv / classification_trace.tsv / atlas_gaps.tsv 仅作对照目标

复核：
  CORE1 本片函数数 = coverage_delta 行数 = atlas[10336:11628] = 1292
  CORE2 high 置信数 = classification_trace.tsv conf==high
  CORE3 三通道 gap：独立全 .text 重扫（op_str 解析目标 + 首字节分类），owner==None
        + 疑似真入口 = R14-R1 严格判据（align16 + prev∈{nop,ret,jmp} + 非分支标签）
"""
import os, bisect, re
import capstone
import pefile
from collections import Counter

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C09_census")
WORK = os.path.join(CARD, "work")
ATLAS_FA = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas", "function_atlas.tsv")
LO, HI = 0x719F30, 0x7734F9

# ---- 自建 PE（pefile，不同于通道 B 的 struct 手解）----
pe = pefile.PE(os.path.join(ROOT, "ra2youli", "gamemd.exe"), fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text")
TVA = IB + sec.VirtualAddress
TDATA = pe.__data__[sec.PointerToRawData:sec.PointerToRawData + sec.SizeOfRawData]

# ---- atlas 区间（独立读）----
lines = open(ATLAS_FA, encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
recs = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]
assert len(recs) == 12916
starts = sorted(int(r["entry"], 16) for r in recs)
size_of = {int(r["entry"], 16): int(r["size"]) for r in recs}


def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + size_of[starts[i]] else None


# ---- CORE1 ----
n_delta = sum(1 for ln in open(os.path.join(CARD, "coverage_delta.tsv"), encoding="utf-8") if ln.strip())
n_slice = len(recs[10336:11628])
print("CORE1 本片函数数: coverage_delta=%d  atlas[10336:11628]=%d  match=%s" %
      (n_delta, n_slice, n_delta == n_slice == 1292))

# ---- CORE2 ----
trf = os.path.join(CARD, "EVIDENCE", "classification_trace.tsv")
tl = open(trf, encoding="utf-8").read().splitlines()
th = tl[0].split("\t")
conf_i = th.index("conf")
n_high = sum(1 for ln in tl[1:] if ln.split("\t")[conf_i] == "high")
grade_i = th.index("grade")
gc = Counter(ln.split("\t")[grade_i] for ln in tl[1:])
print("CORE2 high 置信数: trace-file=%d  grade=%s" % (n_high, dict(gc)))

# ---- CORE3：独立全 .text 重扫 ----
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True; md.skipdata = True
hexpat = re.compile(r'^0x[0-9A-Fa-f]+$')
targets = {"call32": {}, "jmp32": {}, "jmp8": {}}
for ins in md.disasm(TDATA, TVA):
    if ins.id == 0 or ins.mnemonic not in ("call", "jmp"):
        continue
    if not hexpat.match(ins.op_str):
        continue
    tgt = int(ins.op_str, 16)
    if not (LO <= tgt < HI):
        continue
    b0 = ins.bytes[0] if ins.bytes else None
    if ins.mnemonic == "call" and b0 == 0xE8:
        ch = "call32"
    elif ins.mnemonic == "jmp" and b0 == 0xE9:
        ch = "jmp32"
    elif ins.mnemonic == "jmp" and b0 == 0xEB:
        ch = "jmp8"
    else:
        continue
    targets[ch].setdefault(tgt, []).append(ins.address)

gap_file = Counter()
for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8"):
    if ln.strip():
        gap_file[ln.split("\t")[1]] += 1

print("CORE3 三通道 gap（独立重扫，pefile+op_str）:")
for ch in ("call32", "jmp32", "jmp8"):
    tg = [t for t in targets[ch] if owner(t) is None]
    print("       %-7s rescan(ownerNone)=%3d  atlas_gaps.tsv=%3d  match=%s" %
          (ch, len(tg), gap_file[ch], len(tg) == gap_file[ch]))

# ---- 疑似真入口：R14-R1 严格判据，独立重算 ----
md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md2.skipdata = True; md2.detail = False


def read(va, n):
    for s in pe.sections:
        v = IB + s.VirtualAddress
        if v <= va and va + n <= v + max(s.SizeOfRawData, s.Misc_VirtualSize):
            off = s.PointerToRawData + (va - v)
            return pe.__data__[off:off + n]
    raise ValueError


BR = {"test", "cmp", "je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja", "jae", "jb", "jbe",
      "js", "jns", "jo", "jno", "jp", "jnp", "jecxz", "loop", "loope", "loopne", "jcxz"}


def first_mn(va):
    try:
        d = read(va, 32)
    except Exception:
        return ""
    for ins in md2.disasm(d, va):
        if ins.id == 0:
            continue
        return ins.mnemonic
    return ""


def prev_ok(va):
    st = (va - 32) & ~0xF
    try:
        buf = read(st, va - st + 8)
    except Exception:
        return False
    pre = buf[:va - st]
    k = 0
    for c in reversed(pre):
        if c == 0x90:
            k += 1
        else:
            break
    if k >= 2:
        return True
    for ins in md2.disasm(buf, st):
        if ins.id == 0:
            continue
        if ins.address >= va:
            break
        if ins.address + ins.size == va and ins.mnemonic in ("ret", "retn", "jmp"):
            return True
    return False


cands = set()
for ch in ("call32", "jmp32"):
    for t in targets[ch]:
        if owner(t) is None:
            cands.add(t)
suspect = set()
for t in cands:
    if (t % 16 == 0) and prev_ok(t) and (first_mn(t) not in BR):
        suspect.add(t)
print("CORE3 疑似真入口(R14严格): align16+prev{nop,ret,jmp}+非分支 = %d" % len(suspect))
print("       suspects:", ",".join("%08X" % s for s in sorted(suspect)))
assert owner(0x482854) is None, "atlas 空洞站点被错归（R14 §6-17）"
print("       纪律: owner(0x482854)=None OK")
