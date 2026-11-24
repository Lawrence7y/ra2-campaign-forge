# -*- coding: utf-8 -*-
"""Print full disassembly + return-profile for the 9 vector rows to judge ③b contract."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b5_rows.json"), encoding="utf-8") as f:
    rows = json.load(f)

only = None
if len(sys.argv) > 1:
    only = sys.argv[1].upper()

for r in rows:
    entry = r["entry"]
    if only and entry != only:
        continue
    ea = int(entry, 16); size = int(r["size"])
    insns = R.disasm_body(ea, size)
    print("=" * 110)
    print(entry, r["name"])
    for i in insns:
        # annotate calls with target
        ann = ""
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            ann = " ; call -> %08X" % (i.operands[0].imm & 0xFFFFFFFF)
        print("  %08X  %-18s %-42s%s" % (i.address, i.bytes.hex(), ("%s %s" % (i.mnemonic, i.op_str)), ann))
    prof = R.callee_return_profile(ea)
    print("  RETURN PROFILE: consts=%s n_rets=%d origins=%s" % (
        [hex(x) for x in sorted(prof["consts"])] if prof else None,
        prof["n_rets"] if prof else -1,
        [list(o) for o in prof["origins"]] if prof else None))
