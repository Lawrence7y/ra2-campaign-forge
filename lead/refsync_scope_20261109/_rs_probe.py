# -*- coding: utf-8 -*-
"""_rs_probe.py — reproduce orchestrator full scan & verify needle variants.
Read-only over lead/. Zero live-machine, zero sampling code, hashlib only.
"""
import os, hashlib, sys

ROOT = os.path.abspath("D:/Project/ra2-campaign-forge/lead")

NEEDLES_A = [
    "只能判「不可复现」",
    "只能判『不可复现』",
    "不能定位当年错误步骤",
]

def md_files(maxdir):
    out = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        d = 0 if rel == "." else rel.count("/") + 1
        for f in fn:
            if f.lower().endswith(".md"):
                full = os.path.join(dp, f)
                out.append((full, os.path.relpath(full, ROOT).replace("\\", "/"), d))
    return out

def lines_of(p):
    with open(p, "rb") as fh:
        b = fh.read()
    return b, b.decode("utf-8", "replace").splitlines()

if __name__ == "__main__":
    allf = md_files(99)
    print("total md in lead/ (any depth) =", len(allf))
    dd = {}
    for _, rel, d in allf:
        dd[d] = dd.get(d, 0) + 1
    print("md-by-dir-depth:", dict(sorted(dd.items())))
    print("md-by-file-depth:", {k+1: v for k, v in sorted(dd.items())})
    print("file-depth<=2 =", sum(v for k, v in dd.items() if k+1 <= 2))
    print("dir-depth<=2  =", sum(v for k, v in dd.items() if k <= 2))
    ndirs = sum(1 for _ in os.walk(ROOT))
    dirs_le2 = sum(1 for dp, dn, fn in os.walk(ROOT)
                   if (0 if os.path.relpath(dp, ROOT) == "." else
                       os.path.relpath(dp, ROOT).count(os.sep) + 1) <= 2)
    print("total dirs incl root =", ndirs, " dirs depth<=2 =", dirs_le2)
    print()
    for n in NEEDLES_A:
        hits_files = set()
        hits_lines = 0
        for full, rel, d in allf:
            b, ls = lines_of(full)
            for i, L in enumerate(ls, 1):
                if n in L:
                    hits_files.add(rel)
                    hits_lines += 1
        print("NEEDLE", repr(n), "any-depth: files=", len(hits_files), "lines=", hits_lines)
    print()
    # combined (either needle), per depth
    for lim, label in [(2, "dir-depth<=2 (orchestrator)"), (99, "any depth")]:
        sel = [x for x in allf if x[2] <= lim] if lim == 2 else allf
        carriers = {}
        for full, rel, d in sel:
            b, ls = lines_of(full)
            ls_hit = [i for i, L in enumerate(ls, 1)
                      if any(n in L for n in NEEDLES_A[:1] + NEEDLES_A[2:])]
            # orchestrator needles: only the two exact strings
            ls_hit = [i for i, L in enumerate(ls, 1)
                      if ("只能判「不可复现」" in L) or ("不能定位当年错误步骤" in L)]
            if ls_hit:
                carriers[rel] = (len(b), ls_hit)
        print("== combined exact-2-needle,", label, ": scanned md =", len(sel),
              "carrier files =", len(carriers), "total hit lines =",
              sum(len(v[1]) for v in carriers.values()))
        for rel in sorted(carriers):
            print("   ", rel, "bytes=", carriers[rel][0], "lines=", carriers[rel][1])
        print()
