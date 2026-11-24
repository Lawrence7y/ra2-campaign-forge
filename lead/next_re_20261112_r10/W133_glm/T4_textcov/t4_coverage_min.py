#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t4_coverage_min.py -- T4 minimal deliverable, run before cancellation.
Recomputes atlas coverage of gamemd.exe .text only (no disassembly).
Writes uncovered_runs.tsv into this directory. Deterministic, exit 0.
"""
import os
import sys
import hashlib

ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = os.path.dirname(os.path.abspath(__file__))
TEXT_START = 0x401000
TEXT_END = 0x7E038D          # exclusive, per task


def merge(iv):
    iv = sorted((a, b) for a, b in iv if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            if b > out[-1][1]:
                out[-1][1] = b
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def load_rows():
    rows = []
    with open(ATLAS, encoding="utf-8", newline="") as f:
        f.readline()  # header: entry size n_instr n_callers n_callees is_fnptr ...
        for line in f:
            p = line.rstrip("\n").split("\t")
            if not p or not p[0].strip():
                continue
            try:
                ent = int(p[0], 16)
            except ValueError:
                continue
            try:
                sz = int(p[1], 16)
                hexok = True
            except ValueError:
                sz, hexok = int(p[1]), False
            rows.append((ent, sz, hexok))
    return rows


def overlap_rate(iv):
    """fraction of intervals whose end overshoots the next interval's start"""
    iv = sorted(iv)
    bad = tot = 0
    for i in range(len(iv) - 1):
        tot += 1
        if iv[i][1] > iv[i + 1][0]:
            bad += 1
    return bad / max(tot, 1)


def main():
    rows = load_rows()
    total = TEXT_END - TEXT_START
    res = {}
    for name, conv in (("hex", (lambda e, s: (e, e + s))),
                       ("dec", (lambda e, s: (e, e + s)))):
        pass
    # both interpretations of the size column
    iv_hex = [(e, e + s) for e, s, _ in rows if TEXT_START <= e < TEXT_END]
    iv_dec = [(e, e + s) for e, s, _ in rows]  # same parse; interpret below
    # rows were parsed with int(p,16) first; re-derive decimal sizes
    rows_dec = []
    with open(ATLAS, encoding="utf-8", newline="") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if not p or not p[0].strip():
                continue
            try:
                ent = int(p[0], 16)
            except ValueError:
                continue
            try:
                sz = int(p[1])          # decimal
            except ValueError:
                continue
            rows_dec.append((ent, sz))
    iv_dec = [(e, e + s) for e, s in rows_dec if TEXT_START <= e < TEXT_END]

    stats = []
    for name, iv, n_rows in (("size-as-hex", iv_hex, len(rows)),
                             ("size-as-dec", iv_dec, len(rows_dec))):
        m = merge([(a, min(b, TEXT_END)) for a, b in iv])
        cov = sum(b - a for a, b in m)
        ov = overlap_rate([(a, b) for a, b in iv])
        stats.append((name, n_rows, cov, ov, m))

    # pick interpretation with lower adjacent-overlap rate
    stats.sort(key=lambda t: (t[3], t[0]))
    name, nrows, cov, ov, m = stats[0]
    other = stats[1]
    unc = []
    cur = TEXT_START
    for a, b in m:
        if a > cur:
            unc.append((cur, a))
        cur = max(cur, b)
    if cur < TEXT_END:
        unc.append((cur, TEXT_END))
    unc_bytes = total - cov

    with open(os.path.join(OUT, "uncovered_runs.tsv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("start\tend\tsize\n")
        for a, b in unc:
            f.write("%X\t%X\t%d\n" % (a, b, b - a))

    buckets = [(1, 15), (16, 63), (64, 255), (256, 1023), (1024, 4095),
               (4096, 65535), (65536, 10 ** 9)]
    keys = ["1-15", "16-63", "64-255", "256-1K", "1K-4K", "4K-64K", ">64K"]
    hist = dict.fromkeys(keys, 0)
    for a, b in unc:
        for k, (lo, hi) in zip(keys, buckets):
            if lo <= b - a <= hi:
                hist[k] += 1
                break
    top = sorted(unc, key=lambda r: r[1] - r[0], reverse=True)[:10]
    print("chosen_interpretation=%s rows=%d overlap_rate=%.4f"
          % (name, nrows, ov))
    print("alt=%s cov=%d overlap_rate=%.4f" % (other[0], other[2], other[3]))
    print("total=%d covered=%d (%.3f%%) uncovered=%d (%.3f%%) runs=%d"
          % (total, cov, 100.0 * cov / total, unc_bytes,
             100.0 * unc_bytes / total, len(unc)))
    print("claim79.5=%s" % ("RIGHT" if abs(100.0 * cov / total - 79.5) < 0.5
                            else "WRONG"))
    print("run_hist=%s" % hist)
    print("top_runs=" + ";".join("%X-%X:%d" % (a, b, b - a) for a, b in top))
    print("atlas_sha=%s" % hashlib.sha256(open(ATLAS, "rb").read()).hexdigest().upper())
    return 0


if __name__ == "__main__":
    sys.exit(main())
