# -*- coding: utf-8 -*-
"""核 6 强候选的环④：ctor 写点反汇编（确认是 vptr install）+ 派发站点枚举。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID, X86_OP_MEM

WORK = os.path.dirname(os.path.abspath(__file__))
wit = json.load(open(os.path.join(WORK, "witness.json"), encoding="utf-8"))
STRONG = {"004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"}

# 找 call dword ptr [reg + disp] 中 disp == slot_off 的站点（disp8 或 disp32）
# 用 capstone 扫全 .text（约 140 万条，S13_K9 先例可行）
def find_dispatch_sites(slot_off):
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
    sites = []
    for ins in md.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == slot_off and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
                sites.append(ins.address)
    return sites

out=[]
def w(s=""):
    out.append(s)

for r in wit:
    if r["entry"] not in STRONG:
        continue
    w("="*88)
    w("### %s %s" % (r["entry"], r["name"]))
    for s in r["slots"]:
        if not s.get("rtti_name"):
            continue
        w("  slot@%s vbase=%s off=%s rtti=%s" % (s["slot_va"], s.get("vtable_base"), s.get("slot_off"), s.get("rtti_name")))
        slot_off = s.get("slot_off")
        # ctor 写点反汇编
        for g in s.get("global_writes", []):
            wv = int(g["write_va"], 16)
            insns = R.disasm_body(wv, 32)
            seq = "; ".join("%X:%s %s"%(i.address,i.mnemonic,i.op_str) for i in insns[:4])
            w("    write@%s atexit=%s :: %s" % (g["write_va"], g.get("atexit"), seq))
        # 派发站点
        disp = find_dispatch_sites(slot_off)
        w("    dispatch call [reg+%d] sites = %d (sample %s)" % (
            slot_off, len(disp), ["%08X"%x for x in disp[:12]]))

open(os.path.join(WORK, "ring4_verify.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote ring4_verify.txt")
for l in out:
    print(l)
