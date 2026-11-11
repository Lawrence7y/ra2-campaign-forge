# -*- coding: utf-8 -*-
"""STEP 1 evidence collector (read-only outside the write domain).

Run as: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_step1.py

Computes, with hashlib, the byte size / sha256 / mtime of EVERY file under docs/,
sorts by mtime, emits the section-title line numbers of the two key docs, and
fingerprints the fact-side files cited later in the proposal.
"""
import sys
sys.dont_write_bytecode = True

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DOCS = ROOT / "docs"
WD = ROOT / "lead" / "docs_drift_20261112"
EV = WD / "_evidence"
EV.mkdir(parents=True, exist_ok=True)

TZ = timezone(timedelta(hours=8))  # Asia/Shanghai, per session context


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_row(path: Path, rel_base: Path) -> dict:
    st = path.stat()
    return {
        "rel": path.relative_to(rel_base).as_posix(),
        "bytes": st.st_size,
        "sha256": sha256_of(path),
        "mtime_ns": st.st_mtime_ns,
        "mtime_epoch": st.st_mtime,
        "mtime_local": datetime.fromtimestamp(st.st_mtime, TZ).strftime("%Y-%m-%d %H:%M:%S.%f+08:00"),
    }


# ---------- 1. full docs/ manifest ----------
rows = []
for p in DOCS.rglob("*"):
    if p.is_file():
        rows.append(stat_row(p, ROOT))

rows.sort(key=lambda r: (r["mtime_ns"], r["rel"]))
tree_payload = json.dumps(
    [{"rel": r["rel"], "bytes": r["bytes"], "sha256": r["sha256"], "mtime_ns": r["mtime_ns"]}
     for r in rows],
    ensure_ascii=False, sort_keys=True, separators=(",", ":"),
).encode("utf-8")
TREE_SHA = hashlib.sha256(tree_payload).hexdigest()

manifest = {
    "generated_at_local": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S+08:00"),
    "root": ROOT.as_posix(),
    "scope": "docs/** (all files, recursive, including hidden/ignored)",
    "file_count": len(rows),
    "tree_sha256": TREE_SHA,
    "tree_sha256_definition": "sha256 of canonical JSON array of {rel,bytes,sha256,mtime_ns}, sorted by (mtime_ns,rel)",
    "rows": rows,
}
(EV / "00_docs_manifest_start.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
(EV / "00_docs_tree_sha256.txt").write_text(
    "docs_tree_sha256=%s\nfile_count=%d\n" % (TREE_SHA, len(rows)), encoding="utf-8")

# ---------- 2. human-readable STEP1 inventory ----------
lines = []
lines.append("# STEP 1 · docs/ 全量指纹清单（起点快照）")
lines.append("")
lines.append("> 采集命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_step1.py`")
lines.append("> 算法：逐文件 `hashlib.sha256`（1 MiB 分块读）+ `Path.stat()` 取 st_size / st_mtime_ns。")
lines.append("> mtime 显示时区按会话上下文取 Asia/Shanghai（UTC+08:00）；机器可读精确值见 `_evidence/00_docs_manifest_start.json`。")
lines.append("> 范围：`docs/` 递归全部文件（含隐藏文件与 `.mimosa/` 下 JSON），共 **%d** 个文件。" % len(rows))
lines.append("> 全树聚合指纹 `docs_tree_sha256 = %s`（定义见 manifest）。" % TREE_SHA)
lines.append("")
lines.append("## 1.1 按 mtime 升序排列（全量 %d 行）" % len(rows))
lines.append("")
lines.append("| # | 文件（repo 相对路径） | 字节数 | sha256 | mtime (UTC+08:00) |")
lines.append("|--:|:--|--:|:--|:--|")
for i, r in enumerate(rows, 1):
    lines.append("| %d | `%s` | %d | `%s` | %s |" %
                 (i, r["rel"], r["bytes"], r["sha256"], r["mtime_local"]))
lines.append("")
# mtime distribution by day
by_day = {}
for r in rows:
    by_day.setdefault(r["mtime_local"][:10], []).append(r)
lines.append("## 1.2 mtime 按日聚合")
lines.append("")
lines.append("| 日期 (UTC+08:00) | 文件数 | 最早 | 最晚 |")
lines.append("|:--|--:|:--|:--|")
for d in sorted(by_day):
    rs = sorted(by_day[d], key=lambda x: x["mtime_ns"])
    lines.append("| %s | %d | %s | %s |" %
                 (d, len(rs), rs[0]["mtime_local"][11:], rs[-1]["mtime_local"][11:]))
lines.append("")
lines.append("## 1.3 关键两件的 mtime 与指纹（逐字核对题给断言）")
lines.append("")
for name in ("docs/PROJECT_DIRECTION.md", "docs/WORK_CHAIN.md"):
    r = next(x for x in rows if x["rel"] == name)
    lines.append("- `%s`：bytes=%d sha256=`%s` mtime=%s" %
                 (name, r["bytes"], r["sha256"], r["mtime_local"]))
lines.append("")
(WD / "STEP1_DOCS_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# ---------- 3. section-title line numbers ----------
HEADERS = []
for name in ("docs/PROJECT_DIRECTION.md", "docs/WORK_CHAIN.md"):
    p = ROOT / name
    raw = p.read_text(encoding="utf-8-sig")
    for n, line in enumerate(raw.splitlines(), 1):
        s = line.lstrip("\ufeff")
        stripped = s.lstrip()
        if stripped.startswith("#") and (len(stripped) == 1 or stripped[1] in " \t" or stripped[1] == "#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            HEADERS.append({"file": name, "line": n, "level": level, "text": s.rstrip()})

hlines = []
hlines.append("# STEP 1 · 逐节标题行号")
hlines.append("")
hlines.append("> 判据：行首（可含前导空白）为 1–6 个 `#` 且后跟空格的行，认定为标题行。")
hlines.append("> 逐字取自文件 UTF-8 文本，行号为 1 起算。表内行号用于 STEP 3 定位。")
hlines.append("")
for name in ("docs/PROJECT_DIRECTION.md", "docs/WORK_CHAIN.md"):
    hs = [h for h in HEADERS if h["file"] == name]
    hlines.append("## `%s`（共 %d 个标题行）" % (name, len(hs)))
    hlines.append("")
    hlines.append("| 行号 | 级别 | 标题原文 |")
    hlines.append("|--:|:--|:--|")
    for h in hs:
        hlines.append("| %d | H%d | `%s` |" % (h["line"], h["level"], h["text"].replace("|", "\\|")))
    hlines.append("")
(WD / "STEP1_SECTION_HEADERS.md").write_text("\n".join(hlines) + "\n", encoding="utf-8")

# ---------- 4. fact-side fingerprints ----------
FACT_PATTERNS = [
    "lead/re_progress_check_20261111/RE_PROGRESS_20261111.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/direction_ruling_20261108/RULING_DIRECTION.md",
    "re_atlas/STATUS.md",
    "docs/PROJECT_DIRECTION.md",
    "docs/WORK_CHAIN.md",
    "docs/REWRITE_RESEARCH.md",
    "docs/REWRITE_ROADMAP.md",
    "ra2forge/cli.py",
    "ra2forge/builder.py",
    "ra2forge/design.py",
]
extra = []
for pat in [
    "lead/slot2_fullscan_20261111/*",
    "lead/re_crashwriter_static_20261110/*",
    "lead/esi_caller_trace_20261111/*",
    "lead/re_map_preset_decode_20261110/*",
    "lead/playerctrl_semantics_20261111/*",
    "lead/re_orphan_owners_20261110/*",
    "lead/re_orphan_owners_20261111/*",
    "lead/ledger_bound_20261109/*",
]:
    import glob as _glob
    extra.extend(sorted(_glob.glob(str(ROOT / pat))))

fact_rows = []
seen = set()
for f in FACT_PATTERNS + extra:
    p = Path(f)
    if not p.is_absolute():
        p = ROOT / p
    if p.is_file() and p.as_posix() not in seen:
        seen.add(p.as_posix())
        try:
            fact_rows.append(stat_row(p, ROOT))
        except OSError:
            pass
fact_rows.sort(key=lambda r: r["rel"])

flines = ["# 事实侧引用件指纹（本次实算，hashlib）", "",
          "> 用途：STEP 2 每条「事实出处」的行号都锚在这些文件的本次指纹上；行号仅在对应快照 sha256 上成立。",
          "> 算法与 docs/ 清单相同。共 %d 件。" % len(fact_rows), "",
          "| 文件 | 字节数 | sha256 | mtime (UTC+08:00) |", "|:--|--:|:--|:--|"]
for r in fact_rows:
    flines.append("| `%s` | %d | `%s` | %s |" %
                  (r["rel"], r["bytes"], r["sha256"], r["mtime_local"]))
flines.append("")
(EV / "01_fact_side_fingerprints.md").write_text("\n".join(flines) + "\n", encoding="utf-8")
(EV / "01_fact_side_fingerprints.json").write_text(
    json.dumps({"rows": fact_rows}, ensure_ascii=False, indent=2), encoding="utf-8")

print("STEP1 OK")
print("docs file_count = %d" % len(rows))
print("docs_tree_sha256 = %s" % TREE_SHA)
for name in ("docs/PROJECT_DIRECTION.md", "docs/WORK_CHAIN.md"):
    r = next(x for x in rows if x["rel"] == name)
    print("%s bytes=%d mtime=%s sha256=%s" % (name, r["bytes"], r["mtime_local"], r["sha256"]))
print("fact_side_files = %d" % len(fact_rows))
print("headers = %d" % len(HEADERS))
