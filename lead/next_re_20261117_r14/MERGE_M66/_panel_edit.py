# -*- coding: utf-8 -*-
"""M66 PANEL.md sync. Line-index based edits with ASCII-anchor assertions."""
import os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\PANEL.md.bak"

def sha256(p):
    h = hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): h.update(c)
    return h.hexdigest().upper()

raw = open(P,"rb").read()
text = raw.decode("utf-8")
print("sha before:", sha256(P))
print("bytes before:", len(raw))

# backup
open(BAK,"wb").write(raw)

lines = text.split("\n")
assert len(lines) == 522, len(lines)  # 521 lines + trailing empty (file ends with LF)

NOTE = ("M66 并表 NAMED_PUSH_AUDIT6 PASS 18 行（S22 TClassFactory 同族）"
        "+ NAMED_PUSH_AUDIT5 PASS 11 行（S06 4 + S20 7），"
        "evidence_path 分别改指两审计 VERDICT；strict 按权威口径 [未证] 字面重算")

def edit_line(idx, old_anchor, new_anchor, insert_note_after=None):
    """idx is 1-based line number. Replace old_anchor with new_anchor exactly once.
       If insert_note_after given (an ASCII anchor), insert NOTE after it."""
    ln = lines[idx-1]
    assert old_anchor in ln, f"L{idx}: anchor not found: {old_anchor!r}"
    ln = ln.replace(old_anchor, new_anchor, 1)
    if insert_note_after is not None:
        assert insert_note_after in ln, f"L{idx}: note-after anchor not found: {insert_note_after!r}"
        ln = ln.replace(insert_note_after, insert_note_after + NOTE + "；", 1)
    lines[idx-1] = ln
    return ln

# ---- Line 1: title note ----
TITLE_NOTE = ("M66 并表 29 行（NAMED_PUSH_AUDIT6 PASS 18 行 S22 TClassFactory 同族 + "
              "NAMED_PUSH_AUDIT5 PASS 11 行 S06 4/S20 7，均 atlas 内，仅改 coverage 第 4/5/6 列、"
              "第 1/2/3/7/8 列不动；coverage 18,498 行不变；全表 [已证] 1,527→1,556、"
              "atlas 内 1,521→1,550、atlas 外仍 6；面板 S22 proved 69→87、S06 126→130、"
              "S20 46→53；strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；不 git commit）；")
ln1 = lines[0]
assert ln1.startswith("# PANEL — R14 coverage"), ln1[:40]
lines[0] = "# PANEL — R14 coverage" + TITLE_NOTE + ln1[len("# PANEL — R14 coverage"):]

# ---- Line 17: 全表/atlas [已证] row ----
edit_line(17, "**1,527 / 1,521**", "**1,556 / 1,550**",
          insert_note_after="| **1,556 / 1,550** | ")

# ---- Main panel rows ----
# S06 line 60
edit_line(60, "| 123 | 14.52 | 126 | 14.88 |", "| 123 | 14.52 | 130 | 15.35 |",
          insert_note_after="| 123 | 14.52 | 130 | 15.35 | ")
# S20 line 74
edit_line(74, "| 42 | 10.24 | 46 | 11.22 |", "| 42 | 10.24 | 53 | 12.93 |",
          insert_note_after="| 42 | 10.24 | 53 | 12.93 | ")
# S22 line 76
edit_line(76, "| 34 | 0.70 | 69 | 1.42 |", "| 34 | 0.70 | 87 | 1.79 |",
          insert_note_after="| 34 | 0.70 | 87 | 1.79 | ")
# TOTAL line 77
edit_line(77, "| **1372** | **10.62** | **1521** | **11.78** |",
              "| **1372** | **10.62** | **1550** | **12.00** |",
          insert_note_after="| **1372** | **10.62** | **1550** | **12.00** | ")

# ---- Strict double table rows ----
edit_line(110, "| S06 | 847 | 126 | 14.88 | **111** | **13.11** |",
               "| S06 | 847 | 130 | 15.35 | **115** | **13.58** |")
edit_line(124, "| S20 | 410 | 46 | 11.22 | **34** | **8.29** |",
               "| S20 | 410 | 53 | 12.93 | **41** | **10.00** |")
edit_line(126, "| S22 | 4851 | 69 | 1.42 | **26** | **0.54** |",
               "| S22 | 4851 | 87 | 1.79 | **44** | **0.91** |")
edit_line(127, "| **TOTAL** | **12916** | **1521** | **11.78** | **1204** | **9.32** |",
               "| **TOTAL** | **12916** | **1550** | **12.00** | **1233** | **9.55** |")

# ---- strict section narrative: add M66 note after the M65 note line (line 141) ----
M66_STRICT_NOTE = (
    "> 📌 **M66 并表实算说明**：本表 S06 proved/strict 111→115（proved 126→130）、"
    "S20 34→41（proved 46→53）、S22 26→44（proved 69→87）、"
    "TOTAL 1,204→1,233（proved 1,521→1,550）均按盘上实算；"
    "本次并入 29 行新语义均不含字面 `[未证]`（核 delta 第 4 列），strict 随 proved 同增（S06 +4、S20 +7、S22 +18、TOTAL +29）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)
# find the M65 line by ASCII anchor and insert after it
m65_idx = None
for i, ln in enumerate(lines):
    if "M65 并表实算说明" in ln:
        m65_idx = i
        break
assert m65_idx is not None, "M65 note line not found"
lines.insert(m65_idx+1, M66_STRICT_NOTE)

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
open(P,"wb").write(new_raw)
print("sha after:", sha256(P))
print("bytes after:", len(new_raw))
print("lines:", len(lines))
print("inserted strict note after line", m65_idx+1)
