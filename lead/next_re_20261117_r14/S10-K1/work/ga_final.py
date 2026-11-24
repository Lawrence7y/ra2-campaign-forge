#!/usr/bin/env python3
"""S10-K1: 0x709480 full (guard->attack candidate) and 0x414B70-0x414BA8 (QueueMission(1,0))."""
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for start,ln in [(0x709480,0xD0),(0x414B60,0x50)]:
    print("\n=== 0x%08X ==="%start)
    o=va2off(start)
    for ins in md.disasm(data[o:o+ln],start):
        print("  0x%08X: %-26s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
