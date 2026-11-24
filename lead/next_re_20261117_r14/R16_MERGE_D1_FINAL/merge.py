# -*- coding: utf-8 -*-
"""R16-MERGE-D1-FINAL · 写盘：coverage 5 行第 4 列 + PANEL 插入 M98。

写域：仅 COVERAGE\coverage.tsv（5 行第 4 列）、COVERAGE\PANEL.md（插入 1 条 M98）、
     以及本目录 R16_MERGE_D1_FINAL\ 的产物。不动其它任何文件。
字节级：coverage 无 BOM、LF、末尾无换行；PANEL 无 BOM、LF、末尾有换行。
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_FINAL")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_FINAL", "delta.tsv")

def sha(b): return hashlib.sha256(b).hexdigest()

pin_cov  = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
pin_panel= open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
baseline = json.load(open(os.path.join(OUT, "baseline.json"), encoding="utf-8"))
before_col4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
delta_b  = open(DELTA, "rb").read()

# ---------- 1. coverage: 只改 5 行第 4 列 ----------
cov_lines = pin_cov.split(b"\n")            # 18499 segments, last is final data line (no trailing LF)
assert len(cov_lines) == 18499, len(cov_lines)
assert not pin_cov.endswith(b"\n")

# delta rows
dlines = delta_b.decode("utf-8-sig").split("\n")
if dlines and dlines[-1] == "": dlines = dlines[:-1]
drows = [ln.split("\t") for ln in dlines[1:]]
assert len(drows) == 5

changed = {}
for d in drows:
    e = d[0].strip().upper()
    info = before_col4[e]
    seg_idx = info["line_number"] - 1       # 1-based line number -> 0-based segment index
    seg = cov_lines[seg_idx]
    cols = seg.split(b"\t")
    assert len(cols) == 8
    old4 = cols[3].decode("utf-8")
    assert old4 == info["value"]
    new4 = d[3]
    assert new4.startswith(old4) and len(new4) > len(old4)
    cols[3] = new4.encode("utf-8")
    cov_lines[seg_idx] = b"\t".join(cols)
    changed[e] = dict(line=info["line_number"], old_col4_sha=hashlib.sha256(old4.encode("utf-8")).hexdigest(),
                      new_col4_len=len(new4.encode("utf-8")), old_col4_len=len(old4.encode("utf-8")))

new_cov = b"\n".join(cov_lines)
assert len(new_cov) == len(pin_cov) + sum(v["new_col4_len"]-v["old_col4_len"] for v in changed.values())
open(COV, "wb").write(new_cov)
open(os.path.join(OUT, "_after_coverage.tsv"), "wb").write(new_cov)   # for strict_panel compare

# ---------- 2. PANEL: 紧接 M97 块之后插入 1 条 M98 ----------
# M97 block = lines 284..289 (1-based). Insert before line 290 (M77 note).
panel_lines = pin_panel.split(b"\n")        # last segment is b"" because trailing LF
assert pin_panel.endswith(b"\n")
assert panel_lines[-1] == b""
assert len(panel_lines) == 676, len(panel_lines)
# verify anchor lines
assert b"M97 " in panel_lines[283], panel_lines[283][:80]
assert b"M77 " in panel_lines[289], panel_lines[289][:80]

M98 = [
"> ✅ **M98 补记：R16-D1-FINAL 并入 5 行（F2 净新增 ④ 槽位见证；批级 FAIL 仅涉筛选口径，与事实层无关）**",
"> 本批 5 行（`0051B1F0` / `0051DAF0` / `00522340` / `0070B570` / `00748190`）取自 `R16_D1_FINAL/delta.tsv`，5/5 严格前缀（新第 4 列 = 原第 4 列 + `；④ 活表槽位见证：…`，净增 303–311 字符），只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`。",
"> ① **事实层经异族审计 5/5 可用**：`R16_AUDIT_D1_FINAL/VERDICT.md` 判 §A1 原文保全 5/5、§A2 字节事实 30/30、§A3 体外 5/5、§A4 装配形态 5/5、§A6 披露指针 5/5、§E 反抄袭 0 不合格——事实层干净、可见字节全对，这 5 行**可以并表**。",
"> ② **批级 FAIL 的真相（如实披露）**：该批原称「按 ② 有独立审计链筛出 17 行」，异族审计查明执行卡 `generate.py:135-137` 实现的筛选轴实为 **④ 形态（F1/F2）**、代码里**没有任何审计链判定**——这是 **Lead 错误 R16-6**；已由用户 **D-52** 重新定义口径（宽读：`*_audit/VERDICT.md` 与 `NAMED_PUSH_AUDIT*/verdict.tsv` 等值，任何独立审计产物都算），并在另一张纯筛选卡 `R16_SIEVE_D1_WIDE` 里**重做**（判据写进脚本、先出完整集合与「被 17 行漏掉」清单、再派补写卡）。",
"> ③ **「做完这批即整线收口」不成立**：D-51 原文「做完这 17 行，静态 ④ 线整线收口」经审计判不成立——同一 317 行在窄读 / 误用形态轴 / 宽读下分别为 **1 / 17 / ≥83 行**（其中 **67 行**不在误做的 17 行内）。**真实可收集合以 `R16_SIEVE_D1_WIDE` 的实测为准**，不得再以 17 行当收官数。",
"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **389 / 1,654（23.52%）**升至 **394 / 1,654（23.82%）**，本批净增 **5 行**（5 行改前 `④` 计数全 0）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **222 / 1,654（13.42%）**升至 **227 / 1,654（13.72%）**，净增 **5 行**（5 行均写入 `④ 活表槽位见证` 子串，实测非推算）。",
"> 判定与计数均未变：coverage 18,498 数据行、列分布 `{8:18498}`、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。",
]
insert_bytes = [ln.encode("utf-8") for ln in M98]
new_panel_lines = panel_lines[:289] + insert_bytes + panel_lines[289:]
new_panel = b"\n".join(new_panel_lines)
open(PANEL, "wb").write(new_panel)
open(os.path.join(OUT, "_after_PANEL.md"), "wb").write(new_panel)    # for reversibility compare

# ---------- 3. log ----------
log = dict(
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(new_cov), before_bytes=len(pin_cov), after_bytes=len(new_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(new_panel), before_bytes=len(pin_panel), after_bytes=len(new_panel),
               inserted_after_line=289, inserted_lines=len(M98), m98_text=M98),
    changed_rows=changed,
)
with open(os.path.join(OUT, "MERGE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("COV  ", json.dumps(log["coverage"], ensure_ascii=False))
print("PANEL", json.dumps({k:v for k,v in log["panel"].items() if k!="m98_text"}, ensure_ascii=False))
print("changed_rows", json.dumps(changed, ensure_ascii=False))
