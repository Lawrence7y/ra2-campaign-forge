# -*- coding: utf-8 -*-
"""Check REPORT.md §8 samples against delta.tsv col4 (byte-exact tail match)."""
import io, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.dirname(HERE) + os.sep + "R16_D1_WIDE_B1"
L = io.open(os.path.join(B1, "delta.tsv"), encoding="utf-8-sig").read().splitlines()
D = {ln.split("\t")[0]: ln.split("\t")[3] for ln in L[1:]}
rep = io.open(os.path.join(B1, "REPORT.md"), encoding="utf-8").read()
fence = "`" * 3
blocks = re.findall(re.escape(fence) + r"\n(.*?)\n" + re.escape(fence), rep, re.S)
print("fenced blocks:", len(blocks))
for b in blocks:
    s = b.strip()
    hits = [e for e in D if D[e].endswith(s)]
    sub = [e for e in D if s and s in D[e]]
    print("  block len=%d exact_tail_entry=%s substring_in=%s" % (len(s), hits or "-", sub or "-"))
    if not hits:
        print("    block head: %s" % s[:120])
        for e in sub:
            i = D[e].find(s)
            print("    first diff at %d for %s: report=%r delta=%r" % (
                i, e, s[max(0, i - 40):i + 40], D[e][max(0, i - 40):i + 40]))
