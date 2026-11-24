# -*- coding: utf-8 -*-
"""_rfv_cascade.py — 独立核算：43 点处置后各件是否有非零动作；硬项集触达件数；节省指纹数。"""
import re
ROOT = "D:/Project/ra2-campaign-forge/lead/"
vp = ROOT + "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md"
with open(vp, encoding="utf-8") as f: vl = f.read().splitlines()

# 43 点展开（独立重写）
ALL = {}
cur = None
for ln in vl[93:125]:
    cols = [c.strip() for c in ln.strip().strip("|").split("|")]
    if len(cols) < 3 or not cols[0].isdigit(): continue
    if cols[1] != "同件" and cols[1].startswith("lead/"): cur = cols[1][5:]
    for m in re.finditer(r":(\d+)(?:-(\d+))?(\([a-z]\))?", cols[2]):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        for x in range(a, b+1): ALL[(cur,x)] = int(cols[0])

# 逐点三选一（据两份草案独立整理）
GA = "s604_attribution_20261108/S604_ATTRIBUTION.md"
SA = "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md"
LE = "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
D3 = "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md"
TP = "ledger_appendix_20261108/_lad_tpl.md"
SG = "s604_script_gap_20261109/S604_SCRIPT_GAP.md"
SF = "s604_script_gap_20261109/_sg_FINDINGS.md"
EX = "s604_exclusive_20261109/S604_EXCLUSIVITY.md"
SX = "s604_exclusive_20261109/_ex_EXCLUSIVITY.md"
SW = "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md"
RD = "direction_ruling_20261108/RULING_DIRECTION.md"
DR = "direction_ruling_20261108/_dr_RULING.md"
GR = "slowframe_r3_20261108/S604_GAP_RECHECK.md"

J = {}
def put(j, f, *pts):
    for n in pts: J[(f,n)] = j

# 同步草案（改2口径 = 严数3改点；加注10口径 = 严数11点；保留1）
put("加注", GR, 101, 153)
put("加注", GA, 113, 124, 138, 152)
put("改",   GA, 136)
put("改",   LE, 123); put("改", D3, 25)
put("加注", SG, 71, 115, 116, 130)
put("加注", EX, 212)
put("保留", EX, 206)
# 本批 28
put("加注", GA, 154, 165, 174)
put("改",   GA, 171)
put("加注", SA, 24, 69, 92, 108, 112)
put("改",   LE, 215); put("改", TP, 151)
put("加注", SG, 10, 59)
put("保留", SG, 55, 56, 57)
put("加注", SF, 13, 21, 71)
put("加注", EX, 202, 214)
put("加注", SX, 136, 138)
put("加注", SW, 91)
put("加注", RD, 17)
put("加注", DR, 48, 82, 147)

print("判定点总数 = %d (应 43)" % len(J))
print("未判定点 = %r" % sorted(set(ALL)-set(J)))
print("越界点 = %r" % sorted(set(J)-set(ALL)))
from collections import Counter
print("43 点分布 = %r" % dict(Counter(J.values())))

# 每件是否有非零动作（改 或 加注）
files = sorted(set(k[0] for k in ALL))
touched = [f for f in files if any(J.get(k) in ("改","加注") for k in J if k[0]==f)]
zero    = [f for f in files if f not in touched]
print("=== 全量方案：触达件数 = %d ===" % len(touched))
for f in touched:
    pts = sorted(k[1] for k in J if k[0]==f and J[k] in ("改","加注"))
    print("  TOUCH %-60s %d 非零动作点: %s" % (f.split('/')[-1], len(pts), pts))
print("零动作件 = %r" % zero)
print("⇒ 13 件是否全部触达: %s" % (len(touched)==13))

# 最小硬项集
hard = {(LE,123),(D3,25),(LE,215),(TP,151),(GA,171),(GA,136)}
hard_files = set(k[0] for k in hard)
print("=== 最小硬项集 ===")
print("硬项点 = %d : %s" % (len(hard), sorted(hard)))
print("触达件 = %d : %s" % (len(hard_files), sorted(x.split('/')[-1] for x in hard_files)))
print("全量 %d − 最小 %d = 省 %d 次" % (len(touched),len(hard_files),len(touched)-len(hard_files)))
print("若执行 _sa:90 连带 ⇒ +1 件 = %d 次，省 %d 次" % (len(hard_files)+1, len(touched)-len(hard_files)-1))
print("若『模板不单独维护』⇒ 全量 %d / 最小 %d，省 %d" % (len(touched)-1,len(hard_files)-1,(len(touched)-1)-(len(hard_files)-1)))
print("加批次 A 台账追加 +1 ⇒ 全链 %d 次" % (len(touched)+1))
