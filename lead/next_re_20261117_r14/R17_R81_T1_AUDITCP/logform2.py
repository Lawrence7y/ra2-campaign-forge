#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""logform2.py — R44-T1：C′ 里「执行日志形态、但名字/路径判据都没命中、靠 P0 兜底」的件 —— 只读

我方判据（4 种形态，各自可复现）：
  F1  '[cmd]'  与 '--- stdout' 与 '[exit]' 同时出现在前 8 KiB（跑批包装器回显）
  F2  '[exit]' 与 '--- stdout' 同时出现
  F3  前 8 KiB 里形如 'XXXXXXXX@XXXXXXXX' 的地址对 >= 20 个（脚本汇总输出，非原始反汇编）
  F4  行首 PASS/FAIL/OK/STEP 判词 >= 20 行
前置过滤：basename 不含 stdout/stderr（E1 名字判据抓不到这一批）。
只统计，不改分类。只写本目录 logform2.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
LEAD = r"D:\Project\ra2-campaign-forge\lead"
AUD = os.path.dirname(os.path.abspath(__file__))
import audit_sample as AS

fh = open(os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv"),
          encoding="utf-8")
hdr = fh.readline().rstrip("\n").split("\t")
rows = [dict(zip(hdr, l.rstrip("\n").split("\t"))) for l in fh]

RE_STDIO = re.compile(r"std(out|err)", re.I)
RE_ADDR = re.compile(r"[0-9A-Fa-f]{8}@[0-9A-Fa-f]{8}")
RE_VERD = re.compile(r"(?m)^\s*(PASS|FAIL|OK|STEP)\b")

FORMS = {
    "F1_cmd_capture_exit": lambda t: ("[cmd]" in t and "--- stdout" in t and "[exit]" in t),
    "F2_capture_exit": lambda t: ("--- stdout" in t and "[exit]" in t),
    "F3_addr_pairs20": lambda t: len(RE_ADDR.findall(t)) >= 20,
    "F4_verdict_lines20": lambda t: len(RE_VERD.findall(t)) >= 20,
}
res = {}
allhit = set()
for name, f in FORMS.items():
    n = bs = outside = 0
    bs_out = 0
    for r in rows:
        rel = r["rel"]
        if RE_STDIO.search(rel.rsplit("/", 1)[-1]):
            continue
        h = AS.head(rel)
        if not h:
            continue
        t = h.decode("utf-8", "replace")
        if not f(t):
            continue
        n += 1
        bs += int(r["bytes"])
        lab, why = AS.rejudge(rel)[:2]
        if lab == "C′" and why.startswith("P0"):
            outside += 1
            bs_out += int(r["bytes"])
            allhit.add(rel)
    res[name] = dict(n=n, bytes=bs, p0_kept_n=outside, p0_kept_bytes=bs_out)
res["union_p0_kept"] = dict(n=len(allhit),
                            bytes=sum(int(r["bytes"]) for r in rows if r["rel"] in allhit),
                            share_of_Cprime_bytes=round(
                                sum(int(r["bytes"]) for r in rows if r["rel"] in allhit) / 1363708720, 4))
json.dump(res, open(os.path.join(AUD, "logform2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
