#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recall2.py — 干净版召回验证：只用「全树 PROOF* 文件」集合 + 主体行正则。

思路：不做 evidence_path 解析，直接在 lead 全树所有名字含 proof 的文件上跑检测器，
看 11 个已知四环 entry 是否被找回。找回 ⇒ 检测器对"四环文档主体"有召回 ⇒ 675 的 0 可信。
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

# 注意：11 行四环行已修复为 R_OK，不在 R_TRACE_ONLY 里 —— 召回测试必须用**全量** entry 集合
KNOWN11 = ["0045a560", "0045a610", "0053c6a0", "005514b0", "00551560",
           "00557090", "00557140", "006b1850", "006b1900", "006b8660", "006b8710"]
import csv
with open(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"),
          encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh, delimiter="\t"))
entry_set = {r["entry"].lower() for r in rows} | set(KNOWN11)
SH = M.short_map_of(entry_set)

p = subprocess.run(["rg", "--files", "--hidden", "--no-ignore", "--no-ignore-vcs",
                    "--glob", "!.git/**", "--iglob", "*proof*", "."],
                   cwd=LEAD, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=600)
proof = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                for l in p.stdout.splitlines() if l.strip()})
print(f"[in] PROOF* 文件 {len(proof)} 个")

SUBJ_PATS = [
    re.compile(r"\bproof\s+(?:0x)?([0-9a-f]{8})\b", re.I),
    re.compile(r"\bproof\s+(?:0x)?([0-9a-f]{6,7})\b", re.I),
    re.compile(r"①\s*ENTRY\s*:[^\n]{0,90}?entry\s*=\s*(?:0x)?([0-9a-f]{8})", re.I),
    re.compile(r"^\s*#{1,6}\s+(?:0x)?([0-9a-f]{8})\b", re.I),
]

def to8(tok):
    t = tok.lower()
    return t if t in entry_set else SH.get(t)

found = collections.defaultdict(set)
for f in proof:
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        txt = open(full, "r", encoding="utf-8", errors="replace").read(2 * 1024 * 1024)
    except OSError:
        continue
    if not all(c in txt for c in ("①", "④")):
        continue
    for line in txt.splitlines():
        for pat in SUBJ_PATS:
            m = pat.search(line)
            if m:
                e8 = to8(m.group(1))
                if e8:
                    found[e8].add(f)

print(f"[recall] 检测器在四环 PROOF 文件里找回 {len(found)} 个 791 entry 的主体地位")
hit11 = [e for e in KNOWN11 if e in found]
print(f"[recall] 11 个已知四环行中找回 {len(hit11)}/11: {hit11}")
for e in KNOWN11:
    print(f"    {e} {'HIT ' if e in found else 'MISS'} {sorted(found.get(e, []))[:2]}")

json.dump(dict(n_proof=len(proof), detected={k: sorted(v) for k, v in found.items()},
               recall11=len(hit11)),
          open(os.path.join(OUT, "_recall.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 关键：这 11 个之外还找回了谁？会不会把 675 里的行误召回？
zero = set()
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    zero.add(f[0].lower())
others = sorted(set(found) - set(KNOWN11))
in675 = [e for e in others if e in zero]
print(f"\n[recall] 找回集合中不在 11 行的 {len(others)} 个，其中落在 675 里的 = {len(in675)}: {in675[:10]}")
