# -*- coding: utf-8 -*-
"""M71 PANEL.md edits: numeric/remark updates + verbatim M71 disclosure after M70 disclosure."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
CARD  = os.path.join(ROOT, "_cards", "M71-MERGE.md")

# --- extract M71 disclosure block verbatim from card (fenced block under '必须追加的第三条披露') ---
with open(CARD, "rb") as f:
    card_lines = f.read().decode("utf-8").split("\n")
h = next(i for i,l in enumerate(card_lines) if "必须追加的第三条披露" in l)
fence1 = next(i for i in range(h, len(card_lines)) if card_lines[i].strip() == "```")
fence2 = next(i for i in range(fence1+1, len(card_lines)) if card_lines[i].strip() == "```")
disc = card_lines[fence1+1:fence2]   # verbatim lines
print("extracted disclosure lines:", len(disc))
for i,l in enumerate(disc):
    print(f"  D{i+1}: {l[:80]!r}")
assert len(disc) == 5, len(disc)
assert disc[0].startswith("> ⚠️ **M71 披露：")
assert disc[-1].startswith("> 另需账：")

# --- load PANEL ---
with open(PANEL, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")

REMARK = ("M71 并表 NAMED_PUSH_AUDIT12 PASS 11 行（S22_B4 工厂族）；"
          "S22 named 池至此清空（B1 18 + B2 18 + B3 13 + B4 13 + B5 9 = 71 = 全池），"
          "B5 的 9 行 vector 族四环齐全 0（③b 全败于 {0,1} AL 布尔）")
EV = "evidence_path 改指 NAMED_PUSH_AUDIT12/VERDICT.md"

repls = [
 # 1) title line prepend
 ("# PANEL — R14 coverageM70 并表 11 行（",
  "# PANEL — R14 coverageM71 并表 11 行（NAMED_PUSH_AUDIT12 PASS 11 行（S22_B4 工厂族），均 atlas 内，"
  "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
  "全表 [已证] 1,591→1,602、atlas 内 1,585→1,596、atlas 外仍 6；面板 S22 proved 98→109、strict 55→66；"
  "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；" + REMARK + "；" + EV + "；"
  "④ 严格读法收紧将翻转 ≥21 行已披露未执行、待成文规则；不 git commit）；M70 并表 11 行（"),
 # 2) 全表 [已证]/atlas 内 cell + remark
 ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,591 / 1,585** | M70 并表",
  "| 全表 `[已证]` / atlas 内 `[已证]` | **1,602 / 1,596** | " + REMARK + "；" + EV + "；M70 并表"),
 # 3) S22 main row
 ("| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 98 | 2.02 | M70 并表",
  "| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 109 | 2.25 | " + REMARK + "；" + EV + "；M70 并表"),
 # 4) TOTAL main row
 ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1585** | **12.27** | M70 并表",
  "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1596** | **12.36** | " + REMARK + "；" + EV + "；M70 并表"),
 # 5) S22 strict row
 ("| S22 | 4851 | 98 | 2.02 | **55** | **1.13** | 2426 | — | — |",
  "| S22 | 4851 | 109 | 2.25 | **66** | **1.36** | 2426 | — | — |"),
 # 6) TOTAL strict row
 ("| **TOTAL** | **12916** | **1585** | **12.27** | **1268** | **9.82** | — | **3/22** | **1/22** |",
  "| **TOTAL** | **12916** | **1596** | **12.36** | **1279** | **9.90** | — | **3/22** | **1/22** |"),
]
for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, (cnt, old[:70])
    text = text.replace(old, new, 1)
    print(f"replaced (1x): {old[:60]!r}")

# --- insert M71 disclosure immediately after M70 disclosure block (last line) ---
m70_last = "> ⇒ 引用这批行时，不得表述为「该工厂函数被外部调用并检查其返回码」。"
cnt = text.count(m70_last)
assert cnt == 1, cnt
text = text.replace(m70_last, m70_last + "\n" + "\n".join(disc), 1)
print("inserted M71 disclosure after M70 disclosure last line")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

# report line numbers of inserted disclosure
new_lines = text.split("\n")
idx71 = [i+1 for i,l in enumerate(new_lines) if l.startswith("> ⚠️ **M71 披露：")]
print("M71 disclosure line numbers (1-based):", idx71)
assert len(idx71) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
