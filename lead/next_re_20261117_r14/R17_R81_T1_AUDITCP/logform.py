#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""logform.py — R44-T1：C′ 里「不靠名字判据、靠 P0 兜底留下」的脚本日志形态件 —— 只读取证

只写本目录 logform.json。判据（我方定义，写清以便复现）：
  件不含 stdout/stderr 字样（名字判据 E1 抓不到），前 8 KiB 里同时出现 "--- stdout" 与 "[exit]"，
  ⇒ 内容是「[cmd] … / [exit] N / --- stdout+stderr ---」这种跑批日志，属执行流出物。
只统计，不改它的分类。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
LEAD = r"D:\Project\ra2-campaign-forge\lead"
AUD = os.path.dirname(os.path.abspath(__file__))
import audit_sample as AS

A = {}
fh = open(os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv"),
          encoding="utf-8")
hdr = fh.readline().rstrip("\n").split("\t")
for line in fh:
    r = dict(zip(hdr, line.rstrip("\n").split("\t")))
    A[r["rel"]] = r

fm = re.compile(r"std(out|err)", re.I)
hits = []
n_scan = 0
for rel in A:
    if fm.search(rel.rsplit("/", 1)[-1]):
        continue
    head = AS.head(rel)
    if not head:
        continue
    n_scan += 1
    txt = head.decode("utf-8", "replace")
    if "--- stdout" in txt and "[exit]" in txt:
        hits.append(dict(rel=rel, bytes=int(A[rel]["bytes"]),
                         n_stdout=txt.count("--- stdout"), n_exit=txt.count("[exit]"),
                         first=txt.split("\n")[0][:110],
                         mine=AS.rejudge(rel)[:2]))
hits.sort(key=lambda x: -x["bytes"])
out = dict(rule="basename 不含 stdout/stderr；前 8 KiB 同时含 '--- stdout' 与 '[exit]'",
           n_scanned=n_scan, n_hits=len(hits), b_hits=sum(h["bytes"] for h in hits),
           in_Cprime=sum(1 for h in hits if h["mine"][0] == "C′"),
           top=hits[:12])
json.dump(out, open(os.path.join(AUD, "logform.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
