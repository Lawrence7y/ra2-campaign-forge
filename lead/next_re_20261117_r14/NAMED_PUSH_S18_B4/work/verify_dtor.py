# -*- coding: utf-8 -*-
"""最终咽喉复核：005414C0 的 ④ 构造安装点是否真把 vt 0x7EC16C 写入活对象。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
vt = 0x7EC16C
# 反汇编两个安装点附近，确认 C7 .../mov [..],imm32 == vt
for center in [0x005408F0, 0x005409F0]:
    start = center
    code = R.read_va(start, 0x50)
    print("=== around %08X ===" % center)
    for ins in MD.disasm(code, start):
        mark = " <<< VT WRITE" if (ins.operands and any(
            o.type==3 and o.imm and (o.imm & 0xFFFFFFFF)==vt for o in ins.operands)) else ""
        print("  %08X: %-8s %-28s | %s%s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(), mark))
# 检查是否 atexit 注册（push <func>; call 0x7C978A）
print("atexit check: 0x7C978A registered funcs would push func then call 0x7C978A; witness marked atexit=False")
