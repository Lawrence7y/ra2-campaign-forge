"""S10 · 决定性检验：`.data` 区段 0x86E000..0x875000 的 code pointer 在 coverage 里的占比。

判读：
  若该区段是**函数指针表**，其项大多是已被裁定的入口 ⇒ 在 coverage 里命中率高。
  若是 **switch 跳表**，其项是函数体内 case 标签 ⇒ 在 coverage 里几乎 0 命中。
  另与 vtable 槽集（通道 B）交叉：函数指针表的项若同时是虚表槽，也说明它们是函数。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import COVERAGE, EVIDENCE, HERE, load_lines, norm_addr
import s3_channels as s3

img = s3.img
LO, HI = 0x86E000, 0x875000

cov = set()
for ln in load_lines(COVERAGE)[1:]:
    if ln.strip():
        cov.add(int(norm_addr(ln.split("\t")[0]), 16))

chan = __import__("pickle").load(open(os.path.join(HERE, "channels.pkl"), "rb"))
B, A_call, C = chan["B"], chan["A_call"], chan["C"]

region = []
q = LO
while q < HI:
    v = img.u32(q)
    if v is not None and img.in_text(v):
        region.append((q, v))
    q += 4

pts = [v for _, v in region]
uniq = sorted(set(pts))
in_cov = [v for v in uniq if v in cov]
in_B = [v for v in uniq if v in B]
in_call = [v for v in uniq if v in A_call]

# 同区段之外的对照：整个 .data 的 code pointer 在 coverage 的占比
all_data_pts = sorted(chan["C"])
all_in_cov = [v for v in all_data_pts if v in cov]

# 目标是否 16B 对齐 / 是否为硬边界 / 是否 body 自洽
bnd = [v for v in uniq if s3.insn_at(v) is not None]
d1 = 0
d2 = 0
for v in uniq[:4000]:
    d = s3.chan_d(v)
    d1 += bool(d["d1"])
    d2 += bool(d["d2"])

res = dict(
    region="0x86E000-0x875000",
    slots=len(region), distinct_targets=len(uniq),
    pct_16B_aligned=round(100.0 * sum(1 for v in uniq if v % 16 == 0) / len(uniq), 2),
    pct_instruction_boundary=round(100.0 * len(bnd) / len(uniq), 2),
    pct_in_coverage=round(100.0 * len(in_cov) / len(uniq), 2),
    pct_in_channelB_vtable_slots=round(100.0 * len(in_B) / len(uniq), 2),
    pct_in_channelA_call_targets=round(100.0 * len(in_call) / len(uniq), 2),
    d1_rate_sampled=round(100.0 * d1 / min(4000, len(uniq)), 2),
    d2_rate_sampled=round(100.0 * d2 / min(4000, len(uniq)), 2),
    contrast_all_data_code_pointers=len(all_data_pts),
    contrast_all_data_pct_in_coverage=round(100.0 * len(all_in_cov) / len(all_data_pts), 2),
    in_coverage_sample=[f"{v:08X}" for v in in_cov[:10]],
    distinct_stride_pairs=len(uniq) - 1,
)
with open(os.path.join(EVIDENCE, "s10_region_verdict.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=2))
