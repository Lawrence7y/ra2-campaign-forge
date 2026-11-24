# -*- coding: utf-8 -*-
"""_rs_verbatim.py — R3: explicit verbatim comparison of the group-1 sentence
across ALL carriers that contain BOTH needles; prints EQUAL/NOT-EQUAL per
line plus differing codepoints, and cluster hashes. Read-only.
"""
import os, hashlib

ROOT = "D:/Project/ra2-campaign-forge/lead"
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
CANON = ("- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），"
         "**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 "
         "ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，"
         "**台账 :9704-9729 原文是否修订由台账所有者裁决**。")

def cp(c):
    return "<EOS>" if c is None else "%r U+%04X" % (c, ord(c))

if __name__ == "__main__":
    print("CANON len =", len(CANON), "sha256 =", hashlib.sha256(CANON.encode()).hexdigest())
    print()
    hits = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            ls = open(p, "rb").read().decode("utf-8", "replace").splitlines()
            for i, L in enumerate(ls, 1):
                if N1 in L and N2 in L:
                    hits.append((rel, i, L))
    print("lines containing BOTH needles (whole lead/, md only) =", len(hits))
    print()
    same, diff = [], []
    for rel, i, L in sorted(hits):
        if L == CANON:
            same.append((rel, i))
            print("EQUAL     %s:%d  sha256=%s" %
                  (rel, i, hashlib.sha256(L.encode()).hexdigest()))
        else:
            diff.append((rel, i, L))
    print()
    print("EQUAL count =", len(same), " NOT-EQUAL count =", len(diff))
    print()
    print("--- NOT-EQUAL: first differing codepoints vs canonical ---")
    for rel, i, L in diff:
        ds = []
        for k in range(max(len(CANON), len(L))):
            a = CANON[k] if k < len(CANON) else None
            b = L[k] if k < len(L) else None
            if a != b:
                ds.append((k, a, b))
        print("%s:%d  len=%d  ndiff=%d  first=%s" %
              (rel, i, len(L), len(ds),
               ", ".join("%d: %s->%s" % (k, cp(a), cp(b)) for k, a, b in ds[:4])))
        print("    text: %s" % L[:180])
