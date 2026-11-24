#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C09 独立 RTTI 通道：从 gamemd.exe 的 .rdata/.data 手工恢复 vtable + 真实槽数。

设计（与 vtables_v2.json 的 slots 完全独立，不读它的 slots）：
  1) TypeDescriptor：.rdata/.data 中 `.?AV`/`.?AU` 字面量，TD va = namepos-8
  2) COL (RTTI CompleteObjectLocator)：某 4 字节对齐位置 off 满足 [off+12]==TD va
     且 [off+16] (pCD) 落在 image 范围
  3) vtable：某 dword 值 == COL 地址，则该 dword 位置+4 = vtable 起点
  4) 真实槽数 = 从 slot0 起连续的 .text 代码指针个数（下一个 COL 指针/非 .text 值即止）
     —— 这就是「按下一张表的 COL 指针 / vftable 特征直接定界」，避免 v2.json 少计末槽 bug。

自写 struct PE 解析（不 import pefile），与 verify_core 通道（pefile）不同源。
输出 work/rtti_independent.json：{total_slots, delta, vtables:[{vt,col,cls,slots,slots_list}]}
"""
import os, struct, re, json
from collections import Counter

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
WORK = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C09_census\\work")

RAW = open(EXE, "rb").read()
PEOFF = struct.unpack_from("<I", RAW, 0x3C)[0]
assert RAW[PEOFF:PEOFF + 4] == b"PE\0\0"
COFF = PEOFF + 4
NSEC = struct.unpack_from("<H", RAW, COFF + 2)[0]
SIZEOPT = struct.unpack_from("<H", RAW, COFF + 16)[0]
OPT = COFF + 20
IB = struct.unpack_from("<I", RAW, OPT + 28)[0]
SECS = []
ST = OPT + SIZEOPT
for i in range(NSEC):
    o = ST + i * 40
    name = RAW[o:o + 8].rstrip(b"\x00").decode("latin1")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", RAW, o + 8)
    SECS.append(dict(name=name, va=IB + va, vsize=vsize, rawsize=rawsize, raw=rawptr))
BY = {s["name"]: s for s in SECS}
TEXT_LO = BY[".text"]["va"]
TEXT_HI = BY[".text"]["va"] + BY[".text"]["rawsize"]


def u32(va):
    for s in SECS:
        if s["va"] <= va and va + 4 <= s["va"] + max(s["rawsize"], s["vsize"]):
            off = s["raw"] + (va - s["va"])
            if off + 4 > len(RAW):
                raise ValueError("EOF")
            return struct.unpack_from("<I", RAW, off)[0]
    raise ValueError("va %08X no bytes" % va)


def demangle(s):
    if s.startswith(".?AV") or s.startswith(".?AU"):
        s = s[4:]
    if s.endswith("@@"):
        s = s[:-2]
    return s.replace("?$", "T_").replace("@", "_")


def build():
    # 1) TypeDescriptors
    tds = {}
    pat = re.compile(rb"\.\?A[VU]")
    for sn in (".rdata", ".data"):
        s = BY[sn]; buf = RAW[s["raw"]:s["raw"] + s["rawsize"]]
        for m in pat.finditer(buf):
            i = m.start()
            if i < 8:
                continue
            z = buf.find(b"\x00", i)
            if z < 0:
                continue
            tds[s["va"] + i - 8] = buf[i:z].decode("latin1", "replace")
    tdset = set(tds)
    # 2) COL: [off+12]==TD, [off+16] in image range
    cols = {}
    for sn in (".rdata", ".data"):
        s = BY[sn]; buf = RAW[s["raw"]:s["raw"] + s["rawsize"]]
        for off in range(0, len(buf) - 20, 4):
            ptd = struct.unpack_from("<I", buf, off + 12)[0]
            if ptd in tdset:
                pcd = struct.unpack_from("<I", buf, off + 16)[0]
                if 0x400000 <= pcd < 0x900000:
                    cols[s["va"] + off] = tds[ptd]
    # 3) vtable dword -> COL
    vts = []
    for sn in (".rdata", ".data"):
        s = BY[sn]; buf = RAW[s["raw"]:s["raw"] + s["rawsize"]]
        for off in range(0, len(buf) - 4, 4):
            v = struct.unpack_from("<I", buf, off)[0]
            if v in cols:
                vts.append(dict(vt=s["va"] + off + 4, col=v, cls=demangle(cols[v])))
    # 4) 真实槽数：连续 .text 代码指针（零不计数；遇到下一个 COL 指针即止）
    for v in vts:
        n = 0
        while n < 512:
            try:
                p = u32(v["vt"] + 4 * n)
            except ValueError:
                break
            if TEXT_LO <= p < TEXT_HI:
                n += 1
            else:
                break
        v["slots"] = n
        v["slots_list"] = []
        for i in range(n):
            v["slots_list"].append(u32(v["vt"] + 4 * i))
    return vts, cols


if __name__ == "__main__":
    vts, cols = build()
    byvt = {}
    for v in vts:
        byvt.setdefault(v["vt"], v)
    total = sum(v["slots"] for v in byvt.values())
    print("COL=%d  vtable-pos=%d  unique-vt=%d  total-slots=%d" %
          (len(cols), len(vts), len(byvt), total))
    v2 = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))["vtables"]
    their = {v["vt"]: v for v in v2}
    inter = set(byvt) & set(their)
    delta = Counter(byvt[vt]["slots"] - their[vt].get("slots", 0) for vt in inter)
    print("v2 total slots =", sum(v.get("slots", 0) for v in v2))
    print("delta distribution (mine - v2):", dict(sorted(delta.items())))
    print("net delta =", sum(k * c for k, c in delta.items()))
    json.dump(dict(total_slots=total, n_col=len(cols), n_vt=len(byvt),
                   v2_total=sum(v.get("slots", 0) for v in v2),
                   delta={str(k): c for k, c in sorted(delta.items())},
                   vtables=[dict(vt=hex(v["vt"]), col=hex(v["col"]), cls=v["cls"],
                                 slots=v["slots"],
                                 slots_list=[hex(x) for x in v["slots_list"]])
                            for v in byvt.values()]),
              open(os.path.join(WORK, "rtti_independent.json"), "w"), indent=1)
    print("wrote rtti_independent.json")
