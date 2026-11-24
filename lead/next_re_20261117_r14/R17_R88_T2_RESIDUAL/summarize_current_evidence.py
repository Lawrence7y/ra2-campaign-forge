#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize current-version evidence inside each U1 head."""
from __future__ import annotations
import os, re

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
HEAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q2_heads_67.txt")
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")

a_rel = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        a_rel.add(line.split("\t", 1)[0].replace("\\", "/"))

txt = open(HEAD, encoding="utf-8").read()
parts = re.split(r"\n===== \[(\d+)\] (.+?) \| (\d+) B \| read=(\S+) len=(\d+) =====\n", txt)
# parts[0] preamble, then 5 fields per section + body
paths = re.compile(r"(?:lead\\)?((?:next_re_[\w]+/)?[\w\-./\\]+?\.(?:tsv|json|md|txt))")
for i in range(1, len(parts), 5):
    idx, rel, size, got, ln, body = parts[i:i+6]
    cur = []
    for line in body.splitlines():
        if any(k in line for k in ("当前权威", "取代", "作废", "请勿引用", "GOAL-3T · 三目标持续推进")):
            cur.append(line.strip()[:240])
    refs = []
    for p in paths.findall(body):
        p = p.replace("\\", "/")
        if p.startswith("lead/"):
            p = p[5:]
        if p not in refs:
            refs.append(p)
    in_a = [p for p in refs if p in a_rel]
    print(f"[{idx}] {rel}")
    print("  evidence: " + (" | ".join(cur[:3]) if cur else "NONE"))
    print("  refs: " + (", ".join(refs[:6]) if refs else "NONE"))
    print("  in_A: " + (", ".join(in_a[:6]) if in_a else "NONE"))
