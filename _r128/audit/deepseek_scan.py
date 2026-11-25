# -*- coding: utf-8 -*-
"""R128 deepseek auditor: resync linear sweep over full .text with capstone disasm_lite only."""
import struct, json, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
d=open(EXE,'rb').read()
T_PTR, T_SZ, T_VA = 0x1000, 0x3e0000, 0x401000
T=d[T_PTR:T_PTR+T_SZ]
md=Cs(CS_ARCH_X86, CS_MODE_32)

def sweep(buf, base):
    """resync linear sweep: on decode failure advance 1 byte"""
    off=0
    n=len(buf)
    resync=[]
    while off<n:
        got=list(md.disasm_lite(buf[off:off+16], base+off, 1))
        if not got:
            resync.append(base+off)
            off+=1
            continue
        a,s,m,o=got[0]
        yield (a,s,m,o)
        off+=s

if __name__=='__main__':
    pats=sys.argv[1:] or ['0x87f7e8','0x7ea6e8','0x7e36c0','0x7f7c90','0x89a29c']
    out={p:[] for p in pats}
    cnt=0
    for a,s,m,o in sweep(T,T_VA):
        cnt+=1
        for p in pats:
            if p in o:
                out[p].append((a,s,m,o))
    print('instructions decoded:',cnt)
    for p in pats:
        print('== %s : %d hits'%(p,len(out[p])))
        for a,s,m,o in out[p]:
            print('  %x  %s %s'%(a,m,o))
