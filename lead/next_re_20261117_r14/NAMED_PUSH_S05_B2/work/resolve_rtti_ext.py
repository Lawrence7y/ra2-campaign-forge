# -*- coding: utf-8 -*-
"""扩展 RTTI 解析：把 resolve_slot 的回扫窗口从 40 dword 扩到 400，覆盖 vslot 高达 330。
另给出基于已知 vtable base 的 slot 校验（vtable 地址 + 槽号 + 槽指向本 entry）。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from witness_core import _SECS, u32, read_cstr, parse_col, parse_td, find_dword_refs

def resolve_slot_ext(refva, kmax=400):
    for k in range(0, kmax+1):
        vb = refva - 4*k
        c = u32(vb-4)
        if not c:
            continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return {"vtable_base": vb, "slot_off": 4*k, "col": ci["col"],
                    "td": tdi["td"], "name_va": tdi["name_va"], "rtti_name": tdi["name"]}
    return None

def vt_info(vt):
    c = u32(vt-4)
    ci = parse_col(c) if c else None
    if not ci or ci["sig"] != 0:
        return None
    td = parse_td(ci["td"])
    return {"col": ci["col"], "td": ci["td"], "name": td["name"] if td else None}

ENTRIES = [r["entry"] for r in __import__("json").load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"b1_rows.json"),encoding="utf-8"))]

KNOWN_VT = {"AircraftClass":0x7E22A4, "AircraftTypeClass":0x7E2868, "AbstractTypeClass":0x7E2000}

for e in ENTRIES:
    ea = int(e,16)
    refs = find_dword_refs(ea)
    print("="*90)
    print("%s  dword refs in non-text: %s" % (e, ["%08X@%s"%(v,s) for v,s in refs]))
    for refva, sec in refs:
        ext = resolve_slot_ext(refva)
        if ext:
            print("  EXT ref=%08X: vt=%08X off=%d(slot%d) col=%08X td=%08X name=%s" % (
                refva, ext["vtable_base"], ext["slot_off"], ext["slot_off"]//4,
                ext["col"], ext["td"], ext["rtti_name"]))
        else:
            print("  EXT ref=%08X: no COL found in kmax=400" % refva)
        # 用已知 vtable base 直接算槽号
        for cls,vt in KNOWN_VT.items():
            if vt <= refva and (refva-vt)%4==0:
                off=refva-vt
                slot=u32(refva)
                print("    vs %-18s vt=%08X: off=%d slot#=%d dword@slot=%s (entry=%s)" % (
                    cls, vt, off, off//4, R.hx(slot) if slot else None, e))
                vi=vt_info(vt)
                if vi: print("      vt-4 RTTI: col=%08X td=%08X name=%s"%(vi["col"],vi["td"],vi["name"]))
