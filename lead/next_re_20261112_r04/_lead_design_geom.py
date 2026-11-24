#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 自查：W85 设计里的坐标是否越界 / 每格堆叠密度。

判据（0-based 还是 1-based 需看引擎；这里两套都算）：
- 地图 size = [w,h]，合法 cell 通常 x∈[0,w-1] 或 [1,w]。
- 越界 = 任一对象坐标 <0 或 >=w (对 0-based 而言 >w-1)。
- 堆叠 = 同一 cell 上对象数 >1。
"""
import json
from collections import Counter
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")


def analyze(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    m = d["missions"][0]
    w, h = m["size"]
    print("=" * 78)
    print(f"{path.name}   size=({w},{h})  theater={m.get('theater')}")
    print(f"  player={m.get('player')}  waypoints={m.get('waypoints')}")
    print(f"  structures={len(m.get('structures', []))} units={len(m.get('units', []))} infantry={len(m.get('infantry', []))}")

    # 先看一个原始条目长什么样
    for key in ("structures", "units", "infantry"):
        arr = m.get(key) or []
        if arr:
            print(f"  {key}[0] sample = {json.dumps(arr[0], ensure_ascii=False)}")

    for key in ("structures", "units", "infantry"):
        arr = m.get(key) or []
        if not arr:
            continue
        coords = []
        bad = []
        for it in arr:
            c = it.get("cell") or it.get("coord") or it.get("pos")
            if c is None:
                # 可能用 x/y 或 x,y 扁平字段
                if "x" in it and "y" in it:
                    c = [it["x"], it["y"]]
                else:
                    continue
            x, y = int(c[0]), int(c[1])
            coords.append((x, y))
            if not (0 <= x < w and 0 <= y < h):
                bad.append((x, y, it.get("type") or it.get("name")))
        if not coords:
            print(f"  [{key}] 未识别坐标字段，键名 = {sorted(arr[0].keys())}")
            continue
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        cnt = Counter(coords)
        dup = {k: v for k, v in cnt.items() if v > 1}
        print(
            f"  [{key}] n={len(coords)} x∈[{min(xs)},{max(xs)}] y∈[{min(ys)},{max(ys)}] "
            f"越界={len(bad)} 同格堆叠格数={len(dup)} 最大堆叠={max(cnt.values()) if cnt else 0}"
        )
        if bad:
            print(f"     越界样例(最多5)：{bad[:5]}")
        if dup:
            worst = sorted(dup.items(), key=lambda kv: -kv[1])[:5]
            print(f"     最密格(最多5)：{worst}")

    # 按 house 分组统计（若 items 带 house/owner）
    houses = Counter()
    per_house_coords = {}
    for key in ("units", "infantry"):
        for it in m.get(key) or []:
            hs = it.get("house") or it.get("owner") or it.get("side") or "?"
            houses[hs] += 1
            c = it.get("cell") or [it.get("x"), it.get("y")]
            if c and c[0] is not None:
                per_house_coords.setdefault(hs, []).append((int(c[0]), int(c[1])))
    print(f"  house 分布: {dict(houses)}")
    for hs, cs in per_house_coords.items():
        cnt = Counter(cs)
        xs = [c[0] for c in cs]
        ys = [c[1] for c in cs]
        dup = sum(1 for v in cnt.values() if v > 1)
        print(
            f"    {hs:14s} n={len(cs):4d} x∈[{min(xs)},{max(xs)}] y∈[{min(ys)},{max(ys)}] "
            f"堆叠格={dup} 最大={max(cnt.values())}"
        )


for name in (
    r"lead\next_re_20261112_r03\W85_pressure\work\w85_design_pressure.json",
    r"lead\next_re_20261112_r03\W85_pressure\work\w85_design_control.json",
    r"lead\next_re_20261112_r02\W84_defeat_dialog\work\w84_design_df.json",
):
    p = BASE / name
    if p.exists():
        analyze(p)
    else:
        print(f"!! missing {p}")
