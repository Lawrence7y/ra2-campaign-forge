# -*- coding: utf-8 -*-
"""M53 helper: recompute named_S under two ::sub_ exclusion rules (read-only on COVERAGE/atlas).
Writes only inside M53\ (our write domain).
"""
import csv, re, os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT  = os.path.join(ROOT, "M53", "_recompute_named_out.json")

RE_SHORT = re.compile(r"::sub_[0-9A-Fa-f]+$")       # TASK B required rule
RE_8     = re.compile(r"::sub_[0-9A-Fa-f]{8}$")      # literal 8-hex rule (WRONG)

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def main():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))

    with open(COV, encoding="utf-8-sig", newline="") as f:
        cov = list(csv.reader(f, delimiter="\t"))[1:]

    named_short = {}   # S -> count
    named_8      = {}   # S -> count
    named_L      = {}
    atlas_n      = {}
    short_rows   = []   # rows excluded by short rule but NOT by literal-8 rule
    for r in cov:
        if len(r) < 8:
            continue
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        atlas_n[s] = atlas_n.get(s, 0) + 1
        name = r[2].strip()
        if name and not name.startswith("sub_"):
            named_L[s] = named_L.get(s, 0) + 1
            excl_short = bool(RE_SHORT.search(name))
            excl_8     = bool(RE_8.search(name))
            if not excl_short:
                named_short[s] = named_short.get(s, 0) + 1
            if not excl_8:
                named_8[s] = named_8.get(s, 0) + 1
            if excl_short and not excl_8:
                short_rows.append(dict(entry=r[0], S=s, name=name))

    Ss = sorted(k for k in atlas_n if re.match(r"^S\d\d$", k))
    rows = []
    for s in Ss:
        rows.append(dict(S=s, atlas_n=atlas_n[s],
                         named_short=named_short.get(s, 0),
                         named_8=named_8.get(s, 0),
                         diff=named_short.get(s, 0) - named_8.get(s, 0)))
    tot_short = sum(named_short.get(s, 0) for s in Ss)
    tot_8 = sum(named_8.get(s, 0) for s in Ss)
    tot_atlas = sum(atlas_n[s] for s in Ss)
    total = dict(S="TOTAL", atlas_n=tot_atlas,
                 named_short=tot_short, named_8=tot_8, diff=tot_short - tot_8)

    out = dict(rows=rows, total=total, short_rows=short_rows,
               note="diff = named_S(short-form) - named_S(literal-8)")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("S\tatlas_n\tnamed_short\tnamed_8\tdiff(short-8)")
    for r in rows:
        print("%s\t%d\t%d\t%d\t%d" % (r["S"], r["atlas_n"], r["named_short"], r["named_8"], r["diff"]))
    print("TOTAL\t%d\t%d\t%d\t%d" % (total["atlas_n"], total["named_short"], total["named_8"], total["diff"]))
    print("\nShort-form rows excluded by short rule but missed by literal-8 rule (%d rows):" % len(short_rows))
    for r in short_rows:
        print("  %s\t%s\t%s" % (r["entry"], r["S"], r["name"]))
    print("\nWrote", OUT)

main()
