# -*- coding: utf-8 -*-
"""③ 陷阱排查：枚举目标类的全部 vtable（经 RTTI COL 反查），区分主表/小成员表。"""
import json, os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

CLASSES = ["DriveLocomotionClass", "DropPodLocomotionClass", "FlyLocomotionClass",
           "HoverLocomotionClass", "JumpjetLocomotionClass", "RocketLocomotionClass",
           "ShipLocomotionClass", "TeleportLocomotionClass", "TunnelLocomotionClass",
           "WalkLocomotionClass"]

def col_refs(col_va):
    """找出 .rdata/.data 中 dword == col_va 的位置（vtable 的 -4 槽）。"""
    return [x for x in dword_refs(col_va) if not in_text(x)]

# 1) 找所有 COL（.rdata 里 sig==0 且 TD 名在目标集合）
cols = {}
for s in SECS:
    if s["name"] not in (".rdata", ".data"):
        continue
    d = s["data"]
    for off in range(0, len(d) - 0x14, 4):
        sig = struct.unpack_from("<I", d, off)[0]
        if sig != 0:
            continue
        va = s["va"] + off
        td = u32(va + 0xC)
        if not td or not (0x400000 <= td < 0x10000000):
            continue
        nm = cstr(td + 8, 64)
        if nm.startswith(".?AV") and nm.endswith("@@") and "@@@" not in nm:
            cn = nm[4:-2]
            if cn in CLASSES:
                cols.setdefault(cn, []).append(va)

print("=== COLs per class ===")
for c in CLASSES:
    print(c, [hx(x) for x in cols.get(c, [])])

print("\n=== vtables per class (via COL refs) ===")
res = {}
for c, cl in cols.items():
    res[c] = []
    for col in cl:
        for ref in col_refs(col):
            vb = ref + 4
            lay = []
            for k in range(48):
                v = u32(vb + 4 * k)
                if v is None or not in_text(v):
                    break
                lay.append(v)
            inst = [(hx(i.address), i.op_str) for i in install_sites(vb) if is_vptr_store(i, vb)]
            ent = {"vtable": hx(vb), "col": hx(col), "nslots": len(lay),
                   "slot0": hx(lay[0]) if lay else None,
                   "slot1": hx(lay[1]) if len(lay) > 1 else None,
                   "slot2": hx(lay[2]) if len(lay) > 2 else None,
                   "installs": inst}
            res[c].append(ent)

for c in CLASSES:
    print("\n--", c)
    for e in res.get(c, []):
        print("   vt=%s col=%s nslots=%d slot0=%s slot1=%s slot2=%s" %
              (e["vtable"], e["col"], e["nslots"], e["slot0"], e["slot1"], e["slot2"]))
        for i in e["installs"]:
            print("        install", i[0], i[1])

json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vtables.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten vtables.json")

# 2) slot0 函数形态：是否 QI（GUID 比较 / E_NOINTERFACE）
print("\n=== slot0 body shapes ===")
for c in CLASSES:
    seen = set()
    for e in res.get(c, []):
        s0 = int(e["slot0"], 16)
        if s0 in seen:
            continue
        seen.add(s0)
        body = dis_range(s0, 96)
        print("\n--", c, "slot0", e["slot0"])
        for i in body[:22]:
            print("   %s  %-28s %s" % (hx(i.address), i.mnemonic + " " + i.op_str,
                                       i.bytes.hex()))
