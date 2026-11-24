#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R92-T1-REJUDGE / Q4 : §2.49 点名的 10 件未决（tie152_verdicts.tsv 里 verdict=判不了）按新口径的落点。"""
import csv, os, sys

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"

rows = {r["rel"]: r for r in csv.DictReader(open(os.path.join(OUT, "rejudge1242.tsv"), encoding="utf-8"),
                                           delimiter="\t")}
t152 = {r["rel"]: r for r in csv.DictReader(open(os.path.join(LEAD,
         r"next_re_20261117_r14\R17_R91_T1_TIE152\tie152_verdicts.tsv"), encoding="utf-8"), delimiter="\t")}
und = [k for k, v in t152.items() if v["verdict"] == "判不了"]
und.sort()

lines = []
lines.append("=== Q4 · §2.49 点名的 10 件未决 → 新口径落点 ===")
lines.append("")
lines.append(f"名单来源：{os.path.join(LEAD, 'next_re_20261117_r14/R17_R91_T1_TIE152/tie152_verdicts.tsv')}")
lines.append(f"          取 verdict=='判不了' 的 {len(und)} 行（§2.49 一节所引的 10 件，41,607 B）")
lines.append("")
from collections import Counter, defaultdict
c, b = Counter(), defaultdict(int)
for k in und:
    r = rows[k]
    c[r["new_verdict"]] += 1
    b[r["new_verdict"]] += int(r["bytes"])
lines.append("新落点分布：" + " / ".join(f"{k} {c[k]} 件" for k in ("对象抄本", "过程输出", "永久判不了")))
lines.append("字节        ：" + " / ".join(f"{k} {b[k]} B" for k in ("对象抄本", "过程输出", "永久判不了")))
lines.append(f"合计        ：{sum(c.values())} 件 / {sum(b.values())} B")
lines.append("")
for i, k in enumerate(und, 1):
    r = rows[k]
    lines.append(f"[{i:02d}] {r['new_verdict']}  ({r['bytes']} B)")
    lines.append(f"     rel  : {k}")
    lines.append(f"     旧裁 : {r['old_verdict']}（tie152 class={t152[k].get('class','')}，R46 记判不了）")
    lines.append(f"     旧理由: {t152[k].get('reason','')[:220]}")
    lines.append(f"     §2.49: {r['basis']}")
    lines.append("")

with open(os.path.join(OUT, "q4_ten.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
