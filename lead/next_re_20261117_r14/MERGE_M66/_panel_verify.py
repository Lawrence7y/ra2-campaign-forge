# -*- coding: utf-8 -*-
"""Verify PANEL.md final state - print key lines with UTF-8 output to a file."""
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\_panel_verify.txt"
lines = open(P, encoding="utf-8").read().split("\n")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("TOTAL LINES: %d\n\n" % len(lines))
    for n in (1, 17, 60, 74, 76, 77, 110, 124, 126, 127, 141, 142):
        f.write("===== LINE %d =====\n%s\n\n" % (n, lines[n-1]))
    # also check all key numeric anchors exist
    checks = {
        "L17 1556/1550": "**1,556 / 1,550**" in lines[16],
        "L60 130/15.35": "| 123 | 14.52 | 130 | 15.35 |" in lines[59],
        "L74 53/12.93": "| 42 | 10.24 | 53 | 12.93 |" in lines[73],
        "L76 87/1.79": "| 34 | 0.70 | 87 | 1.79 |" in lines[75],
        "L77 TOTAL 1550/12.00": "| **1372** | **10.62** | **1550** | **12.00** |" in lines[76],
        "L110 S06 strict 130/115": "| S06 | 847 | 130 | 15.35 | **115** | **13.58** |" in lines[109],
        "L124 S20 strict 53/41": "| S20 | 410 | 53 | 12.93 | **41** | **10.00** |" in lines[123],
        "L126 S22 strict 87/44": "| S22 | 4851 | 87 | 1.79 | **44** | **0.91** |" in lines[125],
        "L127 TOTAL strict 1550/1233": "| **TOTAL** | **12916** | **1550** | **12.00** | **1233** | **9.55** |" in lines[126],
        "L1 M66 note present": "M66 并表 29 行" in lines[0],
        "L142 strict note present": "M66 并表实算说明" in lines[141],
        "no stale 1521/1,521 in L77": "**1521**" not in lines[76] and "1,521→" not in lines[76].split("M66")[0],
    }
    f.write("===== CHECKS =====\n")
    for k,v in checks.items():
        f.write(("PASS" if v else "FAIL") + "  " + k + "\n")
print("wrote", OUT)
