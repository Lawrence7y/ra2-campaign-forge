#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prose.py — R44-T1：C′ 里「叙述体/判断体」件的规模估计 —— 只读，只写本目录 prose.json

我方判据（可复现）：
  P1a/P1b 均未命中（即不是对象抄本/对象事实表），且前 8 KiB 非空行里 >=25% 含中文，
  ⇒ 内容主体是叙述性文字（结论/判词/卡面），不是字节事实。
只做规模估计，不改分类。
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
RE_VA = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_CN = re.compile(r"[\u4e00-\u9fff]")

n = bs = 0
ex = []
for r in rows:
    rel = r["rel"]
    h = AS.head(rel)
    if not h:
        continue
    ls = [x for x in h.split(b"\n")[:200] if x.strip()]
    if not ls:
        continue
    va = sum(1 for x in ls if RE_VA.match(x.decode("utf-8", "replace"))
             or RE_VA2.match(x.decode("utf-8", "replace")))
    if va and va / len(ls) >= 0.6:
        continue
    low = rel.rsplit("/", 1)[-1].lower()
    if low.endswith((".tsv", ".csv")) and len(ls) >= 5:
        if sum(1 for x in ls if x.count(b"\t") >= 2) / len(ls) >= 0.7:
            continue
    cn = sum(1 for x in ls if RE_CN.search(x.decode("utf-8", "replace")))
    if cn / len(ls) < 0.25:
        continue
    if AS.rejudge(rel)[0] != "C′":
        continue
    n += 1
    bs += int(r["bytes"])
    if len(ex) < 8:
        ex.append(dict(rel=rel, bytes=int(r["bytes"]), cn_ratio=round(cn / len(ls), 2)))

out = dict(rule="P1a/P1b 未命中 且 前 8 KiB 非空行 >=25% 含中文 且 判为 C′",
           n=n, bytes=bs, share_of_Cprime_bytes=round(bs / 1363708720, 4), examples=ex)
json.dump(out, open(os.path.join(AUD, "prose.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
