# -*- coding: utf-8 -*-
"""calib.py — 校准统计：导入直方图 / 虚表类名 / 地址簇 gap 分布 / 字符串样例"""
import json, re
from collections import Counter, defaultdict
import pefile

BASE = 0x400000
ATLAS_DIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas"

# ---- 载入 ----
funcs = []
with open(ATLAS_DIR + r"\function_atlas.tsv", encoding="utf-8") as f:
    f.readline()
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 8: continue
        funcs.append({"entry": int(c[0], 16), "size": int(c[1]), "n_instr": int(c[2]),
                      "n_callers": int(c[3]), "n_callees": int(c[4]),
                      "is_fnptr": int(c[5]), "strings": c[8] if len(c) > 8 else ""})
funcs.sort(key=lambda d: d["entry"])
ev = {int(k, 0) if isinstance(k, str) and k.startswith("0x") else int(k): v
      for k, v in json.load(open(ATLAS_DIR + r"\glm_seg\evidence.json")).items()}
# evidence.json key 是十进制字符串
ev = {int(k): v for k, v in json.load(open(ATLAS_DIR + r"\glm_seg\evidence.json")).items()}

# 1) 导入直方图
dllc, apic = Counter(), Counter()
for d in ev.values():
    dlls = set()
    for imp in d.get("imports", []):
        dll, api = imp.split("!")
        dlls.add(dll); apic[api] += 1
    for dl in dlls: dllc[dl] += 1
print("=== DLL 函数数 ===")
for k, v in dllc.most_common(): print(" %-12s %5d" % (k, v))
print("=== top API ===")
for k, v in apic.most_common(60): print(" %-40s %5d" % (k, v))

# 2) 虚表类名直方图
cls_hist = Counter()
for d in ev.values():
    for c in d.get("vclasses", []):
        cls_hist[re.sub(r"^\.?\?[ACV]", "", c)] += 1
print("=== top vtable classes (函数归属数) ===")
for k, v in cls_hist.most_common(120): print(" %-55s %4d" % (k, v))

# 3) 地址 gap 分布
print("=== gap 分布 ===")
gaps = [(b["entry"] - (a["entry"] + a["size"]), a["entry"], b["entry"])
        for a, b in zip(funcs, funcs[1:])]
import statistics
gg = sorted(g[0] for g in gaps)
print(" n=%d median=%d p90=%d p99=%d max=%d" % (len(gg), gg[len(gg)//2],
      gg[int(len(gg)*.9)], gg[int(len(gg)*.99)], gg[-1]))
big = [g for g in gaps if g[0] >= 512]
print(" gaps >=512B: %d" % len(big))
for g in big[:40]:
    print("   gap=%6d  after %08X  before %08X" % (g[0], g[1], g[2]))

# 4) 大簇概览 (gap>=1024 切簇)
print("=== 簇 (gap>=1024) ===")
clusters = []
cur = [funcs[0]]
for a, b in zip(funcs, funcs[1:]):
    if b["entry"] - (a["entry"] + a["size"]) >= 1024:
        clusters.append(cur); cur = []
    cur.append(b)
clusters.append(cur)
for cl in clusters:
    lo, hi = cl[0]["entry"], cl[-1]["entry"] + cl[-1]["size"]
    nb = sum(f["size"] for f in cl)
    mods = set()
    for f in cl[:]:
        m = ev.get(f["entry"], {}).get("module")
        if m: mods.add(m)
    strs = Counter()
    for f in cl:
        for s in re.split(r" \| ", f["strings"]):
            if s: strs[s] += 1
    top = "; ".join(s for s, _ in strs.most_common(6))
    print(" %08X-%08X n=%4d bytes=%7d mods=%s str=%s" %
          (lo, hi, len(cl), nb, ",".join(sorted(mods))[:70], top[:100]))
