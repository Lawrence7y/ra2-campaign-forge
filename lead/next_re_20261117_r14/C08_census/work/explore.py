#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C08 探索脚本：确认切片范围、vtable 真实槽数（独立定界）、term 分布。可复跑。
本卡负责 function_atlas.tsv 逻辑行 9045..10336 => data[9044:10336]（1292 函数）。
"""
import os, sys, json, struct
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C08_census")
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
sl = allf[9044:10336]
print("slice n:", len(sl))
lo = min(f["entry"] for f in sl)
hi = max(f["entry"] + f["size"] for f in sl)
print("slice entry min:", hex(lo), "max(end):", hex(hi))
print("slice first 3:", [(hex(f['entry']), f['size']) for f in sl[:3]])
print("slice last 3:", [(hex(f['entry']), f['size']) for f in sl[-3:]])
print("context row 9044 (before):", hex(allf[9043]["entry"]))
print("context row 10337 (after):", hex(allf[10336]["entry"]))

# ---- vtable term 分布 + 独立槽数复算 ----
vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
vts = vtj["vtables"]
print("n vtables:", len(vts))
term_c = Counter(v.get("term","?") for v in vts)
print("term distribution:", dict(term_c))
json_slots = sum(v.get("slots",0) for v in vts)
print("JSON total slots:", json_slots)

b = audit_lib.Bin()
text = b.text
TEXT_LO, TEXT_HI = text["va"], text["va"]+text["rawsize"]
rdata = b.sec(".rdata")
RD_LO, RD_HI = rdata["va"], rdata["va"]+rdata["rawsize"]

def is_code(v): return TEXT_LO <= v < TEXT_HI
def u32safe(va):
    try: return b.u32(va)
    except Exception: return None

# 独立定界：从 vt 起数连续 code-or-zero dword，遇第一个非 code 非零 dword 停 => 槽数=当前 k
def nslots(vt, cap=400):
    k = 0
    while k < cap:
        v = u32safe(vt + 4*k)
        if v is None: break
        if is_code(v) or v == 0:
            k += 1
        else:
            break
    return k

diffs = []
tot_ind = 0
for v in vts:
    vt = v["vt"]
    ind = nslots(vt)
    js = v.get("slots",0)
    tot_ind += ind
    if ind != js:
        diffs.append((vt, v.get("class","?"), js, ind, v.get("term","?")))
print("independent total slots:", tot_ind, " delta vs JSON:", tot_ind-json_slots)
print("n diffs:", len(diffs))
print("diff by term:", dict(Counter(d[4] for d in diffs)))
print("diff by (js,ind):", dict(Counter((d[2],d[3]) for d in diffs).most_common(8)))
print("sample diffs:")
for d in diffs[:6]:
    print("  vt=%08X cls=%s json=%d ind=%d term=%s" % d)

# 本片函数命中虚表槽（用独立槽数）
vtmap = {}
for v in vts:
    vt = v["vt"]; cls = v.get("class","?")
    n = nslots(vt)
    for i in range(n):
        t = u32safe(vt+4*i)
        if t is not None and is_code(t):
            vtmap.setdefault(t, []).append((cls, i, vt))
slice_entries = set(f["entry"] for f in sl)
hit = sum(1 for e in slice_entries if e in vtmap)
print("slice funcs with vtable hit (independent slots):", hit, "/", len(sl))

json.dump(dict(lo=hex(lo),hi=hex(hi),n=len(sl),
               json_slots=json_slots, independent_slots=tot_ind,
               n_vtables=len(vts), term_dist=dict(term_c),
               n_diffs=len(diffs), n_slice_vt_hit=hit),
          open(os.path.join(WORK, "explore.json"), "w"), indent=1)
