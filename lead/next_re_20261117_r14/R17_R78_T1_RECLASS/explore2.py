#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""explore2.py — 深入：族内细分、目录结构、内容抽样入口。只写本目录。"""
from __future__ import annotations
import collections, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
def load(p):
    rows = []
    with open(p, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append(dict(rel=f[0], ext=f[1], bytes=int(f[2]), mtime_ns=f[3], selfkind=f[4]))
    return rows
RA = load(os.path.join(BASE, "files_tier_A_snap2.tsv"))
RC = load(os.path.join(BASE, "files_tier_C.tsv"))
setC = {r["rel"] for r in RC}

def segs(rel): return rel.split("/")

# 1) 顶层目录分布
print("=== 顶层目录分布（A） ===")
t = collections.Counter(); tb = collections.Counter()
for r in RA:
    s = segs(r["rel"])
    key = s[0] if len(s) > 1 else "(root)"
    t[key] += 1; tb[key] += r["bytes"]
for k, v in tb.most_common(40):
    print(f"{k:45s} n={t[k]:6d} b={v:12d}")

# 2) EVIDENCE 族细分：目录名里 EVIDENCE 的层级
print("\n=== EVIDENCE 族细分 ===")
ev = [r for r in RA if any(s.upper() == "EVIDENCE" for s in segs(r["rel"]))]
print("total", len(ev), sum(r["bytes"] for r in ev))
sub = collections.Counter(); subb = collections.Counter()
for r in ev:
    s = segs(r["rel"])
    i = [j for j, x in enumerate(s) if x.upper() == "EVIDENCE"][0]
    key = "/".join(s[:i]) + "/EVIDENCE/" + (s[i+1] if len(s) > i+2 else "<direct>")
    # 只保留到 EVIDENCE 下一层，避免过碎
    sub[key] += 1; subb[key] += r["bytes"]
print("distinct (父/EVIDENCE/子) :", len(sub))
for k, v in subb.most_common(30):
    print(f"{k:90s} n={sub[k]:5d} b={v:11d}")

# EVIDENCE 下的文件按扩展名+basename 形态
print("\n=== EVIDENCE 下 basename 形态 ===")
shape = collections.Counter(); shapeb = collections.Counter()
def shape_of(b):
    low = b.lower()
    m = re.search(r"(\.(?:txt|json|tsv|md|csv|log))$", low)
    e = m.group(1) if m else ""
    stem = low[:-len(e)] if e else low
    if re.search(r"\b(stdout|stderr)\b", stem) or "stdout" in stem or "stderr" in stem: return "stdout/stderr" + e
    if stem.endswith("_out"): return "*_out" + e
    if stem.endswith("_probe"): return "*_probe" + e
    if stem.endswith("_check"): return "*_check" + e
    if stem in ("report",): return "report" + e
    if stem.endswith("_report"): return "*_report" + e
    if "disasm" in stem: return "*disasm*" + e
    if "scan" in stem: return "*scan*" + e
    if "dump" in stem: return "*dump*" + e
    if stem in ("readme",): return "README" + e
    return "other" + e
for r in ev:
    k = shape_of(segs(r["rel"])[-1]); shape[k] += 1; shapeb[k] += r["bytes"]
for k, v in shapeb.most_common(30):
    print(f"{k:31s} n={shape[k]:5d} b={v:11d}")

# 3) R17_LEAD_BASELINE
print("\n=== R17_LEAD_BASELINE ===")
lb = [r for r in RA if "R17_LEAD_BASELINE" in segs(r["rel"])]
print("total", len(lb), sum(r["bytes"] for r in lb))
c = collections.Counter(); cb = collections.Counter()
for r in lb:
    b = segs(r["rel"])[-1]
    key = re.sub(r"\d+", "#", b)
    c[key] += 1; cb[key] += r["bytes"]
for k, v in cb.most_common(40):
    print(f"{k:60s} n={c[k]:4d} b={v:11d}")

# 4) _cards
print("\n=== _cards 细分 ===")
cd = [r for r in RA if "_cards" in segs(r["rel"])]
print("total", len(cd), sum(r["bytes"] for r in cd))
c = collections.Counter(); cb = collections.Counter()
for r in cd:
    s = segs(r["rel"])
    i = s.index("_cards")
    key = "/".join(s[:i]) + "/_cards" + ("/" + "/".join(s[i+1:-1]) if len(s) > i+2 else "")
    c[key] += 1; cb[key] += r["bytes"]
for k, v in cb.most_common(20):
    print(f"{k:70s} n={c[k]:4d} b={v:10d}")

# 5) bare REPORT.md 分布
print("\n=== basename==REPORT.md 分布 ===")
rp = [r for r in RA if segs(r["rel"])[-1] == "REPORT.md"]
print("total", len(rp), sum(r["bytes"] for r in rp))
c = collections.Counter(); cb = collections.Counter()
for r in rp:
    s = segs(r["rel"])
    key = s[0]
    c[key] += 1; cb[key] += r["bytes"]
for k, v in cb.most_common(20):
    print(f"{k:50s} n={c[k]:4d} b={v:10d}")
rp2 = [r for r in RA if segs(r["rel"])[-1].lower() == "report.md"]
print("case-insensitive total", len(rp2), sum(r["bytes"] for r in rp2))
