# -*- coding: utf-8 -*-
"""R16-MERGE-F1 / B1 — perform the merge (coverage.tsv col4 x18 + PANEL.md M89 insert).
Byte-precise. Saves before/after state and the inserted block for restorability checks.
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_F1_B1", "delta.tsv")
MY   = os.path.join(ROOT, "R16_MERGE_F1_B1")
os.makedirs(MY, exist_ok=True)

FOUR = "④"
FOUR_SOLOT = "④ 活表槽位见证"

def fstat(path):
    b = open(path, "rb").read()
    return dict(mtime=os.path.getmtime(path), size=len(b),
                sha256=hashlib.sha256(b).hexdigest(), lines=b.count(b"\n"))

# ---------- M89 disclosure ----------
DISCLOSURE_LINES = [
    "> ✅ **M89 补记：F1（槽位-安装型）缺口行 ④ 成文 —— 批次 B1 并入 18 行**",
    "> 本批 18 行取自 `R16_PROBE_4GAP\\scan_F1_audit.tsv` 派生集合（`same_source=no` + `ring4_at` 解出装表指令 + 装表点体外 + 现盘 `[已证]` 且第 4 列无 `④ 活表槽位见证` + ③ 干净），派生命中 76 行，本批取第 1–18 行。",
    "> 异族审计（`R16_AUDIT_F1_B1\\VERDICT.md`）判 **PASS 18 / FAIL 0 / 必改 0**，§B 8 项 × 18 = **144/144** 字节事实独立复算为真。",
    "> **定表**：执行器所选活表经审计独立核「精确类一致者恰好 1 张」（B1 类型：MouseClass::slot17 同槽 9 张、AnimClass::slot84 同槽 21 张，亦各只 1 张类一致）。",
    "> 数字（口径 A/B 实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **347 / 1,654（20.98%）升至 351 / 1,654（21.22%）**，本批**净增 = 351 − 347 = 4 行**，**不是 +18**：18 行里有 **14 行**改前第 4 列已含 `④`，故这 14 行口径 A 不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **134 / 1,654（8.10%）升至 152 / 1,654（9.19%）**（净增 18 行）。",
    "> ⚠️ **已接受限制（来自审计 NIT，不判 FAIL 但引用者须知情）**：① **同一格并存两条 ④** —— 因 append-only 约束，14 行追加后同一第 4 列里同时存在旧 ④ 表述与新 `④ 活表槽位见证`；审计已核新旧两条指向同一 vt/site/宿主、无矛盾，⇒ **下游若按「④ 条数」或子串分桶统计会被双计，必须按行去重**。② **个位行本 entry 体内也装同一张表** —— ④ 采纳的是体外装表点（活性不靠自身见证），但 §12.3 意义上独立链只有体外那一条；审计点名 B2 批有 6 行如此（`005FEAF0`/`0062D7A0`/`0062D9A0`/`00644960`/`00645950`/`006B5850`）；本披露写入该条以覆盖后续批次，B1 批对应行数未逐行核，见各批 `fields.tsv`。",
    "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**。",
]
DISCLOSURE_BYTES = [ln.encode("utf-8") for ln in DISCLOSURE_LINES]
# encoded block: each line + \n (PANEL.md uses LF only)
INSERT_BYTES = ("\n".join(DISCLOSURE_LINES) + "\n").encode("utf-8")

# ---------- capture before ----------
cov_before_bytes = open(COV, "rb").read()
panel_before_bytes = open(PANEL, "rb").read()
before_state = dict(
    coverage=fstat(COV),
    panel=fstat(PANEL),
)
assert cov_before_bytes.count(b"\r") == 0
assert panel_before_bytes.count(b"\r") == 0

# ---------- delta ----------
dlines = open(DELTA, encoding="utf-8").read().split("\n")
if dlines and dlines[-1] == "":
    dlines = dlines[:-1]
assert len(dlines) == 19
delta_rows = [ln.split("\t") for ln in dlines[1:]]
assert all(len(r) == 8 for r in delta_rows)
delta_map = {r[0]: r[3] for r in delta_rows}
assert len(delta_map) == 18

# ---------- coverage byte-level merge ----------
cov_lines = cov_before_bytes.split(b"\n")
trailing_nl = cov_lines[-1] == b""
if trailing_nl:
    cov_lines = cov_lines[:-1]

# index of each data line by entry
entry_idx = {}
for i, ln in enumerate(cov_lines[1:], start=1):
    e = ln.split(b"\t")[0].decode("utf-8")
    entry_idx.setdefault(e, []).append(i)

original_col4 = {}
for e in delta_map:
    assert e in entry_idx and len(entry_idx[e]) == 1, (e, entry_idx.get(e))
    i = entry_idx[e][0]
    f = cov_lines[i].split(b"\t")
    assert len(f) == 8
    disk_col4 = f[3].decode("utf-8")
    assert delta_map[e].startswith(disk_col4), f"strict prefix fail {e}"
    original_col4[e] = disk_col4

new_cov_lines = list(cov_lines)
for e, new_col4 in delta_map.items():
    i = entry_idx[e][0]
    f = list(cov_lines[i].split(b"\t"))
    f[3] = new_col4.encode("utf-8")
    new_cov_lines[i] = b"\t".join(f)

merged_cov_bytes = b"\n".join(new_cov_lines)
if trailing_nl:
    merged_cov_bytes += b"\n"
assert merged_cov_bytes.count(b"\r") == 0

# ---------- PANEL insert after M88 block ----------
panel_lines = panel_before_bytes.split(b"\n")  # last element b'' if trailing newline
m88_idx = [i for i, l in enumerate(panel_lines) if "M88 补记".encode("utf-8") in l]
assert len(m88_idx) == 1, m88_idx
i = m88_idx[0]
j = i
marker_p = "> 📌".encode("utf-8")
while (j + 1 < len(panel_lines)
       and panel_lines[j + 1].startswith(b"> ")
       and not panel_lines[j + 1].startswith(marker_p)):
    j += 1
# j = last line of M88 block; insert after j
assert "M88".encode("utf-8") in b"\n".join(panel_lines[i:j+1])
assert panel_lines[j + 1].startswith(marker_p), panel_lines[j + 1][:40]
new_panel_lines = panel_lines[:j+1] + DISCLOSURE_BYTES + panel_lines[j+1:]
merged_panel_bytes = b"\n".join(new_panel_lines)
assert merged_panel_bytes.count(b"\r") == 0
assert merged_panel_bytes.startswith(panel_before_bytes[:200])

# ---------- safety backups (into own product dir) ----------
open(os.path.join(MY, "coverage.before.bak"), "wb").write(cov_before_bytes)
open(os.path.join(MY, "PANEL.before.bak"), "wb").write(panel_before_bytes)

# ---------- WRITE ----------
open(COV, "wb").write(merged_cov_bytes)
open(PANEL, "wb").write(merged_panel_bytes)

# ---------- capture after ----------
after_state = dict(coverage=fstat(COV), panel=fstat(PANEL))

# ---------- persist state for verify.py ----------
state = dict(
    before=before_state,
    after=after_state,
    original_col4=original_col4,
    delta_col4=delta_map,
    entries=list(delta_map.keys()),
    insert_line_after_m88=j + 1,  # 1-based line number in BEFORE panel
    insert_line_count=len(DISCLOSURE_LINES),
    disclosure_lines=DISCLOSURE_LINES,
    insert_bytes_sha256=hashlib.sha256(INSERT_BYTES).hexdigest(),
    trailing_nl_cov=trailing_nl,
)
with open(os.path.join(MY, "before_state.json"), "w", encoding="utf-8") as f:
    json.dump(before_state, f, ensure_ascii=False, indent=2)
with open(os.path.join(MY, "after_state.json"), "w", encoding="utf-8") as f:
    json.dump(after_state, f, ensure_ascii=False, indent=2)
with open(os.path.join(MY, "merge_state.json"), "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
with open(os.path.join(MY, "inserted_M89.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(DISCLOSURE_LINES) + "\n")

print("=== WROTE coverage.tsv ===")
print(" before size", before_state["coverage"]["size"], "sha", before_state["coverage"]["sha256"][:16])
print(" after  size", after_state["coverage"]["size"], "sha", after_state["coverage"]["sha256"][:16])
print("=== WROTE PANEL.md ===")
print(" before size", before_state["panel"]["size"], "sha", before_state["panel"]["sha256"][:16])
print(" after  size", after_state["panel"]["size"], "sha", after_state["panel"]["sha256"][:16])
print("inserted after BEFORE line", j + 1, "count", len(DISCLOSURE_LINES))
print("delta bytes added cov:", after_state["coverage"]["size"] - before_state["coverage"]["size"])
print("delta bytes added panel:", after_state["panel"]["size"] - before_state["panel"]["size"])
