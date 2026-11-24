# -*- coding: utf-8 -*-
"""逐行 dump ③b② 站点窗口 + direct caller 窗口，供人工判定 eax 陷阱 / 真实分支 / 真实调用者。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

def va(x):
    return int(x, 16) if isinstance(x, str) else int(x)

def dump_window(center_va, before=14, after=18, rad=110):
    start = center_va - rad
    if start < R.TEXT_VA: start = R.TEXT_VA
    code = R.read_va(start, 2*rad + 64)
    insns = list(MD.disasm(code, start))
    out=[]
    for ins in insns:
        if center_va - rad <= ins.address <= center_va + rad:
            mark = " <<<" if ins.address == center_va else ""
            out.append("  %08X: %-8s %-30s | %s%s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(), mark))
    return "\n".join(out)

for r in data:
    print("="*110)
    print("%s %s  chA p3=%d" % (r["entry"], r["hint_name"], r["chA"]["p3"]))
    for s in r["chA_sites"][:6]:
        print("  [3b2 site] call=%s callee=%s test=%s(%s imm=%s) jcc=%s %s" % (
            s["call_addr"], s.get("callee"), s["test_addr"], s["test_kind"], s["test_imm"], s["jcc_addr"], s["jcc_mnemonic"]))
        print("    sig_taken=%s" % s["sig_taken"])
        print("    sig_fallthrough=%s" % s["sig_fallthrough"])
        print(dump_window(va(s["call_addr"]), rad=70))
    for ca in r["direct_callers"][:3]:
        print("  [direct caller] %s" % ca)
        print(dump_window(va(ca), rad=60))
