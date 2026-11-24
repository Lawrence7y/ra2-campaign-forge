# -*- coding: utf-8 -*-
"""精确返回常量剖析：追踪 eax 来源直到每个 ret，捕获 mov/or/xor/neg/sbb/and/sub 形态。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

def profile(va, sz=None):
    sz = sz or R.ATLAS.get(R.hx(va),{}).get('size') or 256
    insns = R.disasm(va, R.read_va(va, sz))
    # eax state: set of symbolic values
    state = {'eax': 'unk'}
    rets = []
    for idx,ins in enumerate(insns):
        i = ins
        if i.id == 0: continue
        o = ins.operands
        def is_eax(op): return op.type==X86_OP_REG and op.reg==X86_REG_EAX
        def is_al(op): return op.type==X86_OP_REG and op.reg==X86_REG_AL
        if i.id==X86_INS_MOV and len(o)==2 and is_eax(o[0]):
            state['eax'] = ('imm',o[1].imm & 0xffffffff) if o[1].type==X86_OP_IMM else 'unk'
        elif i.id==X86_INS_XOR and len(o)==2 and is_eax(o[0]) and is_eax(o[1]):
            state['eax'] = ('imm',0)
        elif i.id==X86_INS_OR and len(o)==2 and is_eax(o[0]) and o[1].type==X86_OP_IMM:
            state['eax'] = ('or', o[1].imm & 0xffffffff)
        elif i.id==X86_INS_AND and len(o)==2 and is_eax(o[0]) and o[1].type==X86_OP_IMM:
            state['eax'] = ('and', o[1].imm & 0xffffffff) if isinstance(state['eax'],tuple) else 'unk'
        elif i.id==X86_INS_NEG and len(o)==1 and is_eax(o[0]):
            state['eax']=('neg', state['eax'])
        elif i.id==X86_INS_SBB and len(o)==2 and is_eax(o[0]) and is_eax(o[1]):
            state['eax']=('sbb', state['eax'])
        elif i.id==X86_INS_CALL:
            state['eax']='callret'
        elif i.id==X86_INS_RET:
            rets.append((i.address, state['eax'], i.bytes.hex()))
            state['eax']='unk'
    return rets

if __name__ == '__main__':
    for a in sys.argv[1:]:
        va=int(a,16)
        print('==== %08X atlas=%s ====' % (va, R.ATLAS.get(R.hx(va),{}).get('size')))
        for addr,val,bb in profile(va):
            print('   ret@%08X (%s) eax=%s' % (addr,bb,val))
