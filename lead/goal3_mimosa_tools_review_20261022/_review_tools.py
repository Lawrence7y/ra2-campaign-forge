# -*- coding: utf-8 -*-
"""裁决 12：审视 tools/ 下 Mimosa「路径穿越」high 告警，逐处判真风险 / 误报。

判据（本脚本自动分类 + 打印上下文，供人工定夺）
-----------------------------------------------
对每个告警站点，取该行前后若干行源码，判定属于下列哪一类：

  (A) **写路径由命令行参数给出**（`argparse` 传入）⇒ 调用者自负责任，
      工具自身不遍历不可信输入 ⇒ **误报**（CLI 工具的常规形态）。
  (B) **路径来自被测文件的内部数据**（解析 INI/JSON 后拼路径）⇒ **真风险**，
      需要校验。
  (C) **路径来自目录遍历结果**（`os.walk` / `glob`）⇒ 视是否有 `..` 归一化而定。
  (D) **读路径由参数给出但用于 `open()`** ⇒ 同 (A)，误报。

自动分类不可靠，脚本的职责是**把上下文摆出来**，结论由人写进 md。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
FINDINGS = Path(r"C:/Users/Administrator/.mimosa/security-scans/"
                r"project-58d54c8400d61bac27a417b2/"
                r"scan-2026-10-22T04-33-44.241Z-23b228f990d6/findings.json")

CTX = 6


def norm(p):
    return p.replace("\\", "/")


def main():
    d = json.loads(FINDINGS.read_text(encoding="utf-8"))
    tools = []
    for f in d["findings"]:
        loc = f.get("location") or {}
        fp = norm(loc.get("file") or loc.get("path") or "")
        if not fp.startswith("tools/"):
            continue
        tools.append((fp, loc.get("line") or loc.get("startLine") or 0, f))

    print(f"tools/ findings: {len(tools)}")
    print("=" * 78)

    # 先看每处的上下文
    for i, (fp, ln, f) in enumerate(tools, 1):
        p = ROOT / fp
        if not p.exists():
            print(f"\n[{i}] {fp}:{ln}  !! FILE MISSING")
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        print(f"\n[{i}] {fp}:{ln}   ({f.get('title')})")
        lo = max(0, ln - 1 - CTX)
        hi = min(len(lines), ln + CTX)
        for k in range(lo, hi):
            mark = ">>" if k == ln - 1 else "  "
            print(f"  {mark} {k+1:>5}: {lines[k][:150]}")

    print()
    print("=" * 78)
    print("=== auto-classification (heuristic, for human review) ===")
    print("=" * 78)

    # 粗分类：看该文件是否 import argparse 且该行附近有无 argv/args.
    summary = []
    for fp, ln, f in tools:
        p = ROOT / fp
        if not p.exists():
            summary.append((fp, ln, "MISSING", ""))
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        lo = max(0, ln - 1 - 8)
        hi = min(len(lines), ln + 8)
        window = "\n".join(lines[lo:hi])
        has_args = bool(re.search(r"\bargs\.|argv|add_argument", window))
        has_walk = bool(re.search(r"os\.walk|glob\.|\bglob\(", window))
        has_open_w = bool(re.search(r"open\([^)]*[\"']w", window))
        kind = []
        if has_args:
            kind.append("args-derived")
        if has_walk:
            kind.append("walk-derived")
        if has_open_w:
            kind.append("write")
        summary.append((fp, ln, ",".join(kind) or "other", ""))

    for fp, ln, kind, _ in summary:
        print(f"  {fp}:{ln:<6} {kind}")

    # 汇总按文件
    print()
    from collections import Counter
    c = Counter(fp for fp, _, _, _ in summary)
    print("=== per-file count ===")
    for k, v in c.most_common():
        print(f"  {v:>2}  {k}")

    print()
    print(f"total tools/ findings: {len(summary)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
