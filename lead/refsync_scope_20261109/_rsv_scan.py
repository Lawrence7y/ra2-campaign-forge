"""_rsv_scan.py — FULLY INDEPENDENT carrier rescan.
Does not import or reuse the author's scripts. Own os.walk, own decode, own
line splitting, own counting. Reads the whole lead/ tree.
Run: python -I -X utf8 ".../_rsv_scan.py"
"""
import os, hashlib, sys
from collections import defaultdict

ROOT = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
VARIANT_NEEDLES = ["只能判『不可复现』", "不能定位当年错误步骤"]

def walk(exts, maxdepth):
    """yield (fullpath, relpath, dir_depth, file_depth)."""
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        ddepth = 0 if rel == "." else rel.count("/") + 1
        if maxdepth is not None and ddepth > maxdepth:
            dn[:] = []
            continue
        for f in fn:
            if exts and not any(f.lower().endswith(e) for e in exts):
                continue
            p = os.path.join(dp, f)
            if os.path.isfile(p):
                yield p, os.path.relpath(p, ROOT).replace("\\", "/"), ddepth, ddepth + 1

def scan(exts, maxdepth, needles, label):
    scanned = 0
    hits = defaultdict(list)   # rel -> [lineno]
    fp = {}
    depth_hist = defaultdict(int)
    for p, rel, dd, fd in walk(exts, maxdepth):
        with open(p, "rb") as fh:
            b = fh.read()
        if b"\x00" in b:
            continue
        scanned += 1
        depth_hist[dd] += 1
        txt = b.decode("utf-8", "replace")
        ls = txt.splitlines()
        ln = [i for i, L in enumerate(ls, 1) if any(n in L for n in needles)]
        if ln:
            hits[rel] = ln
            fp[rel] = (len(b), hashlib.sha256(b).hexdigest(), len(ls))
    total = sum(len(v) for v in hits.values())
    print(f"=== {label} ===")
    print(f"  exts={exts} max_dir_depth={maxdepth} needles={needles}")
    print(f"  scanned_files={scanned}  carrier_files={len(hits)}  hit_lines={total}")
    print(f"  md-by-dir-depth={dict(sorted(depth_hist.items()))}")
    print(f"  files_depth_le2 = {sum(v for k,v in depth_hist.items() if k+1<=2)}  dir_depth_le2 = {sum(v for k,v in depth_hist.items() if k<=2)}")
    print("  --- per file ---")
    for rel in sorted(hits):
        print(f"    {rel}  bytes={fp[rel][0]}  sha={fp[rel][1][:12]}…  lines={hits[rel]}")
    return scanned, len(hits), total, hits

print("################ INDEPENDENT FULL CARRIER RESCAN ################")
print()
a = scan([".md"], 2, NEEDLES, "A. AUTHOR SCOPE: .md, dir-depth<=2, exact 2 needles")
print()
b = scan([".md"], None, NEEDLES, "B. NO DEPTH CAP: .md whole lead/, exact 2 needles")
print()
c = scan([".md", ".txt", ".py", ".json"], None, NEEDLES, "C. ALL EXTS no depth cap, exact 2 needles")
print()
d = scan([".md"], None, VARIANT_NEEDLES, "D. .md no depth cap, CURLY-quote variant needles")
print()
e = scan([".md"], 2, VARIANT_NEEDLES, "E. .md dir-depth<=2, CURLY-quote variant needles")
print()
print("################ DELTAS ################")
print(f"  A(author d2 md)={a[1]} files / {a[2]} lines ; B(no-cap md)={b[1]} files / {b[2]} lines")
print(f"  B - A = {b[1]-a[1]} files / {b[2]-a[2]} lines")
extra_files = sorted(set(b[3]) - set(a[3]))
print(f"  B-only files ({len(extra_files)}): {extra_files}")
extra_lines = {r: b[3][r] for r in extra_files}
print(f"  B-only lines: {extra_lines}")
print(f"  C(allex no-cap)={c[1]} files / {c[2]} lines")
print(f"  D(.md no-cap curly variant)={d[1]} files / {d[2]} lines ; E(d2 curly)={e[1]} files / {e[2]} lines")
