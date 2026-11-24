# -*- coding: utf-8 -*-
"""分类 7 个写点函数：构造 vs 删除析构 vs atexit 全局析构。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

# IAT 全表（解析所有 import thunk）
pe=R._pe
iat={}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    dll=d.dll.decode('latin1')
    for imp in d.imports:
        if imp.address:
            iat[imp.address]=(dll, imp.name.decode('latin1') if imp.name else 'ord%d'%imp.ordinal)

# 反解 thunk VA -> IAT name（FF 25 abs）
def thunk_name(va):
    code=R.read_va(va,6)
    if len(code)>=6 and code[:2]==b'\xff\x25':
        i=struct.unpack('<I',code[2:6])[0]
        return iat.get(i,('?','?'))
    return None

for t in (0x7C8B3D,0x7C897A,0x7C89B6,0x4068E0,0x7C978A):
    print("thunk %08X -> %s" % (t, thunk_name(t)))

funcs=[0x007B0D90,0x007B1790,0x007B19C0,0x007B1AB0,0x007B2780,0x007B2DB0,0x007B2E50,0x007B4170]
for fa in funcs:
    info=R.ATLAS.get("%08X"%fa,{})
    sz=info.get('size',0)
    code=R.read_va(fa,sz if sz else 360)
    ins=list(MD.disasm(code,fa))
    print("\n"+"="*90)
    print("FUNC %08X size=%d nins=%d"%(fa,sz,len(ins)))
    # call 序列（带 thunk 名）
    for x in ins:
        if x.id==0: continue
        if x.id==X86_INS_CALL and x.operands and x.operands[0].type==X86_OP_IMM:
            t=x.operands[0].imm & 0xFFFFFFFF
            print("   CALL %08X @%08X %s"%(t,x.address, thunk_name(t) or ''))
        if x.id==X86_INS_RET:
            print("   RET @%08X ops=%s"%(x.address, x.op_str))
    # atexit 注册
    ax=W.is_atexit_registered(fa)
    print("   atexit_registered=%s"%bool(ax))
