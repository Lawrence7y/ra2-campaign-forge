# -*- coding: utf-8 -*-
"""Comprehensive main-vtable identification for all 13 B4 rows.
For each object ctor, list ALL imm-in-vt-range writes and their slot0; identify
the write to the principal `this` register; check whether ANY vtable written has
slot0 == 0x00410260. Read-only on target.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
GD = {x["entry"]: x for x in json.load(open(os.path.join(HERE,"gather.json"),encoding="utf-8"))}
ROWS = json.load(open(os.path.join(HERE,"b4_rows.json"),encoding="utf-8"))["rows"]

def hx(x): return R.hx(x)

def qreturns_hresult(qva):
    if not qva or not R.in_text(qva): return False
    prof = R.callee_return_profile(qva)
    return bool(prof and set(prof["consts"]) >= {0x80004002,0x80004003} and prof["n_rets"]>=2)

for row in ROWS:
    e = row["entry"]
    gd = GD[e]
    objctor = int(gd["obj_ctor_calls"][0]["dest"],16) if gd["obj_ctor_calls"] else None
    print("\n#### %s %s ####" % (e, gd["name"]))
    print("  factory body QI site=%s ; objctor=%s" % (gd["qi"]["addr"], hx(objctor)))
    has410260 = False
    if objctor:
        sz = R.ATLAS.get(hx(objctor),{}).get("size") or 1024
        for ins in R.disasm_body(objctor, sz):
            if ins.id == X86_INS_MOV and len(ins.operands)==2:
                a,b = ins.operands
                if a.type==X86_OP_MEM and b.type==X86_OP_IMM:
                    v = b.imm & 0xFFFFFFFF
                    if 0x7E0000 <= v <= 0x7FC000:
                        q = R.u32(v)
                        hr = qreturns_hresult(q)
                        if q == 0x00410260: has410260 = True
                        try: bn = ins.reg_name(a.mem.base)
                        except Exception: bn = "?"
                        print("    %s [%-3s%+04x]=%s  slot0=%s hr3=%s  %s" % (
                            hx(ins.address), bn, a.mem.disp, hx(v), hx(q) if q else "-", hr,
                            ins.bytes.hex(" ")))
    print("  >> has vtable with slot0==00410260 in objctor: %s" % has410260)
