# -*- coding: utf-8 -*-
"""第五轮：解析 0x40FDxx API 返回约定；核 row1 循环 ③b④；核行2/3/4 站点被调返回。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C

def dis(va, n, label):
    print("\n=== %s @ %08X ===" % (label, va))
    for i in R.disasm_body(va, n):
        if i.id:
            extra=""
            if i.id==R.X86_INS_CALL and i.operands and i.operands[0].type==R.X86_OP_IMM:
                extra=" ; callee=%08X"%(i.operands[0].imm&0xFFFFFFFF)
            print("  %08X %-20s %s%s" % (i.address, i.bytes.hex(), i.mnemonic+" "+i.op_str, extra))

print("### 被调 API 返回约定（行2/行3 的 cmp/test 目标）")
dis(0x40FD6E, 40, "0065D254 callee [0x7e1128]")
dis(0x40FD9A, 40, "0065D26C callee [0x7e1130]")
dis(0x40FD8C, 40, "0065D289 callee [0x7e112c]")
dis(0x40F908, 40, "0065D3B7 callee [0x7e11e0]")
dis(0x40F868, 40, "0065D3C9 callee [0x7e1200]")
dis(0x65D420, 30, "007F091C = RawFileClass slot6")

print("\n\n### row1 00432050 循环回边与写点（③b④ 评估）")
# 打印 0x4320B0..0x432260 段，标出所有 call / 写内存 / 回边
for i in R.disasm_body(0x4320a0, 0x1c0):
    if not i.id: 
        continue
    tag=[]
    if i.id==R.X86_INS_CALL: tag.append("CALL")
    if i.id in (R.X86_INS_MOV,) and i.operands and i.operands[0].type==R.X86_OP_MEM: tag.append("WRITE?")
    if i.id in (R.X86_INS_JMP,R.X86_INS_JE,R.X86_INS_JNE,R.X86_INS_JG,R.X86_INS_JGE,R.X86_INS_JL,R.X86_INS_JLE):
        tag.append("JMP")
    print("  %08X %-20s %-42s %s" % (i.address, i.bytes.hex(), i.mnemonic+" "+i.op_str, ",".join(tag)))
