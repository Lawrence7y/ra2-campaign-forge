# -*- coding: utf-8 -*-
"""M73 PANEL.md edits: numeric/remark updates + M73 strict note."""
import os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")

REMARK = ("M73 并表 NAMED_PUSH_AUDIT15 PASS 2 行（S18 007B10C0 / S09 004F45B0，"
          "evidence_path 改指 NAMED_PUSH_AUDIT15/VERDICT.md；"
          "审计补证了 delta 缺失的 ②/④ 地址，并纠 004F45B0 的成功返回地址应为 0x4A3592）")

M73_TITLE = (
    "# PANEL — R14 coverageM73 并表 2 行（NAMED_PUSH_AUDIT15 PASS 2 行"
    "（S18 007B10C0 / S09 004F45B0），均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,613→1,615、atlas 内 1,607→1,609、atlas 外仍 6；"
    "面板 S18 proved 56→57、strict 46→47，S09 proved 114→115、strict 97→98；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；"
    + REMARK + "；不 git commit）；"
)

M73_STRICT_NOTE = (
    "> 📌 **M73 并表实算说明**：本表 S18 proved/strict 56→57 / 46→47（57/659=8.65%、47/659=7.13%）、"
    "S09 proved/strict 114→115 / 97→98（115/1051=10.94%、98/1051=9.32%）、"
    "TOTAL proved/strict 1,607→1,609 / 1,290→1,292（1,609/12,916=12.46%、1,292/12,916=10.00%）均按盘上实算；"
    "本次并入 2 行新语义均不含字面 `[未证]`（核两 delta 第 4 列），"
    "strict 随 proved 同增（S18 +1、S09 +1、TOTAL +2）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)

with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

repls = [
    # 1) title line prepend M73 before M72
    ("# PANEL — R14 coverageM72 并表 11 行（",
     M73_TITLE + "M72 并表 11 行（"),
    # 2) 全表/atlas cell + remark
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,613 / 1,607** | M72 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,615 / 1,609** | " + REMARK + "；M72 并表"),
    # 3) S09 main row: proved 114->115, pct 10.85->10.94
    ("| S09 | 1051 | 681 | 64.80 | 681 | 64.80 | 82 | 7.80 | 114 | 10.85 | M46 并表",
     "| S09 | 1051 | 681 | 64.80 | 681 | 64.80 | 82 | 7.80 | 115 | 10.94 | " + REMARK + "；M46 并表"),
    # 4) S18 main row: proved 56->57, pct 8.50->8.65
    ("| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 56 | 8.50 | M63 并表",
     "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 57 | 8.65 | " + REMARK + "；M63 并表"),
    # 5) TOTAL main row: proved 1607->1609, pct 12.44->12.46
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1607** | **12.44** | M72 并表",
     "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1609** | **12.46** | " + REMARK + "；M72 并表"),
    # 6) S09 strict row
    ("| S09 | 1051 | 114 | 10.85 | **97** | **9.23** | 526 | — | — |",
     "| S09 | 1051 | 115 | 10.94 | **98** | **9.32** | 526 | — | — |"),
    # 7) S18 strict row
    ("| S18 | 659 | 56 | 8.50 | **46** | **6.98** | 330 | — | — |",
     "| S18 | 659 | 57 | 8.65 | **47** | **7.13** | 330 | — | — |"),
    # 8) TOTAL strict row
    ("| **TOTAL** | **12916** | **1607** | **12.44** | **1290** | **9.99** | — | **3/22** | **1/22** |",
     "| **TOTAL** | **12916** | **1609** | **12.46** | **1292** | **10.00** | — | **3/22** | **1/22** |"),
]
for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, (cnt, old[:80])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:60])

# --- insert M73 strict note immediately after M72 ㉓ record line ---
m72_last = ("> 📌 **M72 ㉓ 正向记录**："
            "S07 有 2 行真触发㉓陷阱（同一虚表也被析构器写入 00490406 / 006DC475），"
            "因执行器 ④ 锚点取在行外构造器（0048E93B / 006D1D54）而未触雷 ⇒ ㉓ 不是形式检查，是真会命中的判据。")
cnt = text.count(m72_last)
assert cnt == 1, cnt
text = text.replace(m72_last, m72_last + "\n" + M73_STRICT_NOTE, 1)
print("inserted M73 strict note after M72 ㉓ record line")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
isn = [i+1 for i, l in enumerate(new_lines) if l.startswith("> 📌 **M73 并表实算说明**：")]
print("M73 strict note line(s):", isn)
assert len(isn) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
print("AFTER sha256:", hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
