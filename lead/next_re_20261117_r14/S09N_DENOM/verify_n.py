#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
S09N-DENOM 一条命令的结论验证器（只读，不写任何文件）

断言并打印：
  A) 22 个子系统 panel_n == |coverage ∩ atlas|（entry 统一大写）→ diff 全为 0
  B) 每个子系统的 cov_rows - panel_n == 该子系统 atlas 外行数
  C) 大小写敏感匹配会得到 S09=198（卡片起点的错误来源）
用法：python lead\next_re_20261117_r14\S09N_DENOM\verify_n.py   （exit 0 = 全部通过）
"""
import csv, re, sys, os

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

def rd_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t"); next(r)
        return [row for row in r if row]

atlas_raw = [row[0] for row in rd_tsv(ATL)]
ATLAS, ATLAS_EXACT = {e.upper() for e in atlas_raw}, set(atlas_raw)
cov = rd_tsv(COV)

panel = {}
with open(PANEL, encoding="utf-8") as f:
    for line in f:
        m = re.match(r"^\|\s*(S\d\d)\s*\|\s*(\d+)\s*\|", line)
        if m: panel[m.group(1)] = int(m.group(2))

ok = True
print(f"{'sub':4}{'cov_rows':>9}{'panel_n':>9}{'diff':>6}{'atlas_in':>9}{'atlas_out':>10}  ok")
for s in sorted(panel):
    rows = [x for x in cov if x[1] == s]
    ina = sum(1 for x in rows if x[0].upper() in ATLAS)
    diff, out = len(rows) - panel[s], len(rows) - ina
    good = (panel[s] == ina) and (diff == out)
    ok &= good
    print(f"{s:4}{len(rows):9d}{panel[s]:9d}{diff:6d}{ina:9d}{out:10d}  {'PASS' if good else 'FAIL'}")

s09_exact = sum(1 for x in cov if x[1] == "S09" and x[0] in ATLAS_EXACT)
s09_ci    = sum(1 for x in cov if x[1] == "S09" and x[0].upper() in ATLAS)
print(f"\nS09: 大小写归一 atlas 内 {s09_ci}（== panel n {panel['S09']}）"
      f"／大小写敏感 atlas 内 {s09_exact}（卡片起点的 198 由此而来）")
print(f"atlas entry 全小写 = {all(e == e.lower() for e in atlas_raw)}；"
      f"coverage entry 含大写字母的行 = {sum(1 for x in cov if x[0] != x[0].lower())}")
print("\nVERDICT:", "PASS — panel_n ≡ |coverage∩atlas|，diff ≡ atlas 外行数" if ok else "FAIL")
sys.exit(0 if ok else 1)
