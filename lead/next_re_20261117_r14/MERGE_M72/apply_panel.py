# -*- coding: utf-8 -*-
"""M72 PANEL.md edits: numeric/remark updates + M72 strict note + ㉓ positive record."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")

REMARK = ("M72 并表 NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11），"
          "evidence_path 分别改指两审计 VERDICT；S09_B1 的 1 行未审不并")

M72_TITLE = (
    "# PANEL — R14 coverageM72 并表 11 行（NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ "
    "NAMED_PUSH_AUDIT14 PASS 4 行（S11），均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,602→1,613、atlas 内 1,596→1,607、atlas 外仍 6；"
    "面板 S07 proved 67→74、strict 44→51，S11 proved 28→32、strict 27→31；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；"
    + REMARK + "；不 git commit）；"
)

M72_STRICT_NOTE = (
    "> 📌 **M72 并表实算说明**：本表 S07 proved/strict 67→74 / 44→51（74/804=9.20%、51/804=6.34%）、"
    "S11 proved/strict 28→32 / 27→31（32/368=8.70%、31/368=8.42%）、"
    "TOTAL proved/strict 1,596→1,607 / 1,279→1,290（1,607/12,916=12.44%、1,290/12,916=9.99%）均按盘上实算；"
    "本次并入 11 行新语义均不含字面 `[未证]`（核两 delta 第 4 列，A 组 S07 7 行 + B 组 S11 4 行），"
    "strict 随 proved 同增（S07 +7、S11 +4、TOTAL +11）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)

M72_23_NOTE = (
    "> 📌 **M72 ㉓ 正向记录**："
    "S07 有 2 行真触发㉓陷阱（同一虚表也被析构器写入 00490406 / 006DC475），"
    "因执行器 ④ 锚点取在行外构造器（0048E93B / 006D1D54）而未触雷 ⇒ ㉓ 不是形式检查，是真会命中的判据。"
)

with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

repls = [
    # 1) title line prepend M72 before M71
    ("# PANEL — R14 coverageM71 并表 11 行（",
     M72_TITLE + "M71 并表 11 行（"),
    # 2) 全表/atlas cell + remark
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,602 / 1,596** | M71 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,613 / 1,607** | " + REMARK + "；M71 并表"),
    # 3) S07 main row: proved 67->74, pct 8.33->9.20
    ("| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 67 | 8.33 | named(S-R14) 587/804=73.01%、proved 67/804=8.33；",
     "| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 74 | 9.20 | " + REMARK + "；named(S-R14) 587/804=73.01%、proved 67/804=8.33；"),
    # 4) S11 main row: proved 28->32, pct 7.61->8.70
    ("| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 28 | 7.61 | M34 降级 1 行（0075AC80），proved 29→28/368=7.61%；",
     "| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 32 | 8.70 | " + REMARK + "；M34 降级 1 行（0075AC80），proved 29→28/368=7.61%；"),
    # 5) TOTAL main row: proved 1596->1607, pct 12.36->12.44
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1596** | **12.36** | M71 并表",
     "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1607** | **12.44** | " + REMARK + "；M71 并表"),
    # 6) S07 strict row
    ("| S07 | 804 | 67 | 8.33 | **44** | **5.47** | 402 | — | — |",
     "| S07 | 804 | 74 | 9.20 | **51** | **6.34** | 402 | — | — |"),
    # 7) S11 strict row
    ("| S11 | 368 | 28 | 7.61 | **27** | **7.34** | 184 | — | — |",
     "| S11 | 368 | 32 | 8.70 | **31** | **8.42** | 184 | — | — |"),
    # 8) TOTAL strict row
    ("| **TOTAL** | **12916** | **1596** | **12.36** | **1279** | **9.90** | — | **3/22** | **1/22** |",
     "| **TOTAL** | **12916** | **1607** | **12.44** | **1290** | **9.99** | — | **3/22** | **1/22** |"),
]
for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, (cnt, old[:80])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:60])

# --- insert M72 notes immediately after M71 disclosure last line ---
m71_last = "> 另需账：该族 `AddRef`/`Release` 是 `mov eax,1; ret 4` 桩，**Release 实际不释放**；「失败 Release 新建对象」走的是 vt+0x20（slot8 删除析构器，`push 1`），不是 Release。"
cnt = text.count(m71_last)
assert cnt == 1, cnt
text = text.replace(m71_last, m71_last + "\n" + M72_STRICT_NOTE + "\n" + M72_23_NOTE, 1)
print("inserted M72 strict note + ㉓ positive record after M71 disclosure last line")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
i23 = [i+1 for i,l in enumerate(new_lines) if l.startswith("> 📌 **M72 ㉓ 正向记录**：")]
isn = [i+1 for i,l in enumerate(new_lines) if l.startswith("> 📌 **M72 并表实算说明**：")]
print("M72 strict note line(s):", isn)
print("M72 ㉓ note line(s):", i23)
assert len(i23) == 1 and len(isn) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
