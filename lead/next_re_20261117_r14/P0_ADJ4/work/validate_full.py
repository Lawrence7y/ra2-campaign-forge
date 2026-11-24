#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full confusion matrix of criterion PI on all P0_RESIDUAL FUNC/NOT_FUNC rows.
Diagnosis aid for the 95% FUNC rate (do not fudge -- verify criterion soundness)."""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK)
sys.path.insert(0, HERE)
import res2_common as C
from criterion import Engine, load_resid

def main():
    pe = C.PE()
    eng = Engine(pe)
    rr = load_resid()
    stats = collections.Counter()
    fp = []
    fn = []
    for r in rr:
        va = int(r["addr"], 16)
        f = eng.features(va)
        truth = r["verdict"]
        pred = "FUNC" if f["func"] else "NOT_FUNC"
        stats[(truth, pred)] += 1
        if truth == "NOT_FUNC" and pred == "FUNC":
            fp.append((r, f))
        if truth == "FUNC" and pred == "NOT_FUNC":
            fn.append((r, f))
    print("== confusion matrix (truth -> pred) ==")
    for k in sorted(stats):
        print("  %-12s -> %-12s : %d" % (k[0], k[1], stats[k]))
    nfp = len(fp); nfn = len(fn)
    print("false-positive (truth NOT_FUNC, pred FUNC) =", nfp)
    print("false-negative (truth FUNC, pred NOT_FUNC) =", nfn)
    print("\n-- FP sample (up to 25) --")
    for r, f in fp[:25]:
        print("  %s %-14s head=%-8s g1a=%d g1b=%d c1=%d c2=%d c3=%d c4=%d c5=%d" % (
            r["addr"], r["subkind"], f["first_mn"], f["g1a"], f["g1b"],
            f["c1"], f["c2"], f["c3"], f["c4"], f["c5"]))
    print("\n-- FN sample (up to 25) --")
    for r, f in fn[:25]:
        print("  %s %-14s head=%-8s g1a=%d g1b=%d c1=%d c2=%d c3=%d c4=%d c5=%d" % (
            r["addr"], r["subkind"], f["first_mn"], f["g1a"], f["g1b"],
            f["c1"], f["c2"], f["c3"], f["c4"], f["c5"]))

if __name__ == "__main__":
    main()
