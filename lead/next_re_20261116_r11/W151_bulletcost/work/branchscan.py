# -*- coding: utf-8 -*-
"""W151: framing-independent branch scan: find every rel8/rel32 branch (call/jmp/jcc/
loop/jecxz) whose target equals one of the given addresses. Works regardless of how
Ghidra framed (or failed to frame) the code.
Usage: python branchscan.py 0x55b8f0 [more...]
"""
import os, sys, struct

ROOT = r"D:\Project\ra2-campaign-forge"
img = open(os.path.join(ROOT, r"ra2youli\gamemd.exe"), "rb").read()
IB = 0x400000
TOFF, TLEN = 0x1000, 0x3DF38D
text = img[TOFF:TOFF + TLEN]

wanted = {}
for a in sys.argv[1:]:
    wanted[int(a, 16)] = []

JCC32 = set([0x0F80 + i for i in range(16)])


def note(tgt, site, kind):
    if tgt in wanted:
        wanted[tgt].append((site, kind))


for i in range(len(text)):
    op = text[i]
    # rel8
    if 0x70 <= op <= 0x7F or op == 0xEB or 0xE0 <= op <= 0xE3:
        if i + 2 <= len(text):
            rel = struct.unpack("<b", text[i + 1:i + 2])[0]
            note(IB + TOFF + i + 2 + rel, IB + TOFF + i,
                 "jcc8" if 0x70 <= op <= 0x7F else ("jmp8" if op == 0xEB else "loop8"))
    # rel32: E8/E9
    if op in (0xE8, 0xE9) and i + 5 <= len(text):
        rel = struct.unpack("<i", text[i + 1:i + 5])[0]
        note(IB + TOFF + i + 5 + rel, IB + TOFF + i, "call32" if op == 0xE8 else "jmp32")
    # rel32: 0F 8x
    if op == 0x0F and i + 6 <= len(text) and text[i + 1] in JCC32:
        rel = struct.unpack("<i", text[i + 2:i + 6])[0]
        note(IB + TOFF + i + 6 + rel, IB + TOFF + i, "jcc32")

for tgt in wanted:
    v = wanted[tgt]
    print("### target %08x : %d refs" % (tgt, len(v)))
    for site, kind in sorted(v):
        print("    %s from %08x" % (kind, site))
    if not v:
        print("    (none)")
