# -*- coding: utf-8 -*-
"""COL.offset 判主表（MSVC RTTICompleteObjectLocator: +0 sig, +4 offset, +8 cdOffset,
   +0xC pTypeDescriptor, +0x10 pClassDescriptor）。offset==0 => 该 vftable 在主对象偏移 0。"""
import json, os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

def col_full(col_va):
    return {"col": hx(col_va), "sig": u32(col_va), "offset": u32(col_va + 4),
            "cdOffset": u32(col_va + 8), "td": hx(u32(col_va + 0xC)), "chd": hx(u32(col_va + 0x10)),
            "name": cstr(u32(col_va + 0xC) + 8, 96)}

print("=== 陷阱③ 三处「副表 slot0」地址形态 ===")
for a in (0x004105E0, 0x00410580, 0x00410590, 0x00410260):
    print("\n-- %s" % hx(a))
    for i in dis_range(a, 24):
        print("   %s  %-34s %s" % (hx(i.address), i.mnemonic + " " + i.op_str, i.bytes.hex()))

V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vtables.json"), encoding="utf-8"))
print("\n=== 每类各 vtable 的 COL.offset（0=主表）===")
out = {}
for c, lst in V.items():
    print("\n--", c)
    out[c] = []
    for e in lst:
        if not e.get("slot0"):
            continue
        cf = col_full(int(e["col"], 16))
        e2 = dict(e)
        e2["col_offset"] = cf["offset"]
        e2["col_name"] = cf["name"]
        out[c].append(e2)
        print("   vt=%s col=%s COL.offset=%#x name=%s nslots=%d slot0=%s" % (
            e["vtable"], e["col"], cf["offset"], cf["name"], e["nslots"], e["slot0"]))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vtables2.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
