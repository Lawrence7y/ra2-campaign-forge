#!/usr/bin/env python3
"""S10-K1: find code xrefs to mission-name pointer table 0x816CAC and dump MissionClass vtable."""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    for n,v,vs,r,rs in secs:
        if v<=va<v+max(vs,rs): return r+(va-v)
    return None
def off2va(o):
    for n,v,vs,r,rs in secs:
        if r<=o<r+rs: return v+(o-r)
    return None

# 1) find all 4-byte LE occurrences of 0x00816CAC (table base) in the whole file
targets=[0x816CAC,0x816CB0,0x816CAC]
print("=== raw 4-byte occurrences of 0x00816CAC ===")
needle=struct.pack('<I',0x816CAC)
start=0
while True:
    i=data.find(needle,start)
    if i<0: break
    print("  @ file 0x%X (VA 0x%08X)"%(i,off2va(i) or 0))
    start=i+1

# 2) search .text for instructions referencing 0x816CAC via capstone (immediate or disp)
print("\n=== capstone: instructions containing imm/disp 0x816CAC in .text ===")
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    code=data[r:r+rs]
    for ins in md.disasm(code, v):
        opstr=ins.op_str
        if '816cac' in opstr.lower() or '0x816cac' in opstr.lower():
            print("  0x%08X: %-30s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+opstr))

# 3) Dump MissionClass vtable 0x7EDCC0
print("\n=== MissionClass vtable @ 0x7EDCC0 (first 130 slots) ===")
for baseva in [0x7EDCC0]:
    o=va2off(baseva)
    for i in range(130):
        val=struct.unpack_from('<I',data,o+4*i)[0]
        print("  v[%3d] (+0x%03X) = 0x%08X"%(i,4*i,val))
