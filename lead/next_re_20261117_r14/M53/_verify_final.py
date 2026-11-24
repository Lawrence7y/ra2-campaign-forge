# -*- coding: utf-8 -*-
"""M53 self-check: recompute DOD nominal/strict lists from raw data; gather final file stats."""
import csv, re, os, sys, hashlib, json
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN  = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

def stats(p):
    raw = open(p, "rb").read()
    m = os.path.getmtime(p)
    mt = datetime.fromtimestamp(m).strftime("%Y-%m-%d %H:%M:%S.") + ("%03d" % (int(m*1000)%1000))
    return dict(bytes=len(raw), lf=raw.count(b"\n"),
                sha=hashlib.sha256(raw).hexdigest(), mtime=mt)

def main():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip(): atlas.add(ne(p[0]))
    with open(COV, encoding="utf-8-sig", newline="") as f:
        cov = list(csv.reader(f, delimiter="\t"))[1:]
    import collections, math
    d = collections.defaultdict(collections.Counter)
    for r in cov:
        if len(r) < 8: continue
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas: continue
        name = r[2].strip(); sem = r[3]; grade = r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_") and not RE_CSUB.search(name):
            d[s]["named_S14"] += 1
            if not RE_SLOT.search(name): d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem: d[s]["proved_strict_n"] += 1
    nominal, strict = [], []
    detail = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        c = d[s]; a = c["atlas_n"]
        tn, tp = math.ceil(0.9*a), math.ceil(0.5*a)
        ok_n = c["named_S14"] >= tn
        ok_p = c["proved_n"] >= tp
        ok_ps = c["proved_strict_n"] >= tp
        if ok_n and ok_p: nominal.append(s)
        if ok_n and ok_ps: strict.append(s)
        detail.append("%s named=%d/%d(thr%d) proved=%d/%d(thr%d) pstr=%d nom=%s strict=%s" % (
            s, c["named_S14"], a, tn, c["proved_n"], a, tp, c["proved_strict_n"],
            ok_n and ok_p, ok_n and ok_ps))
    print("NOMINAL (named R14 + proved):", ",".join(nominal), "=> %d/22" % len(nominal))
    print("STRICT  (named R14 + proved_strict):", ",".join(strict), "=> %d/22" % len(strict))
    print("\nPer-S detail:")
    for x in detail: print(" ", x)
    print("\nFILE STATS (after all edits):")
    print("  coverage.tsv:", json.dumps(stats(COV), ensure_ascii=False))
    print("  PANEL.md    :", json.dumps(stats(PAN), ensure_ascii=False))
    # backup sha check
    for b in ["_hygiene/coverage.M53.bak", "_hygiene/PANEL.M53.bak"]:
        p = os.path.join(ROOT, b)
        print("  backup", b, "sha:", hashlib.sha256(open(p,"rb").read()).hexdigest())

main()
