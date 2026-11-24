# -*- coding: utf-8 -*-
"""对 6 个强候选详细导出环②/④ 见证（含 ctor 写点反汇编 + 派发站点）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
wit = json.load(open(os.path.join(WORK, "witness.json"), encoding="utf-8"))
STRONG = {"004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"}

out = []
def w(s=""):
    out.append(s); print(s)

for r in wit:
    if r["entry"] not in STRONG:
        continue
    w("="*88)
    w("### %s %s (size=%s)" % (r["entry"], r["name"], r["atlas_size"]))
    w("  direct callers = %s" % r["direct_callers"])
    for s in r["slots"]:
        if not s.get("rtti_name"):
            continue
        w("  SLOT va=%s vbase=%s off=%s RTTI=%s" % (
            s["slot_va"], s.get("vtable_base"), s.get("slot_off"), s.get("rtti_name")))
        w("    COL=%s TD=%s name_va=%s" % (s.get("col"), s.get("td"), s.get("name_va")))
        # ctor/atexit writes disassembly
        for g in s.get("global_writes", []):
            f = g.get("in_func")
            w("    write@%s global=%s in_func=%s atexit=%s" % (
                g.get("write_va"), g.get("global"),
                ("%08X size=%d"%(f[0], f[2])) if f else None, g.get("atexit")))
        # vtable imm loads
        # 找以 slot_off 派发的 call [reg+off] 站点数（宽口径：全 .text 内 call dword [reg+off]）
        slot_off = s.get("slot_off")
        if slot_off is not None:
            cnt = 0
            samples = []
            for ins in R.disasm(R.TEXT_VA, R.TEXT_DATA):
                pass  # too slow; skip full-image capstone
            w("    dispatch sites (call dword ptr [reg+%d]) not enumerated here" % slot_off)

open(os.path.join(WORK, "strong_witness.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\nwrote strong_witness.txt")
