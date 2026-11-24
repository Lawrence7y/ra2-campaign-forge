#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generalizability: apply criterion PI to a deterministic >=30 sample of the
REMAINING 5,498 UNDECIDABLE rows (exclude the 100 already adjudicated).
Report FUNC/NOT_FUNC split and 'confidence' (strong vs weak verdict)."""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK); sys.path.insert(0, HERE)
import res2_common as C
from criterion import Engine

ENUM = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv"
N_SAMPLE = 40

def load_enum_und():
    rows = []
    with open(ENUM, encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip(): continue
            p = dict(zip(h, ln.rstrip("\n").split("\t")))
            if p["verdict"] == "UNDECIDABLE":
                rows.append(p)
    rows.sort(key=lambda r: int(r["address"], 16))
    return rows

def verdict(f):
    # strong/weak based on which channels decide
    if f["func"]:
        if f["c2"]:
            return "FUNC", "strong"   # all channels agree
        return "FUNC", "weak"          # jcc target but otherwise entry-like
    else:
        if (not f["c1"]) or (not f["c3"]):
            return "NOT_FUNC", "strong"  # branch-first or epilogue-head
        return "NOT_FUNC", "weak"        # fails only C4/C5/C2 -- needs P1 review

def main():
    pe = C.PE()
    eng = Engine(pe)
    und = load_enum_und()
    remaining = und[100:]
    print("remaining UNDECIDABLE after first 100 =", len(remaining))
    # deterministic evenly-spaced sample of 40
    sample = []
    for k in range(N_SAMPLE):
        idx = (k * len(remaining)) // N_SAMPLE
        sample.append(remaining[idx])
    # dedupe indices (should be unique for n>=40)
    print("sample size =", len(sample), " first=%s last=%s" % (sample[0]["address"], sample[-1]["address"]))
    cnt = collections.Counter()
    weak_rows = []
    for r in sample:
        va = int(r["address"], 16)
        f = eng.features(va)
        v, conf = verdict(f)
        cnt[(v, conf)] += 1
        if conf == "weak":
            weak_rows.append((r, f, v))
    print("\n== sample verdict distribution ==")
    for k in sorted(cnt):
        print("  %-10s %-7s : %d" % (k[0], k[1], cnt[k]))
    n_func = sum(v for (vv, c), v in cnt.items() if vv == "FUNC")
    n_not = sum(v for (vv, c), v in cnt.items() if vv == "NOT_FUNC")
    n_strong = sum(v for (vv, c), v in cnt.items() if c == "strong")
    n_weak = sum(v for (vv, c), v in cnt.items() if c == "weak")
    print("\nFUNC = %d/%d ; NOT_FUNC = %d/%d" % (n_func, len(sample), n_not, len(sample)))
    print("strong = %d/%d ; weak = %d/%d" % (n_strong, len(sample), n_weak, len(sample)))
    print("\nprojection: of %d remaining rows, decidable(strong) ~= %.0f ; need-review(weak) ~= %.0f" % (
        len(remaining), n_strong / len(sample) * len(remaining), n_weak / len(sample) * len(remaining)))
    print("\n-- weak rows --")
    for r, f, v in weak_rows:
        print("  %s %-9s head=%-8s g1a=%d g1b=%d c1=%d c2=%d c3=%d c4=%d c5=%d" % (
            r["address"], v, f["first_mn"], f["g1a"], f["g1b"],
            f["c1"], f["c2"], f["c3"], f["c4"], f["c5"]))

if __name__ == "__main__":
    main()
