# -*- coding: utf-8 -*-
"""B3 环④ 见证核验：安装点 + 派发站点抽样反汇编 + atexit 复核。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

VT = 0x007F6218
SLOT = 0x007F6238
OFF = 0x20  # slot#8

print("="*90)
print("环④ 见证核验 entry=00748190 vt=%08X slot=%08X off=0x%X" % (VT, SLOT, OFF))
print("="*90)

# 1) 确认 slot 里确实是 entry
print("\n[slot 驻留]")
print("  [%08X] = %08X (期望 00748190)" % (SLOT, W.u32(SLOT)))

# 2) 安装点：vt 写入活对象
print("\n[vptr 安装点 (写 vt 到活对象)]")
inst = W.find_vtable_writes(VT)
for g in inst["global"]:
    f = W.find_containing_atlas_func(g["write_va"])
    ax = W.is_atexit_registered(f[0]) if f else False
    print("  write=%08X global=%s in_func=%s atexit=%s" % (
        g["write_va"], g["global"], f[1] if f else None, ax))

# 3) 抽样派发站点 call [reg+0x20]
print("\n[派发站点抽样 call dword ptr [reg+0x20]]")
MD = __import__("capstone").Cs(__import__("capstone").CS_ARCH_X86, __import__("capstone").CS_MODE_32)
MD.detail = True; MD.skipdata = True
from capstone.x86 import X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID
cnt = 0
samples = []
for ins in MD.disasm(R.TEXT_DATA, R.TEXT_VA):
    if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
        m = ins.operands[0].mem
        if m.disp == 0x20 and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
            samples.append(ins)
            cnt += 1
print("  总派发站点数 =", cnt)
for ins in samples[:6]:
    print("  %08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
