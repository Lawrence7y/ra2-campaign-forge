# -*- coding: utf-8 -*-
"""M60 Part 2: fix PANEL.md strict dual-column table (L103-L127) + append ruling note."""
import os, hashlib

PANEL = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/PANEL.md"

with open(PANEL, "rb") as f:
    b = f.read()
assert b[:3] != b"\xef\xbb\xbf"
s = b.decode("utf-8")
assert "\r" not in s, "unexpected CR in PANEL"
lines = s.split("\n")  # trailing newline -> final ''
assert lines[-1] == "", "PANEL does not end with newline"
lines = lines[:-1]

# exact old -> new for the 6 table rows (only cells named by the card change)
REPL = {
    "| S02 | 330 | 34 | 10.30 | **4** | **1.21** | 165 | — | — |":
    "| S02 | 330 | 35 | 10.61 | **5** | **1.52** | 165 | — | — |",

    "| S09 | 1051 | 114 | 10.85 | **89** | **8.47** | 526 | — | — |":
    "| S09 | 1051 | 114 | 10.85 | **97** | **9.23** | 526 | — | — |",

    "| S13 | 240 | 89 | 37.08 | **88** | **36.67** | 120 | — | — |":
    "| S13 | 240 | 100 | 41.67 | **99** | **41.25** | 120 | — | — |",

    "| S19 | 355 | 20 | 5.63 | **11** | **3.10** | 178 | — | — |":
    "| S19 | 355 | 27 | 7.61 | **18** | **5.07** | 178 | — | — |",

    "| S22 | 4851 | 55 | 1.13 | **12** | **0.25** | 2426 | — | — |":
    "| S22 | 4851 | 55 | 1.13 | **2** | **0.04** | 2426 | — | — |",

    "| **TOTAL** | **12916** | **1457** | **11.28** | **1140** | **8.83** | — | **3/22** | **1/22** |":
    "| **TOTAL** | **12916** | **1490** | **11.54** | **1163** | **9.00** | — | **3/22** | **1/22** |",
}

# locate in the strict table region only (lines index 102..126 == file L103..L127)
region_start = next(i for i, l in enumerate(lines) if "## 严格口径双列表" in l)
hdr_i = next(i for i, l in enumerate(lines[region_start:], region_start) if l.startswith("| S | atlas_n |"))
total_i = next(i for i, l in enumerate(lines[hdr_i:], hdr_i) if l.startswith("| **TOTAL** |"))
print("strict table region: header L%d, TOTAL L%d" % (hdr_i + 1, total_i + 1))
assert hdr_i + 1 == 103 and total_i + 1 == 127, (hdr_i, total_i)

# verify each old line appears exactly once and lies in the strict table region
for old, new in REPL.items():
    hits = [i for i, l in enumerate(lines) if l == old]
    assert len(hits) == 1, "old line not unique (%d hits): %s" % (len(hits), old)
    assert hdr_i <= hits[0] <= total_i, "line outside strict table: %s" % old
    lines[hits[0]] = new

# locate M58 note (the last > note in the block after the table) and append M60 ruling note after it
m58_idx = next(i for i, l in enumerate(lines) if l.startswith("> 📌 **界向更正（M58）**"))
assert total_i < m58_idx
note = ("> 📌 **M60 旧截面修正**：本表 S02（34/4→35/5）、S09（strict 89→97）、"
        "S13（89/100、88/99）、S19（20/27、11/18）、S22（strict 12→2）、"
        "TOTAL（proved 1457→1490、strict→1163）各行曾停留在早先截面，已按盘上重算更正；"
        "S22 的 strict 下降是因为其 55 行已证中 53 行语义自陈未证。"
        "**修正后达标判定未发生翻转，严格口径仍仅 S17**。教训记入错源 ㉙（引用旧截面）。")
assert not any("M60 旧截面修正" in l for l in lines), "M60 note already present"
lines.insert(m58_idx + 1, note)

out = "\n".join(lines) + "\n"
with open(PANEL, "wb") as f:
    f.write(out.encode("utf-8"))
print("PANEL updated. bytes after=%d sha256 after=%s" % (len(out.encode("utf-8")), hashlib.sha256(out.encode("utf-8")).hexdigest().upper()))
print("M60 note inserted at L%d" % (m58_idx + 2))
