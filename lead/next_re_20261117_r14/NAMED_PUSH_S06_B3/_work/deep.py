# -*- coding: utf-8 -*-
"""Deep disassembly dump: per-row full body with bytes, key callee bodies, vtable slot0."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

def dump_func(va, size, label):
    code = R.read_va(va, size)
    insns = R.disasm(va, code)
    print("---- %s @ %08X size=%d insn=%d ----" % (label, va, size, len(insns)))
    for ins in insns:
        raw = code[ins.address - va: ins.address - va + ins.size]
        print("  %08X  %-20s  %-8s %s" % (ins.address, raw.hex(" "), ins.mnemonic, ins.op_str))

# vtable slot 0 check for each distinct vtable
print("=" * 100)
print("VTABLE SLOT-0 CHECK (trap: small member table vs real object main vtable)")
seen = set()
for rec in A:
    for s in rec["ring2_slots"]:
        vb = s.get("vtable_base")
        if not vb or vb in seen: continue
        seen.add(vb)
        vbv = int(vb, 16)
        slot0 = C2.u32(vbv)
        slot1 = C2.u32(vbv + 4)
        print("  vt=%s slot0=%s slot1=%s refslot=%s(%s) name=%s" % (
            vb, R.hx(slot0) if slot0 is not None else "?", R.hx(slot1) if slot1 is not None else "?",
            s["slot_va"], s["slot_off"], s.get("rtti_name")))

# callee bodies referenced by ring3 sites
print("=" * 100)
print("KEY CALLEE BODIES")
for callee in [0x410320, 0x410380, 0x4103E0, 0x5F8000, 0x5F9720, 0x5F5E80]:
    sz = R.ATLAS.get(R.hx(callee), {}).get("size")
    if sz:
        dump_func(callee, min(sz, 256), "callee %08X" % callee)
    else:
        print("  callee %08X: no atlas size" % callee)

# full body for every row
print("=" * 100)
print("FULL ROW BODIES")
for rec in A:
    va = int(rec["entry"], 16)
    sz = rec["ring1"].get("atlas_size")
    dump_func(va, sz, "#%d %s %s" % (rec["idx"], rec["entry"], rec["name"]))
