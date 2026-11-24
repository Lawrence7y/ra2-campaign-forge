#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof675.py — 675 行是否存在「真四环文档」（只读）。

口径（与 PROBE_802_ANCHOR §5.4 的 11 行同标准）：
  某 entry 有资格算「④ 已写在盘上」⇔ 盘上有一份以它为主体的文档，且该文档
  同时含 ①②③④ 四个环段标记（那 11 行的 `PROOF_<8hex>.txt` 就是这个形态）。

构造性事实：`PROOF_<8hex>.txt` 的文件名含 8 位 hex ⇒ 会被 A1 命中 ⇒ 不可能留在 675。
所以 675 若要出现四环文档，只可能来自：
  (a) **6/7 位短形式**命名的 PROOF 文件（本项目实测大量如此：`PROOF_4D7330.txt`）
  (b) 文件名与 entry 无关、但正文以 entry 为主体且分 ①②③④ 段的文件
本脚本对 (a)(b) 都查。
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

rows = M.load_rows(os.path.join(R14, "R16_BASE", "evid", "resolve.tsv"))
entry_set = {r["entry"].lower() for r in rows}
buckets = {}
for line in open(os.path.join(OUT, "buckets675.tsv"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] == "entry":
        continue
    buckets[f[0].lower()] = f

# ---- 全树所有 PROOF* 文件（含 .txt/.json/.py 等） ----
p = subprocess.run(["rg", "--files", "--hidden", "--no-ignore", "--no-ignore-vcs",
                    "--glob", "!.git/**", "--iglob", "*proof*", "."],
                   cwd=LEAD, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=600)
proof_files = sorted({l.strip().lstrip(".\\/").replace("\\", "/")
                      for l in p.stdout.splitlines() if l.strip()})
print(f"[in] lead 全树名字含 'roof' 的文件 {len(proof_files)} 个")

# ---- 每个 PROOF 文件：读正文，找 ①②③④ 与出现的 791 entry ----
info = {}
for f in proof_files:
    full = os.path.join(LEAD, f.replace("/", os.sep))
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(4 * 1024 * 1024)
    except OSError:
        continue
    low = txt.lower()
    rings = "".join(c for c in RING if c in txt)
    toks = set(M.HEX_TOKEN.findall(low))
    shorts = set(M.SHORT_TOKEN.findall(low))
    ent = (toks & entry_set)
    for s in shorts:
        e8 = M.short_map_of(entry_set).get(s)
        if e8:
            ent.add(e8)
    info[f] = dict(rings=rings, entries=sorted(ent), size=len(txt))

four = {f: v for f, v in info.items() if all(c in v["rings"] for c in RING)}
print(f"[ring] 四环齐全的 PROOF 文件 {len(four)} 个")
for f, v in list(four.items())[:15]:
    print(f"        {v['rings']} entries={len(v['entries'])} {f}")

# ---- 文件名带该 entry（6/7/8 位）的 PROOF 文件 ----
def name_has(f, e):
    b = os.path.basename(f).lower()
    return (e in b) or (e.lstrip("0") in b and len(e.lstrip("0")) >= 6)


name_hit = collections.defaultdict(list)
for e in buckets:
    for f in proof_files:
        if name_has(f, e):
            name_hit[e].append(f)

print(f"\n[find] 675 行中「有同名 PROOF 文件」= {len(name_hit)} 行")
cnt = collections.Counter()
detail = []
for e, fs in sorted(name_hit.items()):
    best = None
    for f in fs:
        v = info.get(f)
        if v is None:
            continue
        has4 = all(c in v["rings"] for c in RING)
        subject = e in v["entries"]
        if best is None or (has4, subject) > (best[0], best[1]):
            best = (has4, subject, f, v["rings"], v["size"])
    if best is None:
        continue
    has4, subject, f, rings, size = best
    kind = ("FOUR_RING" if has4 else
            "proof_no_rings" if rings else "proof_no_ring_marks")
    cnt[kind] += 1
    detail.append(dict(entry=e, kind=kind, file=f, rings=rings, size=size,
                       subject_mentioned=subject, n_files=len(fs)))
print(f"[find] 按最强 PROOF 文件分级: {dict(cnt)}")
for d in detail:
    print(f"        {d['entry']} {d['kind']:18s} rings={d['rings'] or '-':6s} "
          f"{d['size']:>8d}B  {d['file']}")

# ---- 本体检查：那 11 行的 PROOF 文件里 ①②③④ 是怎么出现的（作为对照） ----
print("\n[ctl] 对照：已修复 11 行之一 0045A560 的 PROOF 文件（确认四环写法）")
ctl = [f for f in proof_files if "proof_0045a560" in os.path.basename(f).lower()]
for f in ctl:
    v = info.get(f, {})
    print(f"        {f}  rings={v.get('rings')}  size={v.get('size')}")
    full = os.path.join(LEAD, f.replace("/", os.sep))
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        head = fh.read(1200)
    print("        --- 前 12 行 ---")
    for l in head.splitlines()[:12]:
        print("        " + l[:120])

json.dump(dict(n_proof_files=len(proof_files), four_ring_files=list(four),
               name_hit_rows=len(name_hit), detail=detail,
               info={k: dict(rings=v["rings"], n_entries=len(v["entries"]),
                             size=v["size"]) for k, v in info.items()}),
          open(os.path.join(OUT, "_proof675.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[out] {os.path.join(OUT, '_proof675.json')}")
