# -*- coding: utf-8 -*-
"""_rs_lines.py — numbered line dumps with repr, for verbatim evidence."""
import sys, os

ROOT = "D:/Project/ra2-campaign-forge/lead/"

def dump(rel, ranges):
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    ls = b.decode("utf-8", "replace").splitlines()
    print("=" * 100)
    print("FILE:", rel, "bytes=", len(b), "lines=", len(ls))
    for a, z in ranges:
        print("--- lines %d..%d ---" % (a, z))
        for i in range(a, min(z, len(ls)) + 1):
            print("%4d | %s" % (i, ls[i-1]))

if __name__ == "__main__":
    dump("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
         [(105, 130), (205, 225)])
    dump("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
         [(1, 41)])
    dump("ledger_appendix_20261108/_lad_tpl.md",
         [(140, 160)])
