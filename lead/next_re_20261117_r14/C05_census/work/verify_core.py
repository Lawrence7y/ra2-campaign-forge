#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C05 独立复核核心数字（尽量走不同数据通路），供审计对照。可复跑。

复核：
  CORE1 本片函数数 = coverage_delta.tsv 行数 = atlas[5168:6460] = 1292
  CORE2 high 置信数 = classification_trace.tsv conf==high = coverage_delta 中 (self_known+vtable-core) 判据
  CORE3 三通道 gap：call32 / jmp32 / jmp8（独立重扫 .text 逐条反汇编，按首字节 E8/E9/EB 分类）
         + 疑似真入口 = call32 + 非分支标签 jmp32
"""
import os, sys, json, bisect, re
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C05_census")
WORK = os.path.join(CARD, "work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib
import capstone

# ---- CORE1 ----
cd = os.path.join(CARD, "coverage_delta.tsv")
n_delta = sum(1 for ln in open(cd, encoding="utf-8") if ln.strip())
rows, hdr = audit_lib.load_func_atlas()
n_slice = len(rows[5168:6460])
print("CORE1 本片函数数: coverage_delta=%d  atlas[5168:6460]=%d  match=%s" %
      (n_delta, n_slice, n_delta == n_slice == 1292))

# ---- CORE2 ----
tr = json.load(open(os.path.join(WORK, "classification.json"), encoding="utf-8"))["trace"]
n_high = sum(1 for t in tr if t["conf"] == "high")
src_c = Counter(t["source"] for t in tr)
grade_c = Counter(t["grade"] for t in tr)
# 独立交叉：直接从 classification_trace.tsv 文本数第3列 high
trf = os.path.join(CARD, "EVIDENCE", "classification_trace.tsv")
n_high_file = sum(1 for ln in open(trf, encoding="utf-8") if ln.strip() and ln.split("\t")[2] == "high")
print("CORE2 high 置信数: json=%d  trace-file=%d  match=%s" % (n_high, n_high_file, n_high == n_high_file))
print("       grade=%s  source=%s" % (dict(grade_c), dict(src_c)))
print("       high 分解: self_known=%d + vtable-core=%d" %
      (src_c["self_known"], n_high - src_c["self_known"]))

# ---- CORE3：独立全 .text 重扫（不读 gap_full.json 的 rows 做判定）----
lo, hi = 0x54A290, 0x5CBD1F
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

# 非分支标签 jmp32：从 atlas_gaps.tsv 的 note 反推（独立于 gap_full.json 的 first_mn 字段）
BR_HINT = ("疑函数内分支标签",)
jmp32_bad = set()
for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8"):
    if not ln.strip(): continue
    p = ln.rstrip("\n").split("\t")
    if p[1] == "jmp32" and any(h in p[4] for h in BR_HINT):
        jmp32_bad.add(int(p[0], 16))
jmp32_good = ch_tgt["jmp32"] - jmp32_bad
suspect = ch_tgt["call32"] | jmp32_good

# 与 atlas_gaps.tsv 逐通道行数对比
gap_file = Counter()
for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8"):
    if ln.strip(): gap_file[ln.split("\t")[1]] += 1

print("CORE3 三通道 gap（独立重扫）:")
for ch in ("call32", "jmp32", "jmp8"):
    print("       %-7s rescan=%3d  atlas_gaps.tsv=%3d  match=%s" %
          (ch, len(ch_tgt[ch]), gap_file[ch], len(ch_tgt[ch]) == gap_file[ch]))
print("       jmp32 分支标签(疑函数内) =", len(jmp32_bad), sorted(hex(x) for x in jmp32_bad))
print("       疑似真入口 = call32(%d) + jmp32非分支(%d) = %d ; union=%d" %
      (len(ch_tgt["call32"]), len(jmp32_good), len(ch_tgt["call32"])+len(jmp32_good), len(suspect)))

# 纪律抽检：站点归属用区间包含
assert owner(0x482854) is None, "atlas 空洞站点被错归（R14 §6-17）"
print("       纪律: owner(0x482854)=None (atlas 空洞区间包含判据 OK)")
