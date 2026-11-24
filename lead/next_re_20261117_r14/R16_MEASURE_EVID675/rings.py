#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rings.py — 四环检查 + S1_own_dump 质量体检（只读）。

问题：675 行里有没有**任何一个文件**既提到该 entry，又带 ①/②/③/④ 四环标记？
      若有，那才是「④ 已写在盘上、台账没连上」的候选（= PROBE_802_ANCHOR §5.4 里值 11 行的那种）。
另外给 S1_own_dump（文件反汇编起点 == 该 entry）的行做规模体检：多少行、是不是跑飞。
"""
import collections
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mev675 as M

OUT = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(OUT)
LEAD = os.path.dirname(R14)

rows = M.load_rows(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"))
entry_set = {r["entry"].lower() for r in rows}

judge = json.load(open(os.path.join(OUT, "_judge_primary.json"), encoding="utf-8"))
buckets = {}
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    buckets[f[0].lower()] = f

# ---- 1) 全树找「带 ① 和 ④」的文本文件 ----
cmd = ["rg", "-l", "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
       "-e", "①", "-e", "④",
       "--glob", "!.git/**"]
for ext in sorted(M.PRIMARY_EXT):
    cmd += ["--iglob", "*" + ext]
rel_out = os.path.relpath(OUT, LEAD).replace("\\", "/")
cmd += ["--glob", "!" + rel_out + "/**", "."]
p = subprocess.run(cmd, cwd=LEAD, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=1800)
ring_files = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                     for l in p.stdout.splitlines() if l.strip()})
print(f"[rings] 同时含 ① 与 ④ 的文本文件 {len(ring_files)} 个")
# 再按「四个标记分别出现」统计
cmd2 = ["rg", "-l", "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
        "-e", "①", "-e", "②", "-e", "③", "-e", "④", "--glob", "!.git/**"]
for ext in sorted(M.PRIMARY_EXT):
    cmd2 += ["--iglob", "*" + ext]
cmd2 += ["--glob", "!" + rel_out + "/**", "."]
p2 = subprocess.run(cmd2, cwd=LEAD, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=1800)
any_ring = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                   for l in p2.stdout.splitlines() if l.strip()})
print(f"[rings] 含任一 ①②③④ 的文本文件 {len(any_ring)} 个")

# ---- 2) 675 行里，谁的文件在 ring 集合里 ----
hits = M.load_hits(os.path.join(OUT, "_hits_primary.tsv"), entry_set)
ring_set = set(ring_files)
rows_with_ring = []
matched_rows_any = []
for e in [k for k in buckets if buckets[k][3] != "CTX_NONE"]:
    files = {h[0] for h in hits.get(e, [])}
    if files & ring_set:
        rows_with_ring.append((e, sorted(files & ring_set)[:3]))
    if files & set(any_ring):
        matched_rows_any.append(e)
print(f"[rings] 675 行中「命中文件里含 ①+④ 文件」= {len(rows_with_ring)} 行: {rows_with_ring[:10]}")
print(f"[rings] 675 行中「命中文件里含任一环标记文件」= {len(matched_rows_any)} 行")

# ---- 3) S1_own_dump 质量体检 ----
s1 = judge.get("strong675_own_dump", [])
print(f"\n[qlty] S1_own_dump = {len(s1)} 行，逐行规模体检：")
quality = collections.Counter()
detail = []
for d in judge.get("strong675_detail", []):
    if d["tier"] != "S1_own_dump":
        continue
    f = d["file"]
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh)
        sz = os.path.getsize(full)
    except OSError:
        n, sz = -1, -1
    q = ("tiny<1k" if 0 <= sz < 1024 else
         "ok<20k" if sz < 20000 else
         "big<200k" if sz < 200000 else "runaway>=200k")
    quality[q] += 1
    detail.append(dict(entry=d["entry"], file=f, lineno=d["lineno"], lines=n,
                       bytes=sz, quality=q,
                       basename_has_entry=(d["entry"][2:] in os.path.basename(f).lower()
                                           or d["entry"] in os.path.basename(f).lower())))
    print(f"  {d['entry']} L{d['lineno']:<6d} {n:>7d} 行 {sz:>9d}B {q:12s} {f}")
print(f"[qlty] 分布: {dict(quality)}")
nb = sum(1 for d in detail if d["basename_has_entry"])
print(f"[qlty] 其中文件名带该 entry（6 或 8 位）的 = {nb}/{len(detail)}")

json.dump(dict(ring_files=ring_files, any_ring_files=any_ring,
               rows_with_ring=rows_with_ring,
               n_rows_with_ring=len(rows_with_ring),
               n_rows_any_ring=len(matched_rows_any),
               s1_quality=dict(quality), s1_detail=detail),
          open(os.path.join(OUT, "_rings.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"[out] {os.path.join(OUT, '_rings.json')}")
