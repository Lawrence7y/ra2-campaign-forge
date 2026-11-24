# -*- coding: utf-8 -*-
"""w4: 00709A40 ③b① 门控-动作核验 —— 各闸被调目标是否相异（M4/细则#1）。"""
import os,sys
sys.path.insert(0,os.path.dirname(__file__))
import ax_lib
from capstone import *
pe=ax_lib.load(); MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def dis(addr,n=24):
    raw=pe.bytes_at(addr,n); return '; '.join('%s %s'%(i.mnemonic,i.op_str) for i in MD.disasm(raw,addr))

print("=== direct callee 0x71ABC0 ==="); print(dis(0x71ABC0))
print("=== direct callee 0x6385C0 ==="); print(dis(0x6385C0))
# TechnoClass vtable 0x7F4960, slots 0x4d0/4=308 and 0x430/4=268
vt=0x7F4960
for off in (0x4d0,0x430):
    slot=off//4; target=pe.u32(vt+off)
    print("vt[%d] +0x%x -> %08X : %s"%(slot,off,target if target else 0,dis(target,16) if target and pe.is_code(target) else 'N/A'))
# 检查 0x71ABC0 与 0x6385C0 是否 ICF 同型（首字节）
for a in (0x71ABC0,0x6385C0):
    print("%08X bytes=%s"%(a,pe.bytes_at(a,8).hex()))
