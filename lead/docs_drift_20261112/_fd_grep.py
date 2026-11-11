# -*- coding: utf-8 -*-
"""STEP 2 grep evidence collector (read-only outside the write domain).

Run as: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_grep.py

Emits rg-style `path:line:text` output for every drift point, plus exact
match counts, into _grep/. Also computes the max §-number mentioned in docs/.
"""
import sys
sys.dont_write_bytecode = True

import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DOCS = ROOT / "docs"
WD = ROOT / "lead" / "docs_drift_20261112"
GOUT = WD / "_grep"
GOUT.mkdir(parents=True, exist_ok=True)

MAX_SHOW = 200  # display cap; exact totals always reported


def text_files(root: Path):
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".json", ".ini", ".yaml", ".yml", ".py", ".ps1"):
            out.append(p)
    return out


def read_lines(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


DOCS_FILES = text_files(DOCS)
DOCS_CACHE = [(p, read_lines(p)) for p in DOCS_FILES]


def grep_docs(pattern: str, flags=0):
    rx = re.compile(pattern, flags)
    hits = []
    for p, lines in DOCS_CACHE:
        rel = p.relative_to(ROOT).as_posix()
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                hits.append((rel, i, line))
    return hits


def dump(fname: str, title: str, patterns: list, scope_note: str, grep_docs_fn=grep_docs,
         show=MAX_SHOW, extra_lines=None):
    out = [title, "", "> " + scope_note, ""]
    totals = {}
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE if "CASE_INSENSITIVE" in str(pat) else 0)
        hits = grep_docs_fn(pat)
        totals[pat] = len(hits)
        out.append("## pattern: `%s`" % pat)
        out.append("")
        out.append("**total matches = %d**" % len(hits))
        out.append("")
        if hits:
            out.append("```text")
            for rel, n, line in hits[:show]:
                out.append("%s:%d:%s" % (rel, n, line))
            if len(hits) > show:
                out.append("... [display truncated at %d of %d; exact total above]" % (show, len(hits)))
            out.append("```")
        else:
            out.append("```text")
            out.append("(no matches)")
            out.append("```")
        out.append("")
    if extra_lines:
        out.extend(extra_lines)
        out.append("")
    (GOUT / fname).write_text("\n".join(out) + "\n", encoding="utf-8")
    return totals


summary = {}

# ---------- G1: § numbers in docs ----------
sec_rx = re.compile(r"§\s*([0-9]{1,4})")
all_secs = []
per_file_max = {}
for p, lines in DOCS_CACHE:
    rel = p.relative_to(ROOT).as_posix()
    for i, line in enumerate(lines, 1):
        for m in sec_rx.finditer(line):
            all_secs.append((int(m.group(1)), rel, i, line.strip()))
max_sec = max((x[0] for x in all_secs), default=None)
hist = {}
for n, _, _, _ in all_secs:
    hist[n] = hist.get(n, 0) + 1
g1_totals = dump(
    "G1_section_numbers.txt",
    "# G1 · 台账节号（docs/ 侧 grep 输出）",
    [r"§60[0-9]", r"§605", r"§606", r"§607", r"§608", r"§609", r"§\s*[0-9]{3,4}"],
    "范围：docs/ 下全部 %d 个文本文件；逐行 `path:line:text`。计数为精确值。" % len(DOCS_CACHE),
)
g1_extra = [
    "## 统计", "",
    "- docs/ 内 `§` 后接数字的出现总次数：**%d**" % len(all_secs),
    "- **最高 § 号 = %s**" % ("§%d" % max_sec if max_sec is not None else "（无）"),
    "- `§600` 及以上命中数：**%d**" % sum(1 for x in all_secs if x[0] >= 600),
    "- 三位以上节号分布（号:次数）：`%s`" % json.dumps(
        {str(k): v for k, v in sorted(hist.items()) if k >= 100}, ensure_ascii=False),
    "- §600+ 明细：",
]
for n, rel, i, line in sorted([x for x in all_secs if x[0] >= 600]):
    g1_extra.append("  - §%d @ `%s:%d` : %s" % (n, rel, i, line[:200]))
if not [x for x in all_secs if x[0] >= 600]:
    g1_extra.append("  - （无）")
# append to G1 file
with (GOUT / "G1_section_numbers.txt").open("a", encoding="utf-8") as f:
    f.write("\n".join(g1_extra) + "\n")
summary["G1"] = {**g1_totals, "max_section": max_sec, "section_hits_total": len(all_secs),
                 "section_600plus": sum(1 for x in all_secs if x[0] >= 600)}

# ---------- G2: D-31 / direction ruling ----------
g2 = dump(
    "G2_d31.txt",
    "# G2 · D-31 方向裁决（docs/ 侧 grep 输出）",
    [r"D-31", r"direction_ruling", r"RULING_DIRECTION", r"方向裁决", r"Q1.?Q6"],
    "范围：docs/ 下全部 %d 个文本文件。事实侧文件见 G7。" % len(DOCS_CACHE),
)
summary["G2"] = g2

# ---------- G3: 11-10/11-11 static RE line ----------
g3 = dump(
    "G3_static_line.txt",
    "# G3 · 11-10/11-11 静态逆向线（docs/ 侧 grep 输出）",
    [r"slot2", r"0x54A56E", r"0x54A4F0", r"0x54A630", r"HouseClass", r"地图预置",
     r"预置槽位", r"PlayerControl", r"PercentBuilt", r"esi_caller_trace",
     r"re_crashwriter_static", r"re_map_preset_decode", r"playerctrl_semantics",
     r"re_orphan_owners", r"2026-11-1[01]"],
    "范围：docs/ 下全部 %d 个文本文件。事实侧文件见 G7。" % len(DOCS_CACHE),
)
summary["G3"] = g3

# ---------- G4: RE-ATLAS / L0 / 988 ----------
g4 = dump(
    "G4_atlas_numbers.txt",
    "# G4 · RE-ATLAS / L0 / 988 类（docs/ 侧 grep 输出）",
    [r"RE-ATLAS", r"re_atlas", r"R-064", r"停摆", r"STATUS\.md", r"L0 已完成",
     r"988", r"954", r"4\.07%", r"4\.28%", r"12,792", r"13,683", r"覆盖率"],
    "范围：docs/ 下全部 %d 个文本文件。事实侧 `re_atlas/STATUS.md` 见 G7。" % len(DOCS_CACHE),
)
summary["G4"] = g4

# ---------- G5: C line / ra2forge ----------
g5 = dump(
    "G5_ra2forge.txt",
    "# G5 · 交付线 C / ra2forge（docs/ 侧 grep 输出）",
    [r"ra2forge", r"以下是待实现目标", r"不表示已经具备", r"最小贯通样例",
     r"先盘点实际能力", r"DLC 框架与工具"],
    "范围：docs/ 下全部 %d 个文本文件。构建实测见 `../build_probe/`。" % len(DOCS_CACHE),
)
summary["G5"] = g5

# ---------- G6: P0/P1 queue ----------
g6 = dump(
    "G6_queue.txt",
    "# G6 · P0/P1 队列口径（docs/ 侧 grep 输出）",
    [r"P0", r"P1-A", r"P1-B", r"P1-C", r"P2-A", r"P2-C", r"APP2", r"当前审计与正文落地收尾"],
    "范围：docs/ 下全部 %d 个文本文件。事实侧台账/进度报告见 G7。" % len(DOCS_CACHE),
)
summary["G6"] = g6

# ---------- G7: fact-side greps ----------
FACT = {
    "lead/re_progress_check_20261111/RE_PROGRESS_20261111.md": [
        r"§60[0-9]", r"D-31", r"slot2", r"0x54A56E", r"HouseClass", r"PlayerControl",
        r"R-064", r"停摆", r"docs/", r"P0"],
    "lead/GOAL_THREE_TARGETS_20261018.md": [r"## §60[0-9]", r"§609", r"§604"],
    "lead/direction_ruling_20261108/RULING_DIRECTION.md": [r"D-31", r"Q1", r"Q6", r"unconfirmed"],
    "re_atlas/STATUS.md": [r"R-064", r"988", r"4\.07%", r"12,792", r"13,683", r"覆盖率"],
    "lead/slot2_fullscan_20261111/_sf_scan_out.txt": [r"slot2", r"0x54A4F0", r"0x54A630"],
    "lead/re_crashwriter_static_20261110/_cw_disasm_out.txt": [r"0x54A56E", r"0x0054A56E"],
    "lead/esi_caller_trace_20261111/_et_sites_out.txt": [r"0x54A4F0", r"slot2"],
    "lead/re_map_preset_decode_20261110/_md_parse_out.txt": [r"预置", r"槽位", r"XMP29U2"],
    "lead/playerctrl_semantics_20261111/_ps_disasm_out.txt": [r"PlayerControl", r"PercentBuilt"],
}
g7lines = ["# G7 · 事实侧 grep 输出（逐条脱节点的另一半引用）", "",
           "> 范围：下表所列事实侧文件；逐行 `path:line:text`；计数为精确值。", ""]
for rel, pats in FACT.items():
    p = ROOT / rel
    g7lines.append("## `%s`" % rel)
    g7lines.append("")
    if not p.is_file():
        g7lines.append("```text")
        g7lines.append("(FILE NOT FOUND)")
        g7lines.append("```")
        g7lines.append("")
        continue
    lines = read_lines(p)
    for pat in pats:
        rx = re.compile(pat, re.IGNORECASE)
        hits = [(i, l) for i, l in enumerate(lines, 1) if rx.search(l)]
        g7lines.append("### pattern `%s` — total = %d" % (pat, len(hits)))
        g7lines.append("")
        g7lines.append("```text")
        if hits:
            for i, l in hits[:60]:
                g7lines.append("%s:%d:%s" % (rel, i, l[:600]))
            if len(hits) > 60:
                g7lines.append("... [display truncated at 60 of %d; exact total above]" % len(hits))
        else:
            g7lines.append("(no matches)")
        g7lines.append("```")
        g7lines.append("")
(GOUT / "G7_fact_side.txt").write_text("\n".join(g7lines) + "\n", encoding="utf-8")

# ---------- G8: docs-side exact quotes used in STEP3 ----------
QUOTE_TARGETS = [
    ("docs/PROJECT_DIRECTION.md", [3, 4, 19, 46, 48, 50, 69, 71, 73, 74, 75, 76, 77, 78, 79, 81, 83]),
    ("docs/WORK_CHAIN.md", [3, 16, 52, 86, 88, 163, 165, 183]),
    ("docs/REWRITE_ROADMAP.md", [3, 22, 26, 28, 54, 79]),
    ("docs/REWRITE_RESEARCH.md", [3, 11, 12, 13, 312, 314, 319, 328]),
]
q = ["# G8 · STEP 3 拟改动处的逐字原文（docs/ 侧）", "",
     "> 行号在本次起点指纹快照上成立（见 `_evidence/00_docs_manifest_start.json`）。", ""]
for rel, nums in QUOTE_TARGETS:
    lines = read_lines(ROOT / rel)
    q.append("## `%s`" % rel)
    q.append("")
    q.append("```text")
    for n in nums:
        if 1 <= n <= len(lines):
            q.append("%s:%d:%s" % (rel, n, lines[n - 1]))
        else:
            q.append("%s:%d:(out of range; file has %d lines)" % (rel, n, len(lines)))
    q.append("```")
    q.append("")
(GOUT / "G8_quotes.txt").write_text("\n".join(q) + "\n", encoding="utf-8")

# ---------- summary ----------
(WD / "_grep" / "G0_SUMMARY.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
s = ["# G0 · grep 计数汇总（docs/ 侧）", "",
     "> 每条脱节点的完整 `path:line:text` 输出见同目录 G1–G8 文件。", ""]
for k, v in summary.items():
    s.append("## %s" % k)
    s.append("")
    s.append("```json")
    s.append(json.dumps(v, ensure_ascii=False, indent=2))
    s.append("```")
    s.append("")
(GOUT / "G0_SUMMARY.md").write_text("\n".join(s) + "\n", encoding="utf-8")

print("STEP2 GREP OK")
print("docs text files = %d" % len(DOCS_CACHE))
print("max section in docs = %s" % max_sec)
for k in ("G1", "G2", "G3", "G4", "G5", "G6"):
    print(k, json.dumps(summary[k], ensure_ascii=False))
