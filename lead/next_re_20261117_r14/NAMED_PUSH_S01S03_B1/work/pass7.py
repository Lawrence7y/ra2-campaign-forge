# -*- coding: utf-8 -*-
"""row5 WinMainCRTStartup ③ 站点快速核对（② 已 FAIL，仅如实记录）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
ea=0x7cd80f
ins=R.disasm_body(ea,253)
for i in ins:
    if i.id in (R.X86_INS_CALL,R.X86_INS_TEST,R.X86_INS_JE,R.X86_INS_JNE,R.X86_INS_RET):
        extra=""
        if i.id==R.X86_INS_CALL and i.operands and i.operands[0].type==R.X86_OP_IMM:
            extra=" ; callee=%08X"%(i.operands[0].imm&0xFFFFFFFF)
        print("  %08X %-20s %s%s"%(i.address,i.bytes.hex(),i.mnemonic+" "+i.op_str,extra))
