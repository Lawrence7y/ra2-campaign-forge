#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Line-parse q2_heads_67.txt -> concise current-version evidence TSV."""
from __future__ import annotations
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = os.path.join(HERE, "q2_heads_67.txt")
OUT = os.path.join(HERE, "current_evidence_67.tsv")
LEAD = r"D:\Project\ra2-campaign-forge\lead"
A_TSV = os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")

a_rel = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        a_rel.add(line.split("\t", 1)[0].replace("\\", "/"))

lines = open(HEAD, encoding="utf-8").read().splitlines()
starts = []
for i, ln in enumerate(lines):
    m = re.match(r"^===== \[(\d+)\] (.+?) \| (\d+) B \| read=(\S+) len=(\d+) =====$", ln)
    if m:
        starts.append((i, m.groups()))
starts.append((len(lines), None))

PATH_RE = re.compile(r"(?:lead\\)?(next_re_\d+_r\d+/[\w\-./\\]+\.(?:tsv|json|md|txt)|[\w\-./\\]+\.(?:md|tsv|json))", re.I)

with open(OUT, "w", encoding="utf-8", newline="\n") as o:
    o.write("idx\trel\tbytes\tsuperseded_text\tcurrent_ref\tin_A\tevidence\n")
    for (s, g), (e, _) in zip(starts, starts[1:]):
        idx, rel, size, got, ln = g
        body = lines[s+1:e]
        ev = []
        cur = ""
        for j, ln2 in enumerate(body):
            if any(k in ln2 for k in ("本目录已作废", "请勿引用", "当前权威版本", "已被", "GOAL-3T · 三目标持续推进")):
                ev.append(ln2.strip()[:180])
            if "当前权威版本" in ln2 and j+1 < len(body):
                m2 = PATH_RE.search(body[j+1])
                if m2:
                    cur = m2.group(1).replace("\\", "/")
        if not cur and "GOAL-3T · 三目标持续推进" in "\n".join(body):
            cur = "GOAL_THREE_TARGETS_20261018.md"
        ina = "Y" if cur and (cur in a_rel or cur.rsplit("/",1)[-1] in {p.rsplit("/",1)[-1] for p in a_rel}) else "N"
        o.write(f"{idx}\t{rel}\t{size}\t{'Y' if any('本目录已作废' in x or '请勿引用' in x for x in ev) else 'N'}\t{cur}\t{ina}\t{' | '.join(ev[:2])[:240]}\n")
print(f"wrote {OUT} sections={len(starts)-1}")
