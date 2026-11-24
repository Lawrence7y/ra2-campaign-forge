#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shortform.py — 量化「文件名索引只认 8 位 hex」这条漏洞（只读 lead/，只写本目录 _shortform.*）

问题：`R16_SCAN802` / `PROBE_802_ANCHOR` 的 A1 只把**8 位** hex 当文件名命中键。
      但本项目大量文件把地址写成**去前导零的 6/7 位**形式：
          P0_GATE_B/EVIDENCE/47c3d0_clean_full.txt
          S21-F1/EVIDENCE/46CE10_CreateFromINIList.txt
          S02B_GATE/EVIDENCE/fresh_47C4D0.txt
      这些是真正的「逐 entry 专属文件」，却因写法不同被 A1 判成零候选。

本脚本：
  1) 建短形式文件名索引（边界锚定的 6–7 位 hex，按 basename）
  2) 对 675 行零候选，统计有多少行其实有短形式专属文件
  3) 对这些文件做内容级分类：是否是逐 entry 的反汇编 dump / 是否是报告或表
  4) 查它们里有没有 ①②③④ 四环标记（决定「值不值得做」的关键）
  5) 顺带查 PROOF_* 短形式文件（四环文档的命名约定）
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

SHORT_TOK = re.compile(r"(?<![0-9a-f])[0-9a-f]{6,7}(?![0-9a-f])")
RING = ["①", "②", "③", "④"]

rows = M.load_rows(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"))
entry_set = {r["entry"].lower() for r in rows}
short2e = M.short_map_of(entry_set)
print(f"[in] R_TRACE_ONLY={len(rows)}  短形式映射 {len(short2e)} 条")

# ---- 1) 短形式文件名索引 ----
inv = collections.defaultdict(list)
nfiles = 0
for root, dirs, fnames in os.walk(LEAD):
    dirs[:] = [d for d in dirs if d.lower() != ".git"
               and os.path.normcase(os.path.abspath(os.path.join(root, d)))
               != os.path.normcase(os.path.abspath(OUT))]
    for fn in fnames:
        nfiles += 1
        rel = os.path.relpath(os.path.join(root, fn), LEAD).replace("\\", "/")
        for t in SHORT_TOK.findall(fn.lower()):
            if t in short2e:
                inv[t].append(rel)
print(f"[idx] 扫描 {nfiles} 个文件名；短形式命中键 {len(inv)} 个，涉及文件 "
      f"{len({f for v in inv.values() for f in v})} 个")

# ---- 2) 675 行里有多少有短形式专属文件 ----
repro = None
name_inv, _files = M.build_name_index(LEAD, [OUT])
zero = []
for r in rows:
    e = r["entry"].lower()
    if not name_inv.get(e):
        zero.append(r["entry"].lower())
print(f"[repro] 675 复现 = {len(zero)}")

hit_rows = []
for e in zero:
    s = e.lstrip("0")
    fs = sorted({f for t, v in inv.items() if t == s for f in v})
    if fs:
        hit_rows.append((e, fs))
print(f"[find] 675 行中「有短形式同名文件」= {len(hit_rows)} 行")

# ---- 3) 内容级分类这些文件 ----
cand_files = sorted({f for _e, fs in hit_rows for f in fs})
print(f"[find] 涉及 {len(cand_files)} 个文件；建结构…")
structs = {f: M.build_struct(LEAD, f, entry_set) for f in cand_files}

kinds = collections.Counter()
ring_files = collections.Counter()
proof_like = []
detail = []
for e, fs in hit_rows:
    best = None
    for f in fs:
        st = structs.get(f)
        own = "%08x" % st.disasm_min if st is not None and st.disasm_min is not None else None
        # 文件里 ①②③④ 标记（读全文，不只头部）
        rings = ""
        try:
            with open(os.path.join(LEAD, f.replace("/", os.sep)), "r",
                      encoding="utf-8", errors="replace") as fh:
                txt = fh.read(2 * 1024 * 1024)
            rings = "".join(c for c in RING if c in txt)
        except OSError:
            pass
        if rings:
            ring_files[f] = rings
        if re.search(r"proof", os.path.basename(f).lower()):
            proof_like.append(f)
        kind = ("own_dump" if own == e else
                "table" if (st is not None and st.has_header) else
                "prose_md" if os.path.splitext(f)[1].lower() in M.MD_EXT else
                "disasm_other" if own else "other")
        kinds[kind] += 1
        if best is None or (kind == "own_dump" and best[0] != "own_dump"):
            best = (kind, f, own, rings)
    detail.append(dict(entry=e, kind=best[0], file=best[1], own_subject=best[2],
                       rings=best[3], n_files=len(fs)))

print(f"[kind] 文件类别: {dict(kinds)}")
print(f"[ring] 含 ①②③④ 任一的文件 {len(ring_files)} 个: {dict(ring_files)}")
print(f"[ring] 含 PROOF 字样的文件 {len(proof_like)} 个: {proof_like[:10]}")

k = collections.Counter(d["kind"] for d in detail)
print(f"[row ] 675 中有短形式文件的 {len(detail)} 行按最佳文件类别: {dict(k)}")
four = [d for d in detail if "①" in d["rings"] and "④" in d["rings"]]
print(f"[row ] 其中最佳文件同时含 ① 与 ④ 的行 = {len(four)}: {[d['entry'] for d in four]}")

with open(os.path.join(OUT, "_shortform.json"), "w", encoding="utf-8") as fh:
    json.dump(dict(n_zero=len(zero), n_rows_with_short=len(hit_rows),
                   n_files=len(cand_files), kinds=dict(kinds),
                   ring_files=dict(ring_files), proof_like=proof_like,
                   row_kinds=dict(k), rows_ring_1_and_4=[d["entry"] for d in four],
                   detail=detail), fh, ensure_ascii=False, indent=1)
print(f"[out] {os.path.join(OUT, '_shortform.json')}")

# ---- 4) 对照：这 675 行的短形式文件名在 stage-A 的 A1 里为何没命中 ----
print("\n[样例] 前 12 行的短形式文件：")
for d in detail[:12]:
    print(f"  {d['entry']} {d['kind']:12s} {d['file']}  (own={d['own_subject']}, "
          f"rings={d['rings']})")
