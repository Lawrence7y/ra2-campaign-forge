#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e1_pop.py — R44-T1：E1 判据候选人口（盘上实测），只读；只写本目录 e1_pop.json"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
LEAD = r"D:\Project\ra2-campaign-forge\lead"


def load(p):
    rows = []
    fh = open(p, encoding="utf-8")
    hdr = fh.readline().rstrip("\n").split("\t")
    for line in fh:
        rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    return rows


A = load(os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv"))
RE_UNDER = re.compile(r"_out\.[A-Za-z0-9]{1,5}$", re.I)
RE_DOT = re.compile(r"[.\-]out\.[A-Za-z0-9]{1,5}$", re.I)
RE_STDIO = re.compile(r"std(out|err)", re.I)

u = [r for r in A if RE_UNDER.search(r["rel"].rsplit("/", 1)[-1])]
d = [r for r in A if RE_DOT.search(r["rel"].rsplit("/", 1)[-1]) and not RE_UNDER.search(r["rel"].rsplit("/", 1)[-1])]
s = [r for r in A if RE_STDIO.search(r["rel"].rsplit("/", 1)[-1])]
res = dict(
    n_under=len(u), b_under=sum(int(r["bytes"]) for r in u),
    n_dot=len(d), b_dot=sum(int(r["bytes"]) for r in d),
    n_stdio=len(s), b_stdio=sum(int(r["bytes"]) for r in s),
    n_union=len({r["rel"] for r in u + d + s}),
    dot_examples=[r["rel"] for r in d[:8]],
)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e1_pop.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
