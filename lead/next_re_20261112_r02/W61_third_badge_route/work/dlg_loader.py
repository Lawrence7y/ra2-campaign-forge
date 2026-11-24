#!/usr/bin/env python3
# W61: disassemble Run_Dialog (0x622650) + companion (0x622800) and resolve
# any string-VA immediates -> this is where the dialog background art would be loaded.
import sys, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=sys.argv[1]
data=open(EXE,"rb").read(); pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase
def rva2off(r):
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
    return None
def va2off(v): return rva2off(v-IB)
def cstr(va,n=120):
    o=va2off(va)
    if o is None: return None
    b=data[o:o+n].split(b"\x00")[0]
    if not b or any(c<0x20 or c>0x7e for c in b): return None
    return b.decode("latin1")
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
def dis(start,length,label):
    print("\n=== %s 0x%08X..0x%08X ===" % (label,start,start+length))
    o=va2off(start); code=data[o:o+length]
    strs={}
    for ins in md.disasm(code,start):
        for op in ins.operands:
            if op.type==2:
                v=op.imm & 0xFFFFFFFF
                if 0x810000<=v<=0x8C0000:
                    s=cstr(v)
                    if s: strs[v]=s
        print("  0x%08X  %-18s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str))
    print("--- strings referenced ---")
    for v,s in sorted(strs.items()): print("  0x%08X %r" % (v,s))
dis(0x622650,0x1B0,"Run_Dialog 0x622650")
dis(0x622800,0x120,"0x622800")
dis(0x622B50,0x120,"0x622B50 (called at 0x52EC1D)")
