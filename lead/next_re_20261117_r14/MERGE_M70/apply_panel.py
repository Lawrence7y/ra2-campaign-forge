# -*- coding: utf-8 -*-
"""M70 PANEL.md edits: numeric/remark updates + verbatim M70 disclosure after M69 disclosure."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
CARD  = os.path.join(ROOT, "_cards", "M70-MERGE.md")

# --- extract M70 disclosure block verbatim from card (lines 46-50, 1-based) ---
with open(CARD, "rb") as f:
    card_lines = f.read().decode("utf-8").split("\n")
# locate the fenced block under the '必须追加的第二条披露' heading
h = next(i for i,l in enumerate(card_lines) if "必须追加的第二条披露" in l)
fence1 = next(i for i in range(h, len(card_lines)) if card_lines[i].strip() == "```")
fence2 = next(i for i in range(fence1+1, len(card_lines)) if card_lines[i].strip() == "```")
disc = card_lines[fence1+1:fence2]   # verbatim lines
print("extracted disclosure lines:", len(disc))
for i,l in enumerate(disc):
    print(f"  D{i+1}: {l[:70]!r}")
assert len(disc) == 5, len(disc)
assert disc[0].startswith("> ⚠️ **M70 披露：")
assert disc[-1].startswith("> ⇒ 引用这批行时")

# --- load PANEL ---
with open(PANEL, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")

repls = [
 # 1) title line prepend
 ("# PANEL — R14 coverageM69 并表 7 行（",
  "# PANEL — R14 coverageM70 并表 11 行（NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），均 atlas 内，仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；全表 [已证] 1,580→1,591、atlas 内 1,574→1,585、atlas 外仍 6；面板 S22 proved 87→98、strict 44→55；strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；不 git commit）；M69 并表 7 行（"),
 # 2) 全表 [已证]/atlas 内 cell + remark
 ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,580 / 1,574** | M69 并表",
  "| 全表 `[已证]` / atlas 内 `[已证]` | **1,591 / 1,585** | M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md；M69 并表"),
 # 3) S22 main row
 ("| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 87 | 1.79 | M66 并表",
  "| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 98 | 2.02 | M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md；M66 并表"),
 # 4) TOTAL main row
 ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1574** | **12.19** | M69 并表",
  "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1585** | **12.27** | M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md；M69 并表"),
 # 5) S22 strict row
 ("| S22 | 4851 | 87 | 1.79 | **44** | **0.91** | 2426 | — | — |",
  "| S22 | 4851 | 98 | 2.02 | **55** | **1.13** | 2426 | — | — |"),
 # 6) TOTAL strict row
 ("| **TOTAL** | **12916** | **1574** | **12.19** | **1257** | **9.73** | — | **3/22** | **1/22** |",
  "| **TOTAL** | **12916** | **1585** | **12.27** | **1268** | **9.82** | — | **3/22** | **1/22** |"),
]
for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, (cnt, old[:60])
    text = text.replace(old, new, 1)
    print(f"replaced (1x): {old[:50]!r}")

# --- insert M70 disclosure immediately after M69 disclosure block ---
m69_last = "> 受影响行：`TClassFactory<T>::slot3` 同族、`DVC::Delete` 内联展开族，以及 `00442230` 等同构行（合计约 40 行量级）。**收紧口径需一次裁决 + 一次性整批处置，不得零散改判。**"
cnt = text.count(m69_last)
assert cnt == 1, cnt
text = text.replace(m69_last, m69_last + "\n" + "\n".join(disc), 1)
print("inserted M70 disclosure after M69 disclosure last line")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

# report line numbers of inserted disclosure
new_lines = text.split("\n")
idx70 = [i+1 for i,l in enumerate(new_lines) if l.startswith("> ⚠️ **M70 披露：")]
print("M70 disclosure line numbers (1-based):", idx70)
assert len(idx70) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
