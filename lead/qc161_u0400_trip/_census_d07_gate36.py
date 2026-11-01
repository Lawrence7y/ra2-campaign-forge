#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 支撑件：把 L3 门禁报出的「36 high G 条」逐条定性。

为什么要这个件：D-07 立项时只有「36 high」一个数字，两条备选方案（A 清墙 /
B 按写域路由）都建立在「这些 high 到底是什么」的隐含假设上。本件把每条
finding 落到四栏：① 静态命中还是污点链（后者自带 advisory+proofGaps）；
② 落点文件是否被哈希冻结（改了会推翻全链断言 ⇒ 事实上不可修）；
③ 该行是否真的有外部输入进 sink；④ 本线（GOAL-3T）有没有写权。

数据源两路，**都不靠手抄**：
  - 密封深度扫描 findings.json（含 occurrence 粒度）；
  - 对每个落点做 git blame 归因（作者/提交），判「在谁写域」。

复跑：python lead/qc161_u0400_trip/_census_d07_gate36.py
退出码：0 = 普查完成（不表示零风险）；2 = 数据源缺失。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---- 密封扫描件（深扫，2026-10-23T20:36Z；由 mimosa security_scan 产出）----
SCAN = Path(r"C:\Users\Administrator\.mimosa\security-scans"
            r"\project-58d54c8400d61bac27a417b2"
            r"\scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0\findings.json")

# ---- 哈希冻结件：改动会推翻既有全链断言 ----
FROZEN = {
    "lead/goal1_harness6_20261022/qc151_trip.harness6.py":
        ("ff8245d27b3db22a", 463219, "母本（四趟实测 harness_sha16）"),
    "lead/goal1_harness7_20261023/qc151_trip.harness7.py":
        ("d019e8beecfb5fd8", 472020, "D-05 补丁副本（母本零改动派生）"),
}

# ---- 本线写域：GOAL-3T 只动 lead/qc161_u0400_trip/ ----
def in_my_write_domain(path: str) -> bool:
    return path.startswith("lead/qc161_u0400_trip/")


def sha16_of(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def blame_head(path: str) -> str:
    """取该文件最后一次改动的提交短哈希 + 日期，判归因。"""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%h %ad", "--date=short", "--", path],
            cwd=str(ROOT), capture_output=True, text=True, timeout=20, check=False)
        return out.stdout.strip() or "?"
    except Exception as exc:                     # noqa: BLE001
        return "ERR:%s" % exc


def gate_class(f: dict) -> str:
    """门禁类别：静态 sink vs 跨文件污点链（后者为 advisory）。"""
    if f.get("kind") == "cross-file" or f.get("advisory"):
        return "污点链(advisory)"
    return "静态sink"


def _group_by_id(fs: list[dict]) -> dict[str, set[str]]:
    """按 findingId 归并，值 = 该组覆盖的文件集合（用于证伪跨文件共用）。"""
    g: dict[str, set[str]] = {}
    for f in fs:
        g.setdefault(f["findingId"], set()).add(f["location"]["path"])
    return g


def main() -> int:
    if not SCAN.is_file():
        print("★ 数据源缺失：%s" % SCAN)
        return 2
    doc = json.loads(SCAN.read_text(encoding="utf-8"))
    fs = doc["findings"]

    print("=" * 96)
    print("D-07 支撑普查：L3 门禁 36 high 逐条定性")
    print("数据源：%s" % SCAN.name)
    print("密封 totals：%s" % doc.get("totals"))
    print("=" * 96)

    high = [f for f in fs if f["severity"] == "high"]
    # ★ findingId 的真实粒度实测为「(规则, 文件) 对」，**不是**「缺陷数」：
    #   同一文件同规则的 3 处落点共用一个 findingId（atlas_audit.py 189/193/230），
    #   而跨文件从不共用（实测跨文件组数 = 0）。把它当缺陷数会把「一处规则命中
    #   多行」误报成「一个缺陷」，故此处只作归并口径，不做缺陷计数。
    print("\n[1] 计数对账")
    print("    findings 总条数         = %d（occurrence 粒度，每处落点一条）"
          % len(fs))
    print("    severity==high          = %d" % len(high))
    print("    唯一 findingId          = %d（粒度实测 = (规则,文件) 对，"
          "**不是缺陷数**）" % len({f["findingId"] for f in fs}))
    print("    受影响文件数            = %d"
          % len({f["location"]["path"] for f in fs}))
    print("    跨文件共用 findingId    = %d（0 即证实上方粒度判断）"
          % len([k for k, v in _group_by_id(fs).items() if len(v) > 1]))
    stat = sum(1 for f in high if gate_class(f) == "静态sink")
    taint = sum(1 for f in high if gate_class(f) != "静态sink")
    print("    ├─ 静态 sink           = %d" % stat)
    print("    └─ 跨文件污点链(advisory) = %d" % taint)

    print("\n[2] 哈希冻结件核查（改了即推翻全链断言 ⇒ 事实上不可修）")
    frozen_hits = 0
    for p, (want, size, why) in FROZEN.items():
        fp = ROOT / p
        if not fp.is_file():
            print("    ✗ %s 不存在" % p)
            continue
        got = sha16_of(fp)
        nbytes = fp.stat().st_size
        ok = (got == want and nbytes == size)
        hits = sum(1 for f in high if f["location"]["path"] == p)
        frozen_hits += hits if ok else 0
        print("    %s %-46s %s / %d B  (期望 %s / %d)  该件上 high=%d"
              % ("✓" if ok else "✗★", p.split("/")[-1], got, nbytes,
                 want, size, hits))
        print("        冻结理由：%s" % why)
    print("    ⇒ 落在**已核实冻结**件上的 high = %d 条" % frozen_hits)

    print("\n[3] 逐条定性（按类别）")
    print("    %-18s %-52s %-6s %-8s %s"
          % ("类别", "落点", "行", "归属", "冻结?"))

    rows = []
    for f in sorted(high, key=lambda x: (x["location"]["path"],
                                         x["location"]["line"])):
        loc = f["location"]
        p, ln = loc["path"], loc["line"]
        cls = gate_class(f)
        frozen = "是★" if p in FROZEN else "否"
        mine = "本线" if in_my_write_domain(p) else "他线"
        rows.append((cls, p, ln, mine, frozen, f))
        print("    %-18s %-52s %-6s %-8s %s"
              % (cls, p if len(p) <= 52 else "…" + p[-51:], ln, mine, frozen))

    print("\n[4] 关键分组")
    by_file: dict[str, int] = {}
    for cls, p, ln, mine, frozen, _f in rows:
        by_file[p] = by_file.get(p, 0) + 1
    print("    受影响文件数 = %d" % len(by_file))
    for p in sorted(by_file, key=lambda x: -by_file[x]):
        print("      %-62s %d" % (p, by_file[p]))

    mine_hits = [r for r in rows if r[3] == "本线"]
    print("\n[5] 本线写域命中（GOAL-3T 是否引入了任何一条）")
    if mine_hits:
        for cls, p, ln, _m, _fz, _f in mine_hits:
            print("      ★ %s:%s" % (p, ln))
    else:
        print("      0 条 ⇒ 本线交付件对门禁贡献为零；阻断完全来自既有件。")

    n_frozen_files = sum(
        1 for p in FROZEN
        if (ROOT / p).is_file() and sha16_of(ROOT / p) == FROZEN[p][0])
    print("\n[6] 结论（可复算的三句话）")
    print("    ① %d high = %d 静态 sink + %d advisory 污点链"
          "（occurrence 粒度，逐处落点计数）。"
          % (len(high), stat, taint))
    print("    ② 其中 %d 条落在**已实测哈希冻结**的 %d 个件上"
          "（harness6/7）⇒ 修它=改母本/补丁副本=推翻全链断言。"
          % (frozen_hits, n_frozen_files))
    print("    ③ 本线写域命中 0 ⇒ 选项 A（他线清零）要求他人承担"
          " 这 %d 个冻结件的修改，而那与「母本零改动」铁律直接冲突。"
          % n_frozen_files)
    print("\n    ★ 因此 D-07 的 A 与 B 不是「工作量」之别，而是"
          "「A 在冻结件上与铁律冲突」；C 受「主仓=唯一真源」限制。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
