# -*- coding: utf-8 -*-
"""M67 PANEL.md verification: check every mandated edit landed correctly."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M67\PANEL.md.bak"
text = open(P, encoding="utf-8").read()
bak = open(BAK, encoding="utf-8").read()

NOTE_PARTS = [
    "M67 并表 NAMED_PUSH_AUDIT7 PASS 13 行（S20 8 + S06 5，evidence_path 改指 NAMED_PUSH_AUDIT7/VERDICT.md）",
    "0062FE90 表址按审计勘误改为 007E9D64",
    "S06 五行 ④ 由审计补证",
    "S12_B1 四行审计代理失败未审不并",
    "M67 按审计勘误改表址",
    "M67 备注：S06 五行 ④ 由 a-S20S06 审计补证，见 NAMED_PUSH_AUDIT7\\VERDICT.md",
]
for s in NOTE_PARTS:
    assert s in text, ("missing note part", s)
print("[OK] all 6 note parts present in PANEL.md")

checks = [
    ("title M67", "# PANEL — R14 coverageM67 并表 13 行" in text),
    ("L17 1,569/1,563", "| **1,569 / 1,563** |" in text),
    ("L17 old gone", "**1,556 / 1,550**" not in text),
    ("S06 main 135/15.94", "| S06 | 847 | 388 | 45.81 | 388 | 45.81 | 123 | 14.52 | 135 | 15.94 |" in text),
    ("S20 main 61/14.88", "| S20 | 410 | 399 | 97.32 | 399 | 97.32 | 42 | 10.24 | 61 | 14.88 |" in text),
    ("TOTAL main 1563/12.10", "| **1372** | **10.62** | **1563** | **12.10** |" in text),
    ("S06 strict row", "| S06 | 847 | 135 | 15.94 | **120** | **14.17** | 424 | — | — |" in text),
    ("S20 strict row", "| S20 | 410 | 61 | 14.88 | **49** | **11.95** | 205 | — | — |" in text),
    ("TOTAL strict row", "| **TOTAL** | **12916** | **1563** | **12.10** | **1246** | **9.65** | — | **3/22** | **1/22** |" in text),
    ("M67 strict note", "M67 并表实算说明" in text),
    ("no flip note", "达标判定未翻转" in text),
]
for name, ok in checks:
    print(("[OK] " if ok else "[FAIL] ") + name)
    assert ok, name

# verify no old numbers remain in strict table rows
assert "| S06 | 847 | 130 | 15.35 | **115** | **13.58** |" not in text
assert "| S20 | 410 | 53 | 12.93 | **41** | **10.00** |" not in text
assert "| **TOTAL** | **12916** | **1550** | **12.00** | **1233** | **9.55** |" not in text
print("[OK] old strict-table numbers removed")

# count appended notes (should be on L17, S06, S20, TOTAL main rows = 4 occurrences of the full combined note)
cnt = text.count("M67 并表 NAMED_PUSH_AUDIT7 PASS 13 行（S20 8 + S06 5")
print("combined-note occurrences:", cnt)
assert cnt == 4, cnt

print("\nALL PANEL CHECKS PASSED")
