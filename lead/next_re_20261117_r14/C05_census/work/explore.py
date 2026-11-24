#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C05 探索脚本：确认切片范围、atlas 辅助文件结构、sweep 统计。可复跑。"""
import os, sys, json, bisect
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C05_census")
WORK  = os.path.join(CARD, "work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

fa = os.path.join(ATLAS, "function_atlas.tsv")
with open(fa, encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()
hdr = lines[0].split("\t")
data = [ln for ln in lines[1:] if ln.strip()]
print("total data rows:", len(data), "header:", hdr)
assert len(data) == 12916

def parse(ln):
    p = ln.split("\t"); rec = dict(zip(hdr, p))
    return dict(entry=int(rec["entry"], 16), size=int(rec["size"]), n_instr=int(rec["n_instr"]))

allf = [parse(ln) for ln in data]
# 逻辑行 5169..6460 => data[5168:6460]
sl = allf[5168:6460]
print("slice n:", len(sl))
lo = min(f["entry"] for f in sl)
hi = max(f["entry"] + f["size"] for f in sl)
print("slice entry min:", hex(lo), "max(end):", hex(hi))
print("slice first 3:", [(hex(f['entry']), f['size']) for f in sl[:3]])
print("slice last 3:", [(hex(f['entry']), f['size']) for f in sl[-3:]])

# neighbor rows (context)
print("context row 5168 (before):", hex(allf[5167]["entry"]))
print("context row 6461 (after):", hex(allf[6460]["entry"]))

# vtables_v2
vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
print("vtables_v2 keys:", list(vtj.keys()), "n vtables:", len(vtj.get("vtables", [])))
if vtj.get("vtables"):
    print("sample vt:", vtj["vtables"][0])

# module_attribution / source_files counts
for fn in ("module_attribution.tsv", "source_files.tsv"):
    p = os.path.join(ATLAS, fn)
    with open(p, encoding="utf-8", errors="replace") as f:
        hs = f.readline().rstrip("\n").split("\t")
        rows = [f.readline() for _ in range(2)]
    print(fn, "header:", hs, "samples:", [r.strip() for r in rows])

# sweep stats
b = audit_lib.Bin()
print("ImageBase:", hex(b.image_base), "text:", b.text)
calls, jmps, stats = audit_lib.sweep_calls(b)
print("sweep stats:", stats)
print("n call targets:", len(calls), "n jmp targets:", len(jmps))

json.dump(dict(lo=hex(lo), hi=hex(hi), n=len(sl), stats=stats,
               slice_first=hex(sl[0]["entry"]), slice_last_entry=hex(sl[-1]["entry"])),
          open(os.path.join(WORK, "explore.json"), "w"), indent=1)
