#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only survey of rollback-marked narrative candidates and U1 overlap."""
from __future__ import annotations
import os, re, sys
from collections import Counter, defaultdict

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
CAND = os.path.join(R14, "R17_R84_T1_NARRATIVE", "narrative_candidates.tsv")
UNSURE = os.path.join(R14, "R17_R84_T1_NARRATIVE", "unsure.tsv")
EXCL = os.path.join(R14, "R17_R84_T1_NARRATIVE", "should_exclude.tsv")
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)

def base(rel):
    return rel.rsplit("/", 1)[-1]

def strip_rollback(b):
    m = RE_ROLLBACK.search(b)
    if not m:
        return None
    stem = b[:m.start()]
    tail = b[m.end():]
    ext = ""
    if "." in tail:
        ext = tail[tail.index("."):]
    if not ext:
        mm = re.search(r"(\.[A-Za-z0-9]{1,5})$", b)
        ext = mm.group(1) if mm else ""
    return stem + ext

def load_rows(path, cols):
    out = []
    with open(path, encoding="utf-8", newline="") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        idx = {c: header.index(c) for c in cols}
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            out.append({c: p[i] for c, i in idx.items()})
    return out

peer = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        peer.add(base(line.split("\t", 1)[0]).lower())

cand = load_rows(CAND, ["rel", "bytes"])
unsure = {r["rel"]: r for r in load_rows(UNSURE, ["rel", "bytes", "type", "why"])}
excl = {r["rel"]: r for r in load_rows(EXCL, ["rel", "bytes", "type", "why"])}
for d in (unsure, excl):
    for r in d.values():
        r["bytes"] = int(r["bytes"])
for r in cand:
    r["bytes"] = int(r["bytes"])

marked_no_peer = []
marked_peer = []
unmarked = []
for r in cand:
    cur = strip_rollback(base(r["rel"]))
    if cur is None:
        unmarked.append(r)
    elif cur.lower() in peer:
        marked_peer.append(r)
    else:
        marked_no_peer.append(r)

def summarize(label, rows):
    print(label, len(rows), sum(r["bytes"] for r in rows))

summarize("CAND", cand)
summarize("MARKED_NO_PEER", marked_no_peer)
summarize("MARKED_PEER", marked_peer)
summarize("UNMARKED", unmarked)
summarize("UNSURE", unsure.values())
summarize("EXCL", excl.values())

cats = Counter()
catb = Counter()
for r in marked_no_peer:
    if r["rel"] in unsure:
        cats["U1"] += 1; catb["U1"] += r["bytes"]
    elif r["rel"] in excl:
        t = excl[r["rel"]]["type"]
        cats[t] += 1; catb[t] += r["bytes"]
    else:
        cats["K1_or_other"] += 1; catb["K1_or_other"] += r["bytes"]
print("MARKED_NO_PEER categories")
for k in sorted(cats):
    print(" ", k, cats[k], catb[k])

uc = Counter(); ub = Counter()
for rel, r in unsure.items():
    cur = strip_rollback(base(rel))
    if cur is None:
        uc["no_rollback"] += 1; ub["no_rollback"] += int(r["bytes"])
    elif cur.lower() in peer:
        uc["rollback_peer"] += 1; ub["rollback_peer"] += int(r["bytes"])
    else:
        uc["rollback_no_peer"] += 1; ub["rollback_no_peer"] += int(r["bytes"])
print("UNSURE categories")
for k in sorted(uc):
    print(" ", k, uc[k], ub[k])

print("UNSURE why prefixes")
wc = Counter()
wb = Counter()
for r in unsure.values():
    w = r["why"].split("（")[0].split(";")[0]
    wc[w] += 1; wb[w] += int(r["bytes"])
for k in sorted(wc):
    print(" ", k, wc[k], wb[k])

print("MARKED_NO_PEER rows:")
for r in sorted(marked_no_peer, key=lambda x: x["rel"]):
    cls = "U1" if r["rel"] in unsure else (excl[r["rel"]]["type"] if r["rel"] in excl else "K1_or_other")
    print(f"{r['rel']}\t{r['bytes']}\t{cls}\t{strip_rollback(base(r['rel']))}")
