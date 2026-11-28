# -*- coding: utf-8 -*-
"""R211 c12：HouseClass QI 0x4f6830 的【全函数体】反汇编（c2 只扫到首个 ret 0xc 即停，
但体内在第 5 个 GUID 比较后 jne 到 0x4f68fc，那段被漏掉）。
目的：律 U 的 R 集合是否包含 8 与 12（律 W 已证 V 含 8/12）。"""
import sys
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
a=0x4f6830; o=P.r2o(a)
base=a
n=0
for i in md.disasm(P.RAW[o:o+600],a):
    print('  %08x  %-20s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    n+=1
    if n>150: break
