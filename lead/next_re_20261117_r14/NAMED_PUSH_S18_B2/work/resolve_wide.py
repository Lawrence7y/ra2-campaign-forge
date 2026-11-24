# -*- coding: utf-8 -*-
"""扩大 resolve_slot 回扫上限(k=0..128)重新核 4 行的 ②，并核对 slot 号与 RTTI 名。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import witness_core as W
import recore as R
def hx(x): return "%08X" % (x & 0xFFFFFFFF)

def resolve_wide(refva, kmax=128):
    for k in range(0, kmax+1):
        vb = refva - 4*k
        c = W.u32(vb-4)
        if not c: continue
        ci = W.parse_col(c)
        if not ci or ci["sig"] != 0: continue
        tdi = W.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return dict(vtable_base=vb, slot_off=4*k, slot=k, col=c, td=ci["td"], name=tdi["name"])
    return None

CLUE = {
 "005C44E0": ("MPCooperative", 41),
 "005C46E0": ("MPCooperative", 43),
 "005C4CA0": ("MPCooperative", 44),
 "005CAAC0": ("MultiplayerSiege", 50),
}
for e,(cls,slot) in CLUE.items():
    ea=int(e,16)
    refs=W.find_dword_refs(ea)
    print("=== %s clue=%s::slot%d refs=%s ===" % (e, cls, slot, [hx(v) for v,s in refs]))
    for v,s in refs:
        rw=resolve_wide(v)
        if rw:
            ok = (rw["slot"]==slot) and (cls in rw["name"])
            print("   ref@%s vt=%s slot_off=+%d slot=%d COL=%s TD=%s name=%s  MATCH=%s" % (
                hx(v), hx(rw["vtable_base"]), rw["slot_off"], rw["slot"],
                hx(rw["col"]), hx(rw["td"]), rw["name"], ok))
            w=R.u32(rw["vtable_base"])
            print("   writes(install):", [hx(x) for x in W.find_vtable_writes(rw["vtable_base"])["regdisp"]][:8])
        else:
            print("   ref@%s NO RTTI within k<=128" % hx(v))
