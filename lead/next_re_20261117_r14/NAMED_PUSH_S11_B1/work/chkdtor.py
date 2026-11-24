import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
for va in (0x004D03A0,0x005172C0,0x006635C0,0x004B4D00,0x004B66F0,0x0054DFA0):
    at=atlas_func_of(va)
    body=[i for i in dis(va, read_va(va, at[1] if at else 0x80)) if i.id!=0]
    frees=[hx(i.address) for i in body if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM and (i.operands[0].imm&0xFFFFFFFF) in (0x7C8B3D,0x406060)]
    flags=[hx(i.address)+' '+i.mnemonic+' '+i.op_str for i in body if i.id==X86_INS_TEST and 'esp + 8' in i.op_str]
    print('%s size=%-4s frees=%s delflag=%s' % (hx(va), at[1] if at else '-', frees, flags))
