# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
lines = open(PANEL, encoding="utf-8").read().split("\n")
print("=== FULL TITLE (L1) ===")
print(repr(lines[0]))
print("=== DISCLOSURE SECTION L155-L172 ===")
for i in range(155, 173):
    if i <= len(lines):
        print(f"L{i}: {lines[i-1][:500]}")
print("=== M75 card disclosure block ===")
card = open(os.path.join(ROOT,"_cards","M75-MERGE.md"), encoding="utf-8").read().split("\n")
h = next(i for i,l in enumerate(card) if "必须追加的第五条披露" in l)
f1 = next(i for i in range(h,len(card)) if card[i].strip()=="```")
f2 = next(i for i in range(f1+1,len(card)) if card[i].strip()=="```")
for i in range(f1+1,f2): print("  ",repr(card[i]))
print("=== full L17,L57,L60,L70,L75,L77,L107,L110,L120,L125,L127 prefixes ===")
for ln in (17,57,60,70,75,77,107,110,120,125,127):
    s=lines[ln-1]
    print(f"L{ln} len={len(s)} head={s[:120]!r}")
