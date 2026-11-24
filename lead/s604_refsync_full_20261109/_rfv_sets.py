# -*- coding: utf-8 -*-
"""_rfv_sets.py — 独立集合核算：43 点 / 已覆盖 15 / 剩余 28 是否互斥且穷尽。"""
import re

LEAD = "D:/Project/ra2-campaign-forge/lead/"
vp = LEAD + "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md"
dp = LEAD + "s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md"

with open(vp, "r", encoding="utf-8") as f:
    vl = f.read().splitlines()
with open(dp, "r", encoding="utf-8") as f:
    dl = f.read().splitlines()

# §4.2 表 :94-125 展开（与 _rfv_indep.py 同样算法，此处独立重写一遍）
ALL = {}
cur = None
for ln in vl[93:125]:
    cols = [c.strip() for c in ln.strip().strip("|").split("|")]
    if len(cols) < 3 or not cols[0].isdigit():
        continue
    if cols[1] != "同件" and cols[1].startswith("lead/"):
        cur = cols[1][5:]
    for m in re.finditer(r":(\d+)(?:-(\d+))?(\([a-z]\))?", cols[2]):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        for x in range(a, b + 1):
            ALL[(cur, x)] = int(cols[0])

# 同步草案处1..处14 覆盖点（实读 S604_REFSYNC_DRAFT.md:56-70 表 + 交付件 §1.2:37）
COVERED = {
 ("slowframe_r3_20261108/S604_GAP_RECHECK.md", 101),
 ("slowframe_r3_20261108/S604_GAP_RECHECK.md", 153),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 113),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 124),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 136),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 138),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 152),
 ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
 ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
 ("s604_script_gap_20261109/S604_SCRIPT_GAP.md", 71),
 ("s604_script_gap_20261109/S604_SCRIPT_GAP.md", 115),
 ("s604_script_gap_20261109/S604_SCRIPT_GAP.md", 116),
 ("s604_script_gap_20261109/S604_SCRIPT_GAP.md", 130),
 ("s604_exclusive_20261109/S604_EXCLUSIVITY.md", 212),
 ("s604_exclusive_20261109/S604_EXCLUSIVITY.md", 206),
}
# 交付件 §1.3 :43-57 剩余 28 点
REM = {
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", n) for n in (154,165,171,174)
} | {
 ("s604_attribution_20261108/_sa_ATTRIBUTION_S604.md", n) for n in (24,69,92,108,112)
} | {
 ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
 ("ledger_appendix_20261108/_lad_tpl.md", 151),
} | {
 ("s604_script_gap_20261109/S604_SCRIPT_GAP.md", n) for n in (10,55,56,57,59)
} | {
 ("s604_script_gap_20261109/_sg_FINDINGS.md", n) for n in (13,21,71)
} | {
 ("s604_exclusive_20261109/S604_EXCLUSIVITY.md", n) for n in (202,214)
} | {
 ("s604_exclusive_20261109/_ex_EXCLUSIVITY.md", n) for n in (136,138)
} | {
 ("slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md", 91),
 ("direction_ruling_20261108/RULING_DIRECTION.md", 17),
} | {
 ("direction_ruling_20261108/_dr_RULING.md", n) for n in (48,82,147)
}

print("§4.2 全表严数 = %d" % len(ALL))
print("同步草案覆盖严数 = %d" % len(COVERED))
print("交付件 §1.3 剩余严数 = %d" % len(REM))
print("覆盖 ∩ 剩余 = %r  (空集=无重复计算)" % sorted(COVERED & REM))
print("覆盖 ∪ 剩余 = %d" % len(COVERED | REM))
print("全表 − (覆盖∪剩余) = %r  (空集=无遗漏)" % sorted(set(ALL) - (COVERED | REM)))
print("(覆盖∪剩余) − 全表 = %r  (空集=无越界)" % sorted((COVERED | REM) - set(ALL)))
print("43 − 15 = %d ; 43 − 13(口径混算) = %d ; 41 − 13 = %d" % (43-15, 43-13, 41-13))

# 独立表述 41：扣除两对同文重复（LEDGER:123≡_la:25, LEDGER:215≡_lad_tpl:151）各 1 点
DUP = {("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",25),
       ("ledger_appendix_20261108/_lad_tpl.md",151)}
print("43 − 2 对同文重复 = %d (声明 41)" % (len(ALL) - len(DUP)))

# ---- 逐处三选一：从交付件 §3 标题行提取 改/加注/保留 ----
print("=== §3 逐处三选一（从 **#XX｜...｜判定** 标题提取）===")
judg = {}
for i, l in enumerate(dl):
    m = re.match(r"^\*\*(#[A-J]\d(?:[≡#A-Z0-9\-]*)?)｜[^｜]*｜(改|加注|保留)", l)
    if m:
        judg.setdefault(i+1, (m.group(1), m.group(2)))
        print("  :%d %s -> %s" % (i+1, m.group(1), m.group(2)))
from collections import Counter
c = Counter(v[1] for v in judg.values())
print("标题型计数 = %r 共 %d 条" % (dict(c), len(judg)))
# 另外 #C1≡#C2 是 2 点 1 条、#D2-D4 是 3 点 1 条
extra = {"改": 1, "加注": 0, "保留": 2}  # #C1≡#C2 多 1 改点；#D2-D4 多 2 保留点
print("按严数补正：改 %d+1=%d, 加注 %d, 保留 %d+2=%d, 合计 %d" % (
    c["改"], c["改"]+1, c["加注"], c["保留"], c["保留"]+2,
    c["改"]+1+c["加注"]+c["保留"]+2))

# ---- 43 点合并分布（严数）----
# 覆盖 15 点：处5(1改) + 处8≡处9(2改) + 处14(1保留) + 其余 11 加注
cov_dist = {"改":3, "加注":11, "保留":1}
rem_dist = {"改":3, "加注":22, "保留":3}
print("覆盖严数分布 = %r 合计 %d" % (cov_dist, sum(cov_dist.values())))
print("本批严数分布 = %r 合计 %d" % (rem_dist, sum(rem_dist.values())))
print("43 点合并分布 = %r 合计 %d" % (
    {k: cov_dist[k]+rem_dist[k] for k in cov_dist},
    sum(cov_dist.values())+sum(rem_dist.values())))
