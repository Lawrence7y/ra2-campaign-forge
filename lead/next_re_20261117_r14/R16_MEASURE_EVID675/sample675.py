#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sample675.py — 确定性抽样 ≤18 行，输出上下文供人工核（只读产物 + 只读 lead/）。

配额（因 WEAK/NONE 实测为 0，改抽「外部命中最少」的行做反向核）：
  STRONG 6 / MEDIUM 4 / 外部命中最少 2 = 12 行 ≤ 18
抽样规则确定可复现：桶内按 entry 升序等距取。
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mev675 as M

OUT = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(OUT)
LEAD = os.path.dirname(R14)
HDR = ["entry", "subsystem", "name", "bucket", "file", "lineno", "ctx",
       "auto_code", "auto_why", "n_ext", "n_files", "note"]

rows = M.load_rows(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"))
entry_set = {r["entry"].lower() for r in rows}
hits = M.load_hits(os.path.join(OUT, "_hits_primary.tsv"), entry_set)

buckets = {}
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    buckets[f[0].lower()] = f

# 需要结构：只给 STRONG 行的锚点文件
strong = {e: b for e, b in buckets.items() if b[3] == "CTX_STRONG"}
anchor_files = sorted({b[5].split(";")[0].strip() for b in strong.values()})
anchor_files = [f for f in anchor_files if f and f != "-"]
structs = {f: M.build_struct(LEAD, f, entry_set) for f in anchor_files}

def pick(xs, k):
    if not xs:
        return []
    if len(xs) <= k:
        return list(xs)
    step = len(xs) / k
    return [xs[int(i * step)] for i in range(k)]

# 从 buckets 的 note 里取真实锚点（锚点=file:line [code]）
import re
def anchor_of(note):
    m = re.search(r"锚点=([^:]+(?:/[^:]+)*):(\d+) \[([^\]]+)\]", note)
    if not m:
        return None, 0, ""
    return m.group(1), int(m.group(2)), m.group(3)

sel = []
for e in pick(sorted(strong), 6):
    b = strong[e]
    f, ln, code = anchor_of(b[6])
    sel.append((e, b, f, ln, code, "STRONG"))

med = {e: b for e, b in buckets.items() if b[3] == "CTX_MEDIUM"}
for e in pick(sorted(med), 4):
    b = med[e]
    f, ln, code = anchor_of(b[6])
    sel.append((e, b, f, ln, code, "MEDIUM"))

# 反向核：外部命中数最少的 2 行
few = sorted(buckets.items(), key=lambda kv: (int(kv[1][4]), kv[0]))[:2]
for e, b in few:
    f, ln, code = anchor_of(b[6])
    sel.append((e, b, f, ln, code, "FEWHITS"))

print(f"[sample] {len(sel)} 行")
out = []
for e, b, f, ln, code, tag in sel:
    ctx = ""
    if f:
        for rel, l, text in hits.get(e, []):
            if rel == f and l == ln:
                ctx = text.strip()[:200]
                break
    if not ctx:
        # 退化：取前 3 个命中的第一条
        hs = [h for h in hits.get(e, []) if M.file_kind(h[0]) == "external"]
        if hs:
            f2, l2, t2 = hs[0]
            ctx = f"〔首条 external 命中 {f2}:{l2}〕" + t2.strip()[:180]
    out.append([b[0], b[1], b[2], b[3], f or "-", str(ln), ctx,
                code, b[6].split("；")[1] if "；" in b[6] else "",
                b[4], b[6].split("命中 ")[1].split(" 处")[0] if "命中 " in b[6] else "",
                tag])

with open(os.path.join(OUT, "_sample_draft.tsv"), "w", encoding="utf-8", newline="") as fh:
    fh.write("\t".join(HDR) + "\n")
    for r in out:
        fh.write("\t".join(r) + "\n")
print(f"[out] _sample_draft.tsv")
for r in out:
    print(f"\n=== {r[0]} {r[3]} tag={r[11]} anchor={r[4]}:{r[5]} [{r[7]}] files={r[9]}")
    print(f"    {r[6][:190]}")
