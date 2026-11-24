#!/usr/bin/env python3
"""S10-K1: disasm around key mission call sites 0x6FA655, 0x41BA34, 0x41BAD9, 0x41B880, 0x7013C1."""
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
for site in [0x6FA655,0x41BA34,0x41BAD9,0x41B880,0x7013C1]:
    lo=site-0x60; o=va2off(lo)
    print("\n=== context @ call site 0x%08X ==="%site)
    for ins in md.disasm(data[o:o+0xC0],lo):
        flag=' <== CALL SITE' if ins.address==site else ''
        print("  0x%08X: %-24s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,flag))
