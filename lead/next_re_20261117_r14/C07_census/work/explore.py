#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C07 探索脚本：确认切片范围、atlas 辅助文件结构、sweep 统计、RTTI 直读虚表规模。可复跑。
本卡负责 function_atlas.tsv 逻辑行 7753..9044 => data[7752:9044]（1292 函数）。
"""
import os, sys, json, struct
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C07_census")
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
# 逻辑行 7753..9044 => data[7752:9044]
sl = allf[7752:9044]
print("slice n:", len(sl))
lo = min(f["entry"] for f in sl)
hi = max(f["entry"] + f["size"] for f in sl)
print("slice entry min:", hex(lo), "max(end):", hex(hi))
print("slice first 3:", [(hex(f['entry']), f['size']) for f in sl[:3]])
print("slice last 3:", [(hex(f['entry']), f['size']) for f in sl[-3:]])
print("context row 7752 (before):", hex(allf[7751]["entry"]))
print("context row 9045 (after):", hex(allf[9044]["entry"]) if len(allf) > 9044 else "EOF")

vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
print("vtables_v2 keys:", list(vtj.keys()), "n vtables:", len(vtj.get("vtables", [])))
if vtj.get("vtables"):
    print("sample vt:", vtj["vtables"][0])

# RTTI 直读：对照 vtables_v2.json slots 分布（验证 off-by-one 坑）
b = audit_lib.Bin()
text = b.text
tlo, thi = text["va"], text["va"] + text["vsize"]

def sec_of(va):
    for s in b.sections:
        if s["va"] <= va < s["va"] + s["rawsize"]:
            return s
    return None

def u32(va):
    try: return b.u32(va)
    except Exception: return None

# 精简 RTTI 扫描（.rdata only）统计真实槽数 vs JSON slots
rdata = b.sec(".rdata")
buf = b.pe.__data__[rdata["raw"]:rdata["raw"] + rdata["rawsize"]]
n = len(buf)//4
real_slots = {}
i = 1
while i < n:
    v = struct.unpack_from("<I", buf, i*4)[0]
    if tlo <= v < thi:
        col = struct.unpack_from("<I", buf, (i-1)*4)[0]
        if sec_of(col) is not None:
            sig, off, cd, tdp = u32(col), u32(col+4), u32(col+8), u32(col+12)
            cls = None
            if sig in (0,1) and tdp is not None:
                nm = None
                try: nm = b.read(tdp+8, 96)
                except Exception: pass
                if nm:
                    z = nm.find(b"\0")
                    if z > 3 and nm[:z].startswith((b".?AV", b".?AU")):
                        cls = nm[:z].decode("latin1")
            if cls:
                j = i; cnt = 0
                while j < n:
                    vv = struct.unpack_from("<I", buf, j*4)[0]
                    if not (tlo <= vv < thi): break
                    cnt += 1; j += 1
                vt_va = rdata["va"] + i*4
                real_slots[vt_va] = cnt
                i = j
                continue
    i += 1
print("RTTI direct-scan vtables:", len(real_slots))
theirs = {v["vt"]: v.get("slots",0) for v in vtj["vtables"]}
common = set(real_slots) & set(theirs)
diff = Counter(real_slots[k]-theirs[k] for k in common)
print("vtables common:", len(common), "slot-diff (real - json):", dict(sorted(diff.items())))

bin_ = audit_lib.Bin()
sweep = audit_lib.sweep_calls(bin_)
print("sweep stats:", sweep[2])

json.dump(dict(lo=hex(lo), hi=hex(hi), n=len(sl), stats=sweep[2],
               slice_first=hex(sl[0]["entry"]), slice_last_entry=hex(sl[-1]["entry"]),
               context_before=hex(allf[7751]["entry"]),
               rtti_vt_count=len(real_slots), slot_diff=dict(diff)),
          open(os.path.join(WORK, "explore.json"), "w"), indent=1)
