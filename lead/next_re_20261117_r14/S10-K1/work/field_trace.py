#!/usr/bin/env python3
"""S10-K1: (a) 0x709290 full + 0x70944f; (b) all mission-field writers 0xAC/0xB0/0xB4/0xB8/0xBC/0xC0/0xC4 in 0x5B2xxx-0x5B3Axx."""
import pefile, re
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
print("=== 0x70944f region (called when mission==2/Move in 0x709290) ===")
o=va2off(0x709440)
for ins in md.disasm(data[o:o+0x60],0x709440):
    print("  0x%08X: %-26s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))

print("\n=== 0x7091d0 (called by 0x709290) ===")
o=va2off(0x7091d0)
for ins in md.disasm(data[o:o+0x100],0x7091d0):
    print("  0x%08X: %-26s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    if ins.mnemonic.startswith('ret') and ins.address>0x709200: break

print("\n=== mission field accesses in 0x5B2E00..0x5B3B00 ===")
o=va2off(0x5B2E00)
for ins in md.disasm(data[o:va2off(0x5B3B00)],0x5B2E00):
    m=re.search(r'\[\s*\w+\s*\+\s*(0x[0-9a-f]+)\s*\]',ins.op_str)
    if m:
        off=int(m.group(1),16)
        if off in (0xAC,0xB0,0xB4,0xB8,0xBC,0xC0,0xC4,0xC8,0xD0,0x6C,0x90):
            print("  0x%08X: %-8s %s   [field 0x%X]"%(ins.address,ins.mnemonic,ins.op_str,off))
