# -*- coding: utf-8 -*-
"""针对强候选定核：005414C0 的间接 callee 解析 + -1 返回；MPCooperative 各站点 callee 归类。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
data = {r["entry"]: r for r in json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))}

def va(x): return int(x,16) if isinstance(x,str) else int(x)

def callee_ret_scan(target):
    if not target or not R.in_text(target): return []
    size = R.ATLAS.get(R.hx(target), {}).get("size", 200)
    code = R.read_va(target, size)
    insns = list(MD.disasm(code, target))
    retlines=[]; eax="?"
    for ins in insns:
        if ins.id==0: continue
        if ins.mnemonic in ("xor","sub") and ins.op_str=="eax, eax": eax="0"
        elif ins.mnemonic=="mov" and ins.op_str=="eax, 0xffffffff": eax="ffffffff(-1)"
        elif ins.mnemonic=="or" and ins.op_str=="eax, 0xffffffff": eax="ffffffff(-1)"
        elif ins.mnemonic=="ret":
            retlines.append("%08X: ret (eax=%s)"%(ins.address,eax)); eax="?"
    return retlines[:12]

vt = 0x7EC16C
slot18 = R.u32(vt+0x18)
print("005414C0: IPXManagerClass vt=%08X slot+0x18 @ %08X -> callee=%s" % (vt, vt+0x18, R.hx(slot18) if slot18 else None))
print("  callee ret profile:", callee_ret_scan(slot18))
r=data["005414C0"]
for s in r["chA_sites"]:
    print("  site call=%s test=%s(%s imm=%s) jcc=%s->%s" % (
        s["call_addr"],s["test_addr"],s["test_kind"],s["test_imm"],s["jcc_mnemonic"],s.get("jcc_target")))
    b=R.read_va(va(s["call_addr"]),12)
    print("    call+检查 bytes:", " ".join("%02X"%x for x in b))

CRT = {0x7c8e17:"malloc",0x7c8d20:"CRT",0x7c91d0:"CRT",0x7c8b3d:"CRT"}
for e in ["005C18A0","005C1A10","005C1DC0","005C2100","005C2680"]:
    print("="*80)
    print(e, data[e]["hint_name"])
    for i,s in enumerate(data[e]["chA_sites"][:6]):
        c=s.get("callee")
        nm = CRT.get(c, "") if c else "(indirect)"
        print("  site%d call=%s callee=%s %-12s kind=%s imm=%s jcc=%s" % (
            i, s["call_addr"], R.hx(c) if c else None, nm, s["test_kind"], s["test_imm"], s["jcc_mnemonic"]))
