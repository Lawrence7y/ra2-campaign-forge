# -*- coding: utf-8 -*-
"""M67 PANEL.md sync. Anchor-based edits with strict assertions."""
import os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M67\PANEL.md.bak"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()

raw = open(P, "rb").read()
print("sha before:", sha256(P), "bytes before:", len(raw))
open(BAK, "wb").write(raw)

text = raw.decode("utf-8")
lines = text.split("\n")
print("split lines:", len(lines), "last:", repr(lines[-1][:40]))

# The card-mandated note (verbatim) + two correction-specific notes
NOTE = (
    "M67 并表 NAMED_PUSH_AUDIT7 PASS 13 行（S20 8 + S06 5，evidence_path 改指 NAMED_PUSH_AUDIT7/VERDICT.md）；"
    "0062FE90 表址按审计勘误改为 007E9D64；"
    "S06 五行 ④ 由审计补证；"
    "S12_B1 四行审计代理失败未审不并；"
    "M67 按审计勘误改表址；"
    "M67 备注：S06 五行 ④ 由 a-S20S06 审计补证，见 NAMED_PUSH_AUDIT7\\VERDICT.md"
)

def edit_line(idx, old_anchor, new_anchor, insert_note_after=None):
    ln = lines[idx - 1]
    assert old_anchor in ln, f"L{idx}: anchor not found: {old_anchor!r}"
    ln = ln.replace(old_anchor, new_anchor, 1)
    if insert_note_after is not None:
        assert insert_note_after in ln, f"L{idx}: note anchor not found: {insert_note_after!r}"
        ln = ln.replace(insert_note_after, insert_note_after + NOTE + "；", 1)
    lines[idx - 1] = ln
    return ln

# ---- Line 1: title note (prepend after "# PANEL — R14 coverage") ----
TITLE_NOTE = (
    "M67 并表 13 行（NAMED_PUSH_AUDIT7 PASS 13 行 S20 8 + S06 5，均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,556→1,569、atlas 内 1,550→1,563、atlas 外仍 6；"
    "面板 S20 proved 53→61、S06 130→135；"
    "0062FE90 表址按审计勘误改 007E9D84→007E9D64；S06 五行 ④ 由审计补证；"
    "S12_B1 四行审计代理失败未审不并；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；不 git commit）；"
)
assert lines[0].startswith("# PANEL — R14 coverage"), lines[0][:40]
lines[0] = "# PANEL — R14 coverage" + TITLE_NOTE + lines[0][len("# PANEL — R14 coverage"):]

# ---- Line 17: 全表/atlas [已证] row ----
edit_line(17, "**1,556 / 1,550**", "**1,569 / 1,563**",
          insert_note_after="| **1,569 / 1,563** | ")

# ---- Main panel rows ----
edit_line(60, "| 123 | 14.52 | 130 | 15.35 |", "| 123 | 14.52 | 135 | 15.94 |",
          insert_note_after="| 123 | 14.52 | 135 | 15.94 | ")
edit_line(74, "| 42 | 10.24 | 53 | 12.93 |", "| 42 | 10.24 | 61 | 14.88 |",
          insert_note_after="| 42 | 10.24 | 61 | 14.88 | ")
edit_line(77, "| **1372** | **10.62** | **1550** | **12.00** |",
              "| **1372** | **10.62** | **1563** | **12.10** |",
          insert_note_after="| **1372** | **10.62** | **1563** | **12.10** | ")

# ---- Strict double table rows ----
edit_line(110, "| S06 | 847 | 130 | 15.35 | **115** | **13.58** |",
               "| S06 | 847 | 135 | 15.94 | **120** | **14.17** |")
edit_line(124, "| S20 | 410 | 53 | 12.93 | **41** | **10.00** |",
               "| S20 | 410 | 61 | 14.88 | **49** | **11.95** |")
edit_line(127, "| **TOTAL** | **12916** | **1550** | **12.00** | **1233** | **9.55** |",
               "| **TOTAL** | **12916** | **1563** | **12.10** | **1246** | **9.65** |")

# ---- Strict narrative: add M67 note after M66 note ----
M67_STRICT_NOTE = (
    "> 📌 **M67 并表实算说明**：本表 S06 proved/strict 115→120（proved 130→135）、"
    "S20 41→49（proved 53→61）、TOTAL 1,233→1,246（proved 1,550→1,563）均按盘上实算；"
    "本次并入 13 行新语义均不含字面 `[未证]`（核 delta 第 4 列，0062FE90 表址已按审计勘误 007E9D84→007E9D64 但未引入 `[未证]`），"
    "strict 随 proved 同增（S06 +5、S20 +8、TOTAL +13）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)
m66_idx = None
for i, ln in enumerate(lines):
    if "M66 并表实算说明" in ln:
        m66_idx = i
        break
assert m66_idx is not None, "M66 note line not found"
lines.insert(m66_idx + 1, M67_STRICT_NOTE)

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
open(P, "wb").write(new_raw)
print("sha after:", sha256(P), "bytes after:", len(new_raw))
print("inserted strict note after original line", m66_idx + 1)
