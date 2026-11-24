#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C07 独立复核核心数字（尽量走不同数据通路），供审计对照。可复跑。

复核：
  CORE1 本片函数数 = coverage_delta.tsv 行数 = atlas[7752:9044] = 1292
  CORE2 high 置信数 = classification_trace.tsv conf==high = (self_known clean + vtable-core)
  CORE3 三通道 gap（独立重扫 .text 逐条反汇编，按首字节 E8/E9/EB 分类）
        + 疑似真入口（R14-R1 严格判据，独立实现：前驱用**原始字节**判据，不依赖 gap_full 的指令表）

独立性说明：
  - CORE3 的通道计数走 audit_lib.sweep_calls？不 —— 这里自己用 capstone 重扫，不 import sweep_calls 结果。
  - 前驱判定用 t 之前的**原始字节**（C3/C2 ret、EB/E9 jmp、90/CC 填充），
    与 gap_full.py 的「指令起点表 + 线性跳过 nop」完全不同实现，互为佐证。
"""
import os, sys, json, bisect, re
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C07_census")
WORK = os.path.join(CARD, "work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib
import capstone

# ---- CORE1 ----
cd = os.path.join(CARD, "coverage_delta.tsv")
n_delta = sum(1 for ln in open(cd, encoding="utf-8") if ln.strip())
rows, hdr = audit_lib.load_func_atlas()
n_slice = len(rows[7752:9044])
print("CORE1 本片函数数: coverage_delta=%d  atlas[7752:9044]=%d  match=%s" %
      (n_delta, n_slice, n_delta == n_slice == 1292))

# ---- CORE2 ----
tr = json.load(open(os.path.join(WORK, "classification.json"), encoding="utf-8"))["trace"]
n_high = sum(1 for t in tr if t["conf"] == "high")
src_c = Counter(t["source"] for t in tr)
grade_c = Counter(t["grade"] for t in tr)
trf = os.path.join(CARD, "EVIDENCE", "classification_trace.tsv")
n_high_file = sum(1 for ln in open(trf, encoding="utf-8") if ln.strip() and ln.split("\t")[2] == "high")
print("CORE2 high 置信数: json=%d  trace-file=%d  match=%s" % (n_high, n_high_file, n_high == n_high_file))
print("       grade=%s  source=%s" % (dict(grade_c), dict(src_c)))
print("       high 分解: self_known=%d + vtable-core=%d" %
      (src_c["self_known"], n_high - src_c["self_known"]))

# ---- CORE3：独立全 .text 重扫 ----
lo, hi = 0x640A40, 0x6BF750
starts = [va for va, _ in rows]
sizes  = {va: int(rec["size"]) for va, rec in rows}
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None

b = audit_lib.Bin()
t = b.text
m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
m.skipdata = True; m.detail = False
data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
ch_tgt = defaultdict(set)
pat = re.compile(r'^0x[0-9A-Fa-f]+$')
for insn in m.disasm(data, t["va"]):
    if insn.id == 0 or insn.mnemonic not in ("call", "jmp") or not pat.match(insn.op_str):
        continue
    tgt = int(insn.op_str, 16)
    if not (lo <= tgt < hi) or owner(tgt) is not None:
        continue
    op0 = insn.bytes[0] if insn.bytes else None
    if insn.mnemonic == "call" and op0 == 0xE8: ch_tgt["call32"].add(tgt)
    elif insn.mnemonic == "jmp" and op0 == 0xE9: ch_tgt["jmp32"].add(tgt)
    elif insn.mnemonic == "jmp" and op0 == 0xEB: ch_tgt["jmp8"].add(tgt)

# ---- 疑似真入口：独立实现（原始字节前驱 + 首指令反汇编 + align16）----
mm = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mm.skipdata = True; mm.detail = False
BRANCH_LIKE = {"test","cmp","je","jne","jz","jnz","jg","jge","jl","jle","ja","jae",
               "jb","jbe","js","jns","jo","jno","jp","jnp","jecxz","loop","loope","loopne","jcxz"}

def first_mn(va):
    try: d = b.read(va, 32)
    except Exception: return "?"
    for insn in mm.disasm(d, va):
        if insn.id == 0: continue
        return insn.mnemonic
    return "?"

def raw_pred_kind(va):
    """独立：仅看 va 之前的原始字节。返回 accept(bool), desc。
       accept = 前一/几条字节构成 ret(C3/C2) / jmp(EB/E9) / 填充(90/CC)。"""
    # 最多回看 8 字节
    n = 8
    p = va - n
    try: back = b.read(p, n)
    except Exception: return False, "unreadable"
    # 紧邻 va 前一字节
    last = back[-1]
    if last == 0xC3:
        return True, "ret(C3)"
    if last == 0xEB:  # 短 jmp，2 字节，前一字节即 opcode，再前一字节是 rel8
        return True, "jmp8(EB)"
    if last == 0xE9:  # 近 jmp，5 字节
        return True, "jmp32(E9)"
    if last in (0x90, 0xCC):  # nop/int3 填充（连续回看）
        k = len(back) - 1
        while k >= 0 and back[k] in (0x90, 0xCC):
            k -= 1
        return True, "pad(90/CC x%d)" % (len(back)-1-k)
    # ret imm16: C2 xx xx —— C2 距 va 3 字节
    if len(back) >= 3 and back[-3] == 0xC2:
        return True, "ret-imm(C2)"
    return False, "last-byte=%02X" % last

all_tgts = set().union(*[ch_tgt[c] for c in ("call32","jmp32","jmp8")])
suspect2 = set()
for tg in all_tgts:
    if tg % 16 != 0: continue
    ok, _ = raw_pred_kind(tg)
    if not ok: continue
    if first_mn(tg) in BRANCH_LIKE: continue
    suspect2.add(tg)

# 从 atlas_gaps.tsv 读「[疑似真入口]」标记集合做对照
suspect_file = set()
for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8"):
    if not ln.strip(): continue
    p = ln.rstrip("\n").split("\t")
    if "[疑似真入口]" in p[4]:
        suspect_file.add(int(p[0], 16))

gap_file = Counter()
for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8"):
    if ln.strip(): gap_file[ln.split("\t")[1]] += 1

print("CORE3 三通道 gap（独立重扫）:")
for ch in ("call32", "jmp32", "jmp8"):
    print("       %-7s rescan=%3d  atlas_gaps.tsv=%3d  match=%s" %
          (ch, len(ch_tgt[ch]), gap_file[ch], len(ch_tgt[ch]) == gap_file[ch]))
print("       total distinct addresses =", len(all_tgts), " rows =", sum(gap_file.values()))
print("CORE3 疑似真入口（R14-R1 严格，独立实现）: recompute=%d  atlas_gaps.tsv标记=%d  match=%s" %
      (len(suspect2), len(suspect_file), suspect2 == suspect_file))
if suspect2 != suspect_file:
    print("       only-recompute:", [hex(x) for x in sorted(suspect2 - suspect_file)])
    print("       only-file:", [hex(x) for x in sorted(suspect_file - suspect2)])

assert owner(0x482854) is None, "atlas 空洞站点被错归（R14 §6-17）"
print("       纪律: owner(0x482854)=None (atlas 空洞区间包含判据 OK)")
