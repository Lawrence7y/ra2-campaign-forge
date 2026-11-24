# -*- coding: utf-8 -*-
"""深核 007B10C0 IPXInterfaceClass::slot15 四环。"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

e = "007B10C0"; ea = int(e,16)
print("==== RTTI chain for %s ====" % e)
w = W.witness_entry(e)
for s in w["slots"]:
    print("slot_va=%s sec=%s vt=%s off=%s col=%s td=%s name=%s" % (
        s.get("slot_va"), s.get("section"), s.get("vtable_base"), s.get("slot_off"),
        s.get("col"), s.get("td"), s.get("rtti_name")))
    if s.get("col"):
        col = int(s["col"],16)
        print("  COL@%08X bytes=%s sig=%08X td=%08X chd=%08X" % (
            col, W.va_read(col,16).hex(), W.u32(col), W.u32(col+0xC), W.u32(col+0x10)))
    if s.get("td"):
        td=int(s["td"],16)
        print("  TD@%08X name=%r" % (td, W.read_cstr(td+8,80)))
    if s.get("vtable_base"):
        vb=int(s["vtable_base"],16)
        print("  vt@%08X [-4]=%08X slots0..20=%s" % (
            vb, W.u32(vb-4) or 0, [hex(W.u32(vb+4*i) or 0) for i in range(0,21)]))
    print("  global_writes:", s.get("global_writes"))

print()
print("==== dispatch sites (call [reg+0x3c]) ====")
data={r["entry"]:r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"analysis.json"),encoding="utf-8"))}
r=data[e]
for s in r["slots"]:
    if s.get("rtti_name"):
        ds=s.get("dispatch_sites",[])
        print("  slot %s off %s: %d dispatch sites, first 8: %s" % (s["slot_va"],s["slot_off"],len(ds),ds[:8]))
print("  direct_callers:", r["direct_callers"])
