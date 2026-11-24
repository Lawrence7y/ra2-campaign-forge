# -*- coding: utf-8 -*-
"""_f2w_pass.py — 交付报告用：原 R11-PASS 件在增强版下的表现 + 全 30 件 verdict 统计。只读。"""
import json
from pathlib import Path

CMP = Path(r"D:\Project\ra2-campaign-forge\lead\r11_f2_fix_20261109\_f2_compare_out.json")
cmp_ = json.loads(CMP.read_text(encoding="utf-8"))
REPO = "D:\\Project\\ra2-campaign-forge\\"

print("== orig R11-PASS 件在增强版下 ==")
for r in cmp_["results"]:
    if r["orig"]["verdict"] == "PASS":
        print(r["file"].replace(REPO, ""), "| orig P=%d W=%d match=%d | plus P=%d W=%d match=%d" % (
            len(r["orig"]["problems"]), len(r["orig"]["warnings"]),
            sum(1 for b in r["orig"]["bindings"] if b["match"] is True),
            len(r["plus"]["problems"]), len(r["plus"]["warnings"]),
            sum(1 for b in r["plus"]["bindings"] if b.get("match") is True)))

print()
print("== 全 30 件 verdict 统计 ==")
o11 = sum(1 for r in cmp_["results"] if r["orig"]["verdict"] == "PASS")
p11 = sum(1 for r in cmp_["results"] if r["plus"]["verdict"] == "PASS")
oo = sum(1 for r in cmp_["results"] if r["orig_overall"] == "PASS")
po = sum(1 for r in cmp_["results"] if r["plus_overall"] == "PASS")
print("R11 PASS: orig=%d plus=%d | overall PASS: orig=%d plus=%d" % (o11, p11, oo, po))
