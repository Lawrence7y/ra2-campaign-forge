# -*- coding: utf-8 -*-
# _wlv_payloads.py — 独立实读 5 份任务书 payload.lowered 原文（不采信报告转述）
import json, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs")
FILES = {
    "matrix_ab_ruling(第五步)": "dwfrun-db5bad08-1aa0-4dea-940f-5f66a8b27a06.mjs",
    "matrix_reach(第二步)": "dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs",
    "n11_wording_fix(逐处对照)": "dwfrun-903e6b21-eb50-4c2f-a8dd-da3851198786.mjs",
    "s604_script_gap(存在性/可重建)": "dwfrun-bc9d8b8e-9faa-4226-8022-ccd881335683.mjs",
    "R9SEM(自证起源)": "dwfrun-8156bb52-3202-457d-bbde-6774ee112fb8.mjs",
}
NEEDLES = [
    "需谁批准", "要给出实跑输出", "必须给逐处改前改后对照",
    "给出确定结论：脚本存在 / 不存在 / 存在疑似但不确定",
    "给出判定：可唯一重建 / 可重建但有自由度 / 不可重建",
    "编排方已实跑确认这 5 处都是",
    "语义在场、字面不匹配",
]
def lowered(fname):
    t = (ROOT / fname).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    low, _ = json.JSONDecoder().raw_decode(t[i+len("export const payload = "):])
    return low.get("lowered", "")

print("=== 每份任务书 lowered 长度与命中 ===")
lowered_by = {}
for label, fn in FILES.items():
    low = lowered(fn)
    lowered_by[label] = low
    print(f"\n--- {label}  {fn}  len={len(low)} ---")
    for n in NEEDLES:
        cnt = low.count(n)
        if cnt:
            print(f"  HIT x{cnt}: {n}")
            for m in list(re.finditer(re.escape(n), low))[:3]:
                s = max(0, m.start()-180); e = min(len(low), m.end()+220)
                ctx = low[s:e].replace("\n", " | ")
                print(f"     ctx: ...{ctx}...")
print("\n=== 关键句精确上下文（逐字，含前后 300 字符）===")
CHECK = [
    ("matrix_ab_ruling(第五步)", "需谁批准"),
    ("matrix_reach(第二步)", "要给出实跑输出"),
    ("n11_wording_fix(逐处对照)", "必须给逐处改前改后对照"),
    ("s604_script_gap(存在性/可重建)", "给出确定结论：脚本存在 / 不存在 / 存在疑似但不确定"),
    ("s604_script_gap(存在性/可重建)", "给出判定：可唯一重建 / 可重建但有自由度 / 不可重建"),
    ("R9SEM(自证起源)", "编排方已实跑确认这 5 处都是"),
]
for label, n in CHECK:
    low = lowered_by[label]
    i = low.find(n)
    print(f"\n[{label}] needle={n!r} found_at={i}")
    if i >= 0:
        print(repr(low[max(0,i-300): i+len(n)+300]))
