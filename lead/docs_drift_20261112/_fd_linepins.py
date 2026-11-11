# -*- coding: utf-8 -*-
"""Auxiliary grep (bounded): find any file that pins LINE NUMBERS to the two
target docs -- determines whether inserting near the top would break anchors.

Run as: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_linepins.py

Scope deliberately bounded: docs/**, lead/**/*.md + lead/**/*.txt (<5 MB),
root-level *.md, plus ra2forge/**/*.py. Large evidence outputs (>5 MB) are
excluded and reported as unverified, not silently dropped.
"""
import sys
sys.dont_write_bytecode = True
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "docs_drift_20261112"
GOUT = WD / "_grep"

MAX_BYTES = 5 * 1024 * 1024
rx = re.compile(
    r"(?:PROJECT_DIRECTION|WORK_CHAIN)\.md\s*[:：]\s*[0-9]"
    r"|(?:PROJECT_DIRECTION|WORK_CHAIN)\s*§\s*[0-9]"
    r"|(?:WORK_CHAIN)\s+§\s*[0-9.]+\s*/\s*:[0-9]+",
    re.IGNORECASE)

candidates = []
for base, pat in [
    (ROOT / "docs", "**/*.md"),
    (ROOT / "docs", "**/*.txt"),
    (ROOT / "lead", "**/*.md"),
    (ROOT / "lead", "**/*.txt"),
    (ROOT / "ra2forge", "**/*.py"),
]:
    for p in base.glob(pat):
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".py"):
            candidates.append(p)
for p in ROOT.glob("*.md"):
    if p.is_file():
        candidates.append(p)

seen, scanned, skipped = set(), [], []
for p in sorted(candidates):
    ap = p.as_posix()
    if ap in seen:
        continue
    seen.add(ap)
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith("lead/docs_drift_20261112/"):
        continue
    try:
        if p.stat().st_size > MAX_BYTES:
            skipped.append((rel, p.stat().st_size))
            continue
    except OSError:
        continue
    scanned.append(p)

hits = []
for p in scanned:
    rel = p.relative_to(ROOT).as_posix()
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        continue
    for i, l in enumerate(lines, 1):
        if rx.search(l):
            hits.append((rel, i, l))

out = ["# G9 · 行号锚点反查（改动影响面）", "",
       "> 目的：判断在 `docs/PROJECT_DIRECTION.md` / `docs/WORK_CHAIN.md` **顶部插入**文字，",
       "> 是否会让别处对这两份文件的「行号钉位」失效（WORK_CHAIN.md:171-173 自述的纪律）。",
       "> 范围（有界）：`docs/**/*.md|txt`、`lead/**/*.md|txt`、`ra2forge/**/*.py`、根 `*.md`；",
       "> 单文件 >5 MB 跳过并登记为未验。共扫描 %d 件，跳过 %d 件。" % (len(scanned), len(skipped)), "",
       "**命中 = %d**" % len(hits), "", "```text"]
for rel, i, l in hits:
    out.append("%s:%d:%s" % (rel, i, l[:400]))
if not hits:
    out.append("(no matches)")
out.append("```")
out.append("")
out.append("## 跳过的 >5 MB 文件（未验其是否含行号钉位）")
out.append("")
out.append("```text")
for rel, sz in sorted(skipped):
    out.append("%s (%d B)" % (rel, sz))
if not skipped:
    out.append("(none)")
out.append("```")
out.append("")
(GOUT / "G9_line_pins.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("LINE PIN HITS = %d ; scanned = %d ; skipped = %d" % (len(hits), len(scanned), len(skipped)))
for rel, i, l in hits[:40]:
    print("%s:%d:%s" % (rel, i, l[:180]))
