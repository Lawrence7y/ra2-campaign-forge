#!/usr/bin/env python3
# W61: disassemble the candidate control proc / dialog init regions.
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
def dis(name,start,length):
    print("\n=== DISASM %s 0x%08X..0x%08X ===" % (name,start,start+length))
    o=va2off(start); code=data[o:o+length]
    for ins in md.disasm(code,start):
        ann=""
        # annotate immediates that are strings / global addrs
        for op in ins.operands:
            pass
        print("  0x%08X  %-20s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str))
    print("=== END %s ===" % name)
dis("0x471300 control-proc?", 0x471300, 0x140)
dis("0x6C9300 control-proc?", 0x6C92C0, 0x180)
dis("0x52DE00 dialog-init / subclass?", 0x52DE00, 0x640)
dis("0x777C00 RegisterClassA vicinity", 0x777C40, 0x120)
