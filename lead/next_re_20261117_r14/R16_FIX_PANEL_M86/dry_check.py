#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dry check: confirm OLD_BLOCK matches the real backup lines 214..221 exactly,
and confirm the codepoints used in NEW_LINES come from the card verbatim."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_edit as a

backup = a.BACKUP.read_bytes()
text = backup.decode("utf-8")
lines = text.split("\n")
# 1-based line 214..221 -> index 213..220
real_block = ("\n".join(lines[213:221]) + "\n").encode("utf-8")
print("OLD_BLOCK == real lines 214..221 :", a.OLD_BLOCK == real_block)
print("OLD_BLOCK occurrences in backup :", backup.count(a.OLD_BLOCK))
print("line 214 marker:", lines[213])
print("line 219 old   :", lines[218])
print("line 221 old   :", lines[220])

card = Path(__file__).resolve().parent.parent / "_cards" / "R16-FIX-PANEL-M86.md"
ctext = card.read_text(encoding="utf-8")
# Find the A-B token in the card and show codepoints
for tok in ["A\u2212B", "A-B", "\u2463 \u6d3b\u8868\u69fd\u4f4d\u89c1\u8bc1", "\u26a0\ufe0f"]:
    print("card contains %r : %s" % (tok, tok in ctext))
# print codepoints around 'A' near 'B =' in card line 56
for ln in ctext.split("\n"):
    if "\u53e3\u5f84 A \u7684\u5df2\u77e5\u5f02\u8d28\u6027" in ln:
        i = ln.find("A")
        # locate the A directly before B
        j = ln.find("B =")
        print("card A-B substring:", repr(ln[j-3:j+3]))
        print("codepoints:", [hex(ord(c)) for c in ln[j-3:j+3]])
        break
