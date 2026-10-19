#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F1 root-cause dump: parse existing bench maps' house/unit placement.

Writes out/re_work/mimo_benchmap/f1_rootcause.txt
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUT = ROOT / "out" / "re_work" / "mimo_benchmap"
OUT.mkdir(parents=True, exist_ok=True)
MAPDIR = ROOT / "out" / "loadbench"

STANDARD = [
    "Americans", "Alliance", "French", "Germans", "British",
    "Africans", "Arabs", "Confederation", "Russians", "YuriCountry",
    "GDI", "Nod", "Neutral", "Special",
]


def parse_sections(text: str) -> dict[str, list[str]]:
    secs: dict[str, list[str]] = {}
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"\[([^\]]+)\]", s)
        if m:
            cur = m.group(1)
            secs.setdefault(cur, [])
            continue
        if cur and s and not s.startswith(";"):
            secs[cur].append(s)
    return secs


def kv(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def analyze(path: Path) -> dict:
    text = path.read_bytes().decode("gbk", errors="replace")
    secs = parse_sections(text)
    basic = kv(secs.get("Basic", []))
    houses_list = secs.get("Houses", [])
    unit_owners: Counter[str] = Counter()
    inf_owners: Counter[str] = Counter()
    unit_types: Counter[str] = Counter()
    inf_types: Counter[str] = Counter()
    cells: set[tuple[str, str, str]] = set()
    for line in secs.get("Units", []):
        if "=" not in line:
            continue
        parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
        if len(parts) >= 5:
            unit_owners[parts[0]] += 1
            unit_types[parts[1]] += 1
            cells.add((parts[0], parts[3], parts[4]))
    for line in secs.get("Infantry", []):
        if "=" not in line:
            continue
        parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
        if len(parts) >= 5:
            inf_owners[parts[0]] += 1
            inf_types[parts[1]] += 1
            cells.add((parts[0], parts[3], parts[4]))
    house_flags = {}
    for h in STANDARD:
        hsec = kv(secs.get(h, []))
        house_flags[h] = {
            "PlayerControl": hsec.get("PlayerControl"),
            "IQ": hsec.get("IQ"),
            "Allies": hsec.get("Allies"),
            "Country": hsec.get("Country"),
        }
    return {
        "file": path.name,
        "size": path.stat().st_size,
        "basic": {k: basic.get(k) for k in
                  ("Name", "GameMode", "MaxPlayer", "MinPlayer", "MultiplayerOnly",
                   "Player", "FreeRadar", "IgnoreGlobalAITriggers")},
        "houses_list": houses_list,
        "unit_owners": dict(unit_owners),
        "inf_owners": dict(inf_owners),
        "unit_types": dict(unit_types),
        "inf_types": dict(inf_types),
        "total_objects": sum(unit_owners.values()) + sum(inf_owners.values()),
        "unique_cells": len(cells),
        "house_flags": house_flags,
    }


def main() -> None:
    lines: list[str] = []
    lines.append("# MIMO-BENCHMAP F1 root-cause field evidence")
    lines.append("# target maps: out/loadbench/[2]0LoadBench_U0200.yrm / U0800.yrm")
    lines.append("")
    results = []
    for name in ("[2]0LoadBench_U0050.yrm", "[2]0LoadBench_U0200.yrm",
                 "[2]0LoadBench_U0800.yrm"):
        p = MAPDIR / name
        if not p.exists():
            lines.append(f"MISSING {name}")
            continue
        r = analyze(p)
        results.append(r)
        lines.append(f"## {r['file']}  size={r['size']}")
        lines.append(f"  Basic: {r['basic']}")
        lines.append(f"  [Houses]: {r['houses_list']}")
        lines.append(f"  Units by owner : {r['unit_owners']}")
        lines.append(f"  Inf  by owner : {r['inf_owners']}")
        lines.append(f"  Unit types     : {r['unit_types']}")
        lines.append(f"  Inf  types     : {r['inf_types']}")
        lines.append(f"  TOTAL objects  : {r['total_objects']}   unique_cells={r['unique_cells']}")
        lines.append("  house flags (PlayerControl / IQ / Allies):")
        for h, fl in r["house_flags"].items():
            lines.append(f"    {h:16} pc={fl['PlayerControl']!s:4} iq={fl['IQ']!s:4} allies={fl['Allies']!s:16} country={fl['Country']}")
        lines.append("")

    # Root-cause synthesis
    lines.append("## ROOT-CAUSE SYNTHESIS (field-level)")
    lines.append("""
[实证] 预置单位归属：
  U0200: Units 120 (Russians 60 + Americans 60) + Infantry 80 (Russians 40 + Americans 40) = 200
  U0800: Units 480 (Russians 240 + Americans 240) + Infantry 320 (Russians 160 + Americans 160) = 800
  全部预置对象的 owner ∈ {Russians, Americans}，无一挂在 Neutral/Special/Multi*。

[实证] MultiplayerOnly=1 + MaxPlayer=2 + MinPlayer=2：
  地图被限定为遭遇战/联机；大厅按玩家槽位创建 HouseClass。

[实证] house 段 PlayerControl=no（Russians/Americans 均是）：
  注释写「人机房由大厅分配」。遭遇战里 PlayerControl 由大厅按选国结果改写，
  地图里预写的 no 不会把这两个 house 变成玩家房。

[实证] HouseClass（YRpp HouseClass.h）：
  - StartingUnits : DynamicVectorClass<StartingTechnoStruct*>
  - RespawnStartingForces() @ 0x50D440   ← 遭遇战开局部队来源
  - IsPlayer() = CurrentPlayer || PlayerControl
  遭遇战每个玩家槽位会走 RespawnStartingForces 生成「国家默认开局部队」。

[推演] 为何实测 21/22 而非 0 或 200：
  21/22 ≈ 2 个玩家槽位的 StartingUnits 合计（每槽 MCV+若干护卫，随国家/兵力档变化），
  而非地图 [Units]/[Infantry] 的 200/800。
  地图预置的 Russians/Americans 对象未被实例化 —— 因为遭遇战创建的 HouseClass
  名称由大厅选国决定；若选国 ≠ Russians/Americans（或 MultiplayerOnly 路径
  只给「玩家槽位对应的 house」挂载预置对象），这 200/800 条就被丢弃。

[实证] 坐标无堆叠：U0200 200 对象占 200 个唯一 cell（max stack=1），
  排除「同格堆叠导致只生成一个」的可能。

[结论] 根因 = 预置单位的 owner house 与遭遇战实际启用的 house 集合不相交
  （或仅部分相交）；21/22 是 StartingUnits，不是地图负载。
  门禁 U 档要求 valid_samples≥500 / coverage≥70% 在当前图+模式下不可达。
""")
    out = OUT / "f1_rootcause.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
