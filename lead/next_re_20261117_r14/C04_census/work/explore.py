#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C04 快速勘察：切片范围、地址分布、vtable 类命中、字符串样例、模块样例。"""
import os, sys, json, re
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

rows, hdr = audit_lib.load_func_atlas()
# 按逻辑行（data 顺序）切，忠实"按行号切"
p = os.path.join(ATLAS, "function_atlas.tsv")
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
data = [l for l in lines[1:] if l.strip()]
hdr2 = lines[0].split("\t")
sl = data[3876:5168]  # 逻辑行 3877..5168
print("total data rows:", len(data), " slice:", len(sl))
recs = [dict(zip(hdr2, l.split("\t"))) for l in sl]
es = [int(r["entry"], 16) for r in recs]
print("range: %08X .. %08X" % (min(es), max(es)))
# 每 0x10000 段计数
ctr = Counter(e >> 16 for e in es)
print("== per 0x10000 ==")
for k in sorted(ctr):
    print("%05X0000  %d" % (k, ctr[k]))

# vtable 类命中（用 vtables_v2.json）
vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
def demangle(c):
    s = c
    if s.startswith(".?AV") or s.startswith(".?AU"): s = s[4:]
    if s.endswith("@@"): s = s[:-2]
    s = s.replace("?$", "T_").replace("@", "_")
    return s
b = audit_lib.Bin()
text = b.text
tlo, thi = text["va"], text["va"] + text["rawsize"]
vt_by_func = {}
for v in vtj["vtables"]:
    vt = v["vt"]; cls = demangle(v.get("class", "?")); n = v.get("slots", 0)
    if n <= 0 or n > 400: continue
    for i in range(n):
        try: tgt = b.u32(vt + 4*i)
        except Exception: continue
        if tlo <= tgt < thi:
            vt_by_func.setdefault(tgt, []).append((cls, i))
hits = [(e, vt_by_func[e]) for e in es if e in vt_by_func]
print("\n== vtable slot funcs:", len(hits), "==")
cc = Counter()
for e, vs in hits:
    for cls, i in vs: cc[cls] += 1
for cls, n in cc.most_common(40):
    print("  %-45s %d" % (cls, n))

# 字符串样例（含 .CPP）
print("\n== string samples (with .CPP) ==")
for r in recs:
    s = r.get("strings", "")
    if ".CPP" in s.upper() or ".cpp" in s:
        print("  %s  %s" % (r["entry"], s[:110]))

# first_import 分布
print("\n== first_import ==")
imp = Counter(r.get("first_import", "") for r in recs if r.get("first_import", ""))
for k, n in imp.most_common(30):
    print("  %-30s %d" % (k, n))

# module 分布
mods = Counter()
with open(os.path.join(ATLAS, "module_attribution.tsv"), encoding="utf-8", errors="replace") as f:
    next(f)
    for ln in f:
        q = ln.rstrip("\n").split("\t")
        if len(q) >= 4: mods[os.path.basename(q[3].replace("\\","/"))] += 1
print("\n== all module names in atlas ==")
for k, n in mods.most_common():
    print("  %-30s %d" % (k, n))
