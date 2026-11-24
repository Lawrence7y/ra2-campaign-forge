#!/usr/bin/env python3
# W61: locate generic control proc / art binding for badge control IDs.
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
TEXT_OFF=pe.sections[0].PointerToRawData; TEXT_SZ=pe.sections[0].SizeOfRawData
TEXT_VA=IB+pe.sections[0].VirtualAddress
text=data[TEXT_OFF:TEXT_OFF+TEXT_SZ]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True

def dis_range(start,length,label):
    print("\n--- %s 0x%08X..0x%08X ---" % (label,start,start+length))
    o=va2off(start); code=data[o:o+length]
    for ins in md.disasm(code,start):
        print("  0x%08X  %-18s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str))

print("=== push 0x6EA/0x6EB/0x6EC occurrences in .text ===")
for val in [0x6ea,0x6eb,0x6ec]:
    pat=b"\x68"+struct.pack("<I",val)
    i=0; loc=[]
    while True:
        j=text.find(pat,i)
        if j<0: break
        loc.append(TEXT_VA+j); i=j+1
    print("  push 0x%03X : %d sites : %s" % (val,len(loc),", ".join("0x%08X"%x for x in loc)))
    for x in loc:
        if 0x52EC00<=x<0x52F3E8: continue
        print("    --- context around 0x%08X ---" % x)
        dis_range(x-32,80,"ctx")

print("\n=== generic control-setup region 0x470C80..0x471060 ===")
dis_range(0x470C80,0x3E0,"0x470C80")
