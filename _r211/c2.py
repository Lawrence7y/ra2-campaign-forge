# -*- coding: utf-8 -*-
"""R211 c2：HouseClass QI 0x4f6830 全反汇编（逐指令）+ 与 6 个 Locomotion QI / Aircraft QI 的对照模板。
要点：验证 S2 常量直写是不是 mov dword ptr [out], 4。
"""
import sys,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def dump(a,lim=1400,maxn=400,label=''):
    o=P.r2o(a); print('--- %s @%s ---'%(label,hex(a)))
    n=0
    for i in md.disasm(P.RAW[o:o+lim],a):
        print('  %08x  %-22s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
        n+=1
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if n>maxn: break
dump(0x4f6830,label='HouseClass QI')
print()
dump(0x4af720,label='DriveLocomotion QI')
