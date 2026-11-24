# -*- coding: utf-8 -*-
"""Check factory-vtable slot0 for all 13 rows, and dump QI call-site context
(what vptr is loaded into eax before `call [eax]`). Read-only.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
AN = {x["entry"]: x for x in json.load(open(os.path.join(HERE,"analysis.json"),encoding="utf-8"))}
GD = {x["entry"]: x for x in json.load(open(os.path.join(HERE,"gather.json"),encoding="utf-8"))}
ROWS = json.load(open(os.path.join(HERE,"b3_rows.json"),encoding="utf-8"))["rows"]

def hx(x): return R.hx(x)

for row in ROWS:
    e = row["entry"]
    ea = int(e,16)
    c = next(c for c in AN[e]["ring2"]["cands"] if c["rtti_name"] and c["slotnum_match"])
    vtbase = int(c["vtable_base"],16)
    slot0 = R.u32(vtbase)
    qs = GD[e]["qi"]["addr"]
    qa = int(qs,16)
    insns = list(R.disasm_body(ea, int(row["size"])))
    idx = {i.address:k for k,i in enumerate(insns)}
    k = idx.get(qa)
    ctx = []
    if k is not None:
        for i in insns[max(0,k-6):k+2]:
            ctx.append("%s %s" % (hx(i.address), i.mnemonic+" "+i.op_str))
    print("%s  factory_vt=%s slot0=%s  QIsite_ctx: %s" % (
        e, c["vtable_base"], hx(slot0) if slot0 else "-", " | ".join(ctx)))
