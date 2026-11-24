#!/usr/bin/env python3
# W61: disassemble 0x6040C0..0x6042C0 - the campaign-icon/animation string refs.
import sys,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=sys.argv[1]
d=open(EXE,'rb').read(); p=pefile.PE(EXE,fast_load=False); IB=p.OPTIONAL_HEADER.ImageBase
def o(va):
    for s in p.sections:
        if s.VirtualAddress<=va-IB<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(va-IB-s.VirtualAddress)
def cs(va,n=80):
    x=o(va)
    if x is None: return None
    b=d[x:x+n].split(b'\x00')[0]
    if not b or any(c<0x20 or c>0x7e for c in b): return None
    return b.decode('latin1')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
S,E=0x6040C0,0x6042E0
x=o(S); code=d[x:x+(E-S)]
for ins in md.disasm(code,S):
    ann=''
    for op in ins.operands:
        if op.type==2:
            v=op.imm&0xFFFFFFFF
            if 0x810000<=v<=0x8C0000:
                s=cs(v)
                if s: ann+='  ; -> %r'%s
    print('0x%08X  %-20s %s%s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str,ann))
