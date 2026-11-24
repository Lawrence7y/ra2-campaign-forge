from re_core import *
from capstone.x86 import X86_OP_IMM

def call_xrefs(target):
    out=[]
    for lo,hi,raw,rawsz,name in SEGS:
        if name!='.text': continue
        code=PE.__data__[raw:raw+rawsz]
        for p in range(len(code)-5):
            if code[p]!=0xE8: continue
            rel=struct.unpack_from('<i',code,p+1)[0]
            if lo+p+5+rel==target: out.append(lo+p)
    return out

for t in [0x40F510,0x75E3B0,0x46C440,0x46C790]:
    print(hex(t),'direct callers',[hex(x) for x in call_xrefs(t)])

def ctor_evidence(ctor,n,regs,vptr,glob):
    print('\nCTOR',hex(ctor),'vptr',hex(vptr),'glob',hex(glob))
    ins=list(dis(ctor,n))
    for i in ins:
        s=fmt(i)
        if i.address in [x for x in range(0,1)]: pass
        # print relevant: write vptr, take globals, array insert, call dtor? write +0x24
        if ('mov dword ptr [ebp], 0x' in s or 'mov dword ptr [esi], 0x' in s or 'mov dword ptr [ebp + 0x24]' in s or 'mov dword ptr [esi + 0x24]' in s or f'0x{glob:08x}' in s.lower().replace('0x','')):
            print(s)

ctor_evidence(0x75cec0,5000,None,0x7f6b30,0x8874c4)
ctor_evidence(0x46bbc0,6000,None,0x7e4948,0xa83c84)
