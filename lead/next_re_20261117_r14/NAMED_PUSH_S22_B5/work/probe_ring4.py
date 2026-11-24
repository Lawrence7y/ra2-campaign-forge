# -*- coding: utf-8 -*-
"""④ probe: examine vtable-install functions (ctor vs dtor), their callers, and whether install is live.
Also collect ALL direct calls inside each body (look for any Find returning -1 / status code, ③b diligence)."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "ring_analysis.json"), encoding="utf-8") as f:
    RA = json.load(f)

def func_dis(ea, cap):
    return R.disasm_body(ea, cap)

for entry, d in RA.items():
    print("=" * 110)
    print(entry, d["name"])
    # all calls in body (③b diligence)
    ea = int(entry, 16); size = int(json.load(open(os.path.join(HERE,"b5_rows.json"),encoding="utf-8"))[0]["size"]) if False else None
    # get size from dump
    with open(os.path.join(HERE,"dump.json"),encoding="utf-8") as f:
        sz = json.load(f)[entry]["size"]
    insns = R.disasm_body(ea, sz)
    calls = []
    for i in insns:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            calls.append("%08X" % (i.operands[0].imm & 0xFFFFFFFF))
        elif i.id == X86_INS_CALL:
            calls.append(i.op_str)
    print("  body calls:", calls)
    # ④ install functions
    if not d["writes"]:
        print("  (no writes)")
        continue
    for ins in d["writes"]["installs"]:
        f = ins["in_func"]
        if not f:
            print("  install@%s global=%s (no containing atlas func) atexit=%s" % (ins["write_va"], ins["global"], ins["atexit"]))
            continue
        ea2, _, sz2 = f
        ea2 = int(ea2, 16)
        fdis = func_dis(ea2, sz2)
        # signature: writes vtable to [reg]? deletes? calls operator delete (0x7C8B3D/0x7C93E8)?
        has_delete = False
        vtable_writes = []
        calls_in = []
        for i in fdis:
            if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
                c = i.operands[0].imm & 0xFFFFFFFF
                calls_in.append("%08X" % c)
                if c in (0x7C8B3D, 0x7C93E8):
                    has_delete = True
        # who calls this install func?
        callers = C.find_direct_calls(ea2)
        print("  install@%s in_func=%08X(size=%d) atexit=%s has_operator_delete=%s callers=%s" % (
            ins["write_va"], ea2, sz2, ins["atexit"], has_delete,
            ["%08X" % x for x in callers[:8]]))
        print("     calls_in:", calls_in[:12])
        # print first ~12 insns of install func to see ctor pattern
        for i in fdis[:14]:
            print("       %08X %s %s" % (i.address, i.bytes.hex(), ("%s %s"%(i.mnemonic,i.op_str))))
