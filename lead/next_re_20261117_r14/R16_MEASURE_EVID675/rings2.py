#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rings2.py — 四环检查（剔除台账自指；只读）。

rings.py 的第一版把 coverage.tsv 等**台账列标题里的 ①②③④** 当成了四环证据，
导致 675/675 全部"命中"——这是假阳性，本脚本修掉：
  - 剔除 file_kind()==selfref 的文件（coverage*/resolve/classification_trace/度量产物）
  - 只保留 **external** 文件里的环标记
  - 并区分"文件里真有 ①②③④ 四段结构"与"只出现一两个符号"
最后按 PROOF_* 命名约定交叉验一遍。
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mev675 as M

OUT = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(OUT)
LEAD = os.path.dirname(R14)
RING = ["①", "②", "③", "④"]

rows = M.load_rows(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"))
entry_set = {r["entry"].lower() for r in rows}
hits = M.load_hits(os.path.join(OUT, "_hits_primary.tsv"), entry_set)

buckets = {}
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    buckets[f[0].lower()] = f

# 675 行的 external 命中文件
zero_files = collections.defaultdict(set)
for e in buckets:
    for rel, _ln, _t in hits.get(e, []):
        if M.file_kind(rel) == "external":
            zero_files[e].add(rel)
all_ext = sorted({f for fs in zero_files.values() for f in fs})
print(f"[in] 675 行的 external 命中文件 {len(all_ext)} 个")

# 逐个文件读环标记（只读前 2MB，够用）
ring_of = {}
for f in all_ext:
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(4 * 1024 * 1024)
    except OSError:
        continue
    got = "".join(c for c in RING if c in txt)
    if got:
        ring_of[f] = got

print(f"[ring] external 文件里含环标记的 {len(ring_of)} 个")
both = {f: r for f, r in ring_of.items() if "①" in r and "④" in r}
print(f"[ring] 其中同时含 ① 与 ④ 的 {len(both)} 个")
four = {f: r for f, r in ring_of.items() if all(c in r for c in RING)}
print(f"[ring] 四环齐全的 {len(four)} 个")
for f, r in list(four.items())[:10]:
    print(f"        {r}  {f}")

# 675 行里，谁的文件命中 these
rows_four = sorted(e for e in zero_files if zero_files[e] & set(four))
rows_both = sorted(e for e in zero_files if zero_files[e] & set(both))
print(f"[row ] 675 行中命中「四环齐全文件」的 = {len(rows_four)}: {rows_four[:10]}")
print(f"[row ] 675 行中命中「①+④ 文件」的 = {len(rows_both)}: {rows_both[:10]}")

# PROOF_* 命名约定交叉验证
proof = [f for f in all_ext if "proof" in os.path.basename(f).lower()]
print(f"[proof] external 命中文件里名字带 PROOF 的 = {len(proof)}: {proof[:10]}")

# 全树 PROOF_ 文件总数（不看命中，看盘上到底有多少四环文档）
import subprocess
p = subprocess.run(["rg", "--files", "--hidden", "--no-ignore", "--no-ignore-vcs",
                    "--glob", "!.git/**", "-g", "*PROOF*", "-g", "*proof*", "."],
                   cwd=LEAD, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=600)
all_proof = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                    for l in p.stdout.splitlines() if l.strip()})
print(f"[proof] lead 全树 PROOF* 文件 {len(all_proof)} 个")

# 这些 PROOF 文件里出现的 675 entry（以主体形态或任意形态）
cov675 = collections.defaultdict(list)
for f in all_proof:
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(2 * 1024 * 1024).lower()
    except OSError:
        continue
    for t in set(M.HEX_TOKEN.findall(txt)):
        if t in buckets:
            cov675[t].append(f)
print(f"[proof] 覆盖到的 675 entry 数 = {len(cov675)}")
for e, fs in list(cov675.items())[:10]:
    print(f"        {e} ← {fs[:3]}")

json.dump(dict(n_ext_files=len(all_ext),
               ring_files=ring_of, both_1_4=both, four_rings=four,
               rows_four=rows_four, rows_both_1_4=rows_both,
               proof_in_hits=proof, all_proof_files=all_proof,
               proof_covers_675=dict(cov675)),
          open(os.path.join(OUT, "_rings2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"[out] {os.path.join(OUT, '_rings2.json')}")
