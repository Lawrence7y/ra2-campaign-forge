#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag.py — STRONG 行的锚点形态细分与「文件主体是否另有其人」诊断。只读产物 + 只读 lead/。"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mev675 as M

OUT = os.path.dirname(os.path.abspath(__file__))
LEAD = os.path.dirname(os.path.dirname(OUT))

rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(OUT, "buckets675.tsv"),
                                                 encoding="utf-8")][1:]
strong = [r for r in rows if r[3] == "CTX_STRONG"]
print(f"STRONG n={len(strong)}")

codes = collections.Counter()
for r in strong:
    codes[r[6].split("；")[0].split()[0]] += 1
print("why-code:", dict(codes))

# 每个 STRONG 行：其最强锚点文件 / 行 / 上下文，以及该文件自己的「主体 entry」
resolve = os.path.join(os.path.dirname(OUT), "R16_BASE", "evid", "resolve.tsv")
all_rows = M.load_rows(resolve)
entry_set = {x["entry"].lower() for x in all_rows}
hits = M.load_hits(os.path.join(OUT, "_hits_primary.tsv"), entry_set)

need = {}
for r in strong:
    e = r[0].lower()
    need[e] = r[5].split(";")[0].strip()

files = sorted({f for f in need.values() if f and f != "-"})
structs = {f: M.build_struct(LEAD, f, entry_set) for f in files}

print("\n=== STRONG 逐行：锚点文件、行号、该文件自己的主体 entry、上下文 ===")
for r in strong:
    e = r[0].lower()
    f = need[e]
    st = structs.get(f)
    hs = [h for h in hits.get(e, []) if h[0] == f]
    # 找最强形态那一行
    best = None
    for rel, ln, text in hs:
        form, why, code = M.classify(e, st, ln, text)
        if best is None or M.RANK[form] > M.RANK[best[0]]:
            best = (form, why, code, ln, text)
    if not best:
        print(f"{r[0]} <> !! no hit line in {f}")
        continue
    form, why, code, ln, text = best
    # 文件自己的主体：disasm_min / 第一个 # 头 / 第一个 meta entry= / 第一个 FUNCDEF
    own = None
    if st is not None and st.disasm_min is not None:
        own = "%08x" % st.disasm_min
    subs = sorted(M.subject_entries(st, entry_set))
    print(f"{r[0]} {code:3s} L{ln:<6d} file={f}")
    print(f"        own_subject={own} subjects_in_file={len(subs)} {subs[:5]}")
    print(f"        line: {text.strip()[:130]}")
