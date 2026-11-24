#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_subject.py — 最后一击：四环文档的「主体 entry」是否落在 675 里（只读）。

上一脚本只按**文件名**找 PROOF 文件，漏了两类：
  (a) 合并式文档 `PROOFS.md`（一个文件含多个 entry 的 ①②③④ 章节）
  (b) 文件名不带 entry、但内部有 `① ENTRY: atlas entry=<entry>` 这类主体行
本脚本对**所有**含四环的文本文件，提取其「主体 entry」集合，再与 675 求交。
主体 entry 的三个来源（与 PROBE_802_ANCHOR 的 A1/A3/A4 同源）：
  - `PROOF <entry>` 头行 / `PROOF_<entry>` 文件名
  - `① ENTRY: ... entry=<entry>`（四环文档的第①环）
  - `OWNER_DISK=..\t..` 后的名称行首 entry
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
RING = ["①", "②", "③", "④"]

import csv
with open(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"), encoding="utf-8", newline="") as fh:
    _all = list(csv.DictReader(fh, delimiter="\t"))
entry_set = {r["entry"].lower() for r in _all}
rows = [r for r in _all if r.get("class") == "R_TRACE_ONLY"]
buckets = {}
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    buckets[f[0].lower()] = f
zero = set(buckets)

# 所有含四环的文本文件（不限 PROOF 命名）
rel_out = os.path.relpath(OUT, LEAD).replace("\\", "/")
cmd = ["rg", "-l", "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
       "-e", "①", "-e", "④", "--glob", "!.git/**"]
for ext in sorted(M.PRIMARY_EXT):
    cmd += ["--iglob", "*" + ext]
cmd += ["--glob", "!" + rel_out + "/**", "."]
p = subprocess.run(cmd, cwd=LEAD, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=1800)
cands = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                for l in p.stdout.splitlines() if l.strip()})
print(f"[in] 含 ① 与 ④ 的 external 文本文件 {len(cands)} 个（已排除本卡产物）")

SUBJ_PATS = [
    re.compile(r"^\s*#*\s*proof\s+(?:0x)?([0-9a-f]{8})\b", re.I),        # PROOF 004D7330
    re.compile(r"^\s*#*\s*proof\s+(?:0x)?([0-9a-f]{6,7})\b", re.I),      # 短形式
    re.compile(r"①\s*ENTRY\s*:[^\n]{0,80}?entry\s*=\s*(?:0x)?([0-9a-f]{8})", re.I),
    re.compile(r"^\s*#{1,6}\s+(?:0x)?([0-9a-f]{8})\b", re.I),            # md 小节标题
    re.compile(r"^\s*(?:0x)?([0-9a-f]{8})\s*=*\s*(?:PROOF|proof)", re.I),
]
SH = M.short_map_of(entry_set)

def to8(tok):
    t = tok.lower()
    if t in entry_set:
        return t
    if t in SH:
        return SH[t]
    return None

hits675 = collections.defaultdict(list)
n_ring_file = 0
for f in cands:
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(4 * 1024 * 1024)
    except OSError:
        continue
    if not all(c in txt for c in ("①", "④")):
        continue
    n_ring_file += 1
    subs = set()
    for line in txt.splitlines()[:4000]:
        for pat in SUBJ_PATS:
            m = pat.search(line)
            if m:
                e8 = to8(m.group(1))
                if e8:
                    subs.add(e8)
    for e in subs & zero:
        hits675[e].append(f)

print(f"[ring] 真含 ①+④ 的文件 {n_ring_file} 个")
print(f"[find] 675 行中「被四环文档以主体形态点名」= {len(hits675)} 行")
for e, fs in sorted(hits675.items())[:20]:
    print(f"        {e} ← {fs[:3]}")
print(f"[out] 详情见 _proof_subject.json")
json.dump(dict(n_cands=len(cands), n_ring_file=n_ring_file,
               rows_named_as_subject=sorted(hits675),
               detail={k: v for k, v in hits675.items()}),
          open(os.path.join(OUT, "_proof_subject.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
