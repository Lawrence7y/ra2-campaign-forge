# -*- coding: utf-8 -*-
"""Probe ambiguous rows to identify the true main vtable (slot0) and distinguish
from small member subobject tables. Special constraint: main vt slot0 must be 0x410260.
Read-only on target.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

def hx(x): return R.hx(x)

def dump_ctor_vt_writes(ctor_va):
    sz = R.ATLAS.get(hx(ctor_va), {}).get("size") or 1024
    print("  == ctor %s size=%s ==" % (hx(ctor_va), sz))
    for ins in R.disasm_body(ctor_va, sz):
        if ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if a.type == X86_OP_MEM and b.type == X86_OP_IMM:
                v = b.imm & 0xFFFFFFFF
                if 0x7E0000 <= v <= 0x7FC000:
                    try:
                        bn = ins.reg_name(a.mem.base)
                    except Exception:
                        bn = str(a.mem.base)
                    print("    %s  %-28s %-40s ; disp=%s base=%s" % (
                        hx(ins.address), ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str,
                        hex(a.mem.disp & 0xFFFFFFFF), bn))
    return

def qi_profile_detail(qva):
    if not qva or not R.in_text(qva):
        return
    sz = R.ATLAS.get(hx(qva), {}).get("size") or 128
    print("    == QI %s size=%s ==" % (hx(qva), sz))
    for ins in R.disasm_body(qva, sz):
        if ins.id == X86_INS_RET or ins.id == X86_INS_CALL or \
           (ins.id == X86_INS_MOV and len(ins.operands)==2 and ins.operands[0].type==X86_OP_REG
            and ins.operands[0].reg==X86_REG_EAX):
            print("       %s  %-20s %s" % (hx(ins.address), ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str))

def vt_slot0(vt):
    q = R.u32(vt)
    return q

TARGETS = ["006C2B10", "006C3710", "006C3D10", "006C2F90", "006C3A10"]
GD = {x["entry"]: x for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"gather.json"),encoding="utf-8"))}

for e in TARGETS:
    print("\n######## ROW %s (%s) ########" % (e, GD[e]["name"]))
    gd = GD[e]
    print("  QI site: %s   release: %s" % (gd["qi"]["addr"] if gd["qi"] else "-", gd["release"]["addr"] if gd["release"] else "-"))
    # object ctor va
    objctor = int(gd["obj_ctor_calls"][0]["dest"],16) if gd["obj_ctor_calls"] else None
    if objctor:
        dump_ctor_vt_writes(objctor)
    # for each vt cand, show slot0 and whether slot0 chains to 0x410260
    for oc in gd["qiverify"]:
        for p in oc["vt_cands"]:
            vt = int(p["vt"],16)
            q = R.u32(vt)
            print("    vt=%s slot0(QI)=%s QI_ok=%s  -> profile:" % (p["vt"], hx(q) if q else "-", p["QI_ok"]))
            if q: qi_profile_detail(q)
