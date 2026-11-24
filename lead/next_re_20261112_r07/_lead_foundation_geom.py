#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 交叉核：C6 布局里 NAPOWR / TESLA 的实际坐标，及两种底座假设下的重叠格数。

用 ra2forge/maplib.py 的等距投影：to_cell(row,col) = (W + col - row, row + 1)
（W = 地图宽 = 100）。
"""
import json
from collections import Counter
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
DESIGN = BASE / r"lead\next_re_20261112_r04\W88_envelope\out\inputs\C6\w88_design_C6.json"

d = json.loads(DESIGN.read_text(encoding="utf-8"))
m = d["missions"][0]
W, H = m["size"]
print(f"size=({W},{H})  structures={len(m.get('structures', []))}  units={len(m.get('units', []))}")

structs = m["structures"]
by_type = {}
for s in structs:
    by_type.setdefault(s["type"], []).append((s["row"], s["col"], s.get("owner")))

print("\n=== 建筑清单 ===")
for t, lst in sorted(by_type.items()):
    rows = sorted({r for r, _, _ in lst})
    cols = sorted({c for _, c, _ in lst})
    print(f"  {t:8s} n={len(lst):2d}  rows={rows}  cols={cols}")

# 底座假设（等距投影下的 (dx, dy) 覆盖范围）
FOUND = {
    "NAPOWR": (3, 2),
    "TESLA": (1, 1),      # 假设 A（W89）
    "ATESLA": (1, 1),
    "NACNST": (4, 4),
    "GAPOWR": (2, 2),
}
FOUND_B = dict(FOUND)
FOUND_B["TESLA"] = (3, 2)  # 假设 B（W95）

WIDTH = W


def to_cell(row, col):
    return (WIDTH + col - row, row + 1)


def footprint(row, col, fw, fh):
    x, y = to_cell(row, col)
    return {(x + dx, y + dy) for dx in range(fw) for dy in range(fh)}


def overlap_report(found, label):
    print(f"\n=== {label} ===")
    cells = Counter()
    for t, lst in by_type.items():
        fw, fh = found.get(t, (1, 1))
        for row, col, _ in lst:
            for c in footprint(row, col, fw, fh):
                cells[c] += 1
    over = {c: n for c, n in cells.items() if n > 1}
    print(f"  占用格 {len(cells)}  重叠格 {len(over)}  最大堆叠 {max(cells.values())}")
    # 只算 NAPOWR 之间 / TESLA 之间
    for target in ("NAPOWR", "TESLA"):
        if target not in by_type:
            continue
        fw, fh = found.get(target, (1, 1))
        cc = Counter()
        for row, col, _ in by_type[target]:
            for c in footprint(row, col, fw, fh):
                cc[c] += 1
        ov = sum(1 for n in cc.values() if n > 1)
        print(f"    {target} 单类：占用 {len(cc)}  重叠格 {ov}  最大 {max(cc.values())}  (底座 {fw}x{fh})")


overlap_report(FOUND, "假设 A：TESLA = 1x1（W89 说法）")
overlap_report(FOUND_B, "假设 B：TESLA = 3x2（W95 说法）")
