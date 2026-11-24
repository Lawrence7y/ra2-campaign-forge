#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C08 独立 RTTI 通道验证：从 .rdata 的 COL->TypeDescriptor 恢复 vtable + 真实槽数。
刻意自写（struct 手动解 PE），不读 vtables_v2.json 的 slots，不 import a0_lib。
核对：全镜像 slot 总数应为 14044，与 v2.json 13351 差 +693；
      delta 分布应 ≈ {1:794,0:327,-1:85,-2:8}。
"""
import os, sys, json, struct, re, bisect
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
EXE = os.path.join(ROOT, "ra2youli\\gamemd.exe")
WORK = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C08_census\\work")

raw = open(EXE, "rb").read()
peoff = struct.unpack_from("<I", raw, 0x3C)[0]
assert raw[peoff:peoff+4] == b"PE\0\0"
coff = peoff + 4
nsec = struct.unpack_from("<H", raw, coff+2)[0]
sizeopt = struct.unpack_from("<H", raw, coff+16)[0]
opt = coff + 20
IB = struct.unpack_from("<I", raw, opt+28)[0]
secs = []
st = opt + sizeopt
for i in range(nsec):
    o = st + i*40
    name = raw[o:o+8].rstrip(b"\x00").decode("latin1")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", raw, o+8)
    secs.append(dict(name=name, va=IB+va, vsize=vsize, rawsize=rawsize, raw=rawptr))
byname = {s["name"]: s for s in secs}
TEXT_LO = byname[".text"]["va"]
TEXT_HI = byname[".text"]["va"] + byname[".text"]["rawsize"]

def u32(va):
    for s in secs:
        if s["va"] <= va and va+4 <= s["va"] + max(s["rawsize"], s["vsize"]):
            off = s["raw"] + (va - s["va"])
            if off+4 > len(raw): raise ValueError("EOF")
            return struct.unpack_from("<I", raw, off)[0]
    raise ValueError("va %08X no bytes" % va)

def sec_of(va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["rawsize"], s["vsize"]):
            return s["name"]
    return None

def demangle(s):
    if s.startswith(".?AV") or s.startswith(".?AU"): s = s[4:]
    if s.endswith("@@"): s = s[:-2]
    return s.replace("?$", "T_").replace("@", "_")

def build():
    # 1) TypeDescriptor: `.?AV`/`.?AU` literal in .rdata/.data -> TD va = namepos-8
    tds = {}
    pat = re.compile(rb"\.\?A[VU]")
    for sn in (".rdata", ".data"):
        s = byname[sn]; buf = raw[s["raw"]:s["raw"]+s["rawsize"]]
        for m in pat.finditer(buf):
            i = m.start()
            if i < 8: continue
            z = buf.find(b"\x00", i)
            if z < 0: continue
            tds[s["va"]+i-8] = buf[i:z].decode("latin1", "replace")
    tdset = set(tds)
    # 2) COL: dword at off where off+12 == TD va, off+16 (pCD) looks 0x400000..0x900000
    cols = {}
    for sn in (".rdata", ".data"):
        s = byname[sn]; buf = raw[s["raw"]:s["raw"]+s["rawsize"]]
        for off in range(0, len(buf)-20, 4):
            ptd = struct.unpack_from("<I", buf, off+12)[0]
            if ptd in tdset:
                pcd = struct.unpack_from("<I", buf, off+16)[0]
                if 0x400000 <= pcd < 0x900000:
                    cols[s["va"]+off] = tds[ptd]
    # 3) vtable: dword whose value is COL addr; vt=pos+4
    vts = []
    for sn in (".rdata", ".data"):
        s = byname[sn]; buf = raw[s["raw"]:s["raw"]+s["rawsize"]]
        for off in range(0, len(buf)-4, 4):
            v = struct.unpack_from("<I", buf, off)[0]
            if v in cols:
                vts.append(dict(vt=s["va"]+off+4, col=v, cls=demangle(cols[v])))
    # 4) real slot count = consecutive .text code pointers from slot0 (zeros NOT counted)
    for v in vts:
        n = 0
        while n < 512:
            try: p = u32(v["vt"] + 4*n)
            except ValueError: break
            if TEXT_LO <= p < TEXT_HI: n += 1
            else: break
        v["slots"] = n
        v["slots_list"] = []
        for i in range(n):
            v["slots_list"].append(u32(v["vt"] + 4*i))
    return vts, cols

if __name__ == "__main__":
    vts, cols = build()
    byvt = {}
    for v in vts: byvt.setdefault(v["vt"], v)
    print("COL=%d  vtable pos=%d  unique vt=%d" % (len(cols), len(vts), len(byvt)))
    total = sum(v["slots"] for v in byvt.values())
    print("independent total slots (unique vt) =", total)
    theirs = json.load(open(os.path.join(ATLAS,"vtables_v2.json"),encoding="utf-8"))["vtables"]
    their_by_vt = {v["vt"]: v for v in theirs}
    print("v2 total slots =", sum(v.get("slots",0) for v in theirs))
    inter = set(byvt) & set(their_by_vt)
    delta = Counter(byvt[vt]["slots"] - their_by_vt[vt].get("slots",0) for vt in inter)
    print("delta (mine - v2) distribution:", dict(sorted(delta.items())))
    print("net delta:", sum(k*c for k,c in delta.items()))
    # save
    json.dump(dict(total_slots=total, n_col=len(cols), n_vt=len(byvt),
                   delta={str(k):v for k,v in sorted(delta.items())},
                   vtables=[dict(vt=hex(v["vt"]),col=hex(v["col"]),cls=v["cls"],
                                 slots=v["slots"], slots_list=[hex(x) for x in v["slots_list"]])
                            for v in byvt.values()]),
              open(os.path.join(WORK,"rtti_independent.json"),"w"), indent=1)
    print("wrote rtti_independent.json")
