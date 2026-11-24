# -*- coding: utf-8 -*-
"""工厂自身 ④：找 ctor(写工厂vt) 的调用者、slot3 派发点，排除析构器/atexit。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C
from capstone.x86 import *

HERE=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"analysis.json"),encoding="utf-8") as f: A=json.load(f)

def direct_callers(target):
    return [R.hx(x) for x in C.find_direct_calls(target)]

# 工厂 ctor 从 probe 已知：entry -> ctor 写工厂 vt
FACT_CTOR = {
 "006BF810":"006BF740","006BF990":"006BF8C0","006BFB10":"006BFA40","006BFC90":"006BFBC0",
 "006BFE10":"006BFD40","006BFF90":"006BFEC0","006C0110":"006C0040","006C0290":"006C01C0",
 "006C0410":"006C0340","006C0590":"006C04C0","006C0710":"006C0640","006C0890":"006C07C0",
 "006C0A10":"006C0940","006C0B90":"006C0AC0","006C0D10":"006C0C40","006C0E90":"006C0DC0",
}
# 校验 ctor 字节含写本工厂 vt
for e,ctor in FACT_CTOR.items():
    cva=int(ctor,16)
    ins=list(R.disasm_body(cva,32))
    w=[(R.hx(i.address),i.mnemonic+" "+i.op_str) for i in ins if i.id==X86_INS_MOV]
    callers=direct_callers(cva)
    atexit=C.is_atexit_registered(cva)
    # ctor 内部是否 call 析构特征(delete 0x7C8B3D/free)
    dels=[R.hx(i.operands[0].imm&0xFFFFFFFF) for i in ins if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM and (i.operands[0].imm&0xFFFFFFFF) in (0x7C8B3D,0x7C93E8)]
    print("%s ctor=%s atexit=%s callers=%s dels=%s | %s" % (e,ctor,atexit,callers[:6],dels,w[:5]))
