#!/usr/bin/env python3
"""S10-K1: FootClass::AI tail + search call to TechnoClass::AI (0x6F9E50)."""
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
print("=== FootClass::AI tail 0x4DAE40..0x4DAF10 ===")
o=va2off(0x4DAE40)
for ins in md.disasm(data[o:o+0xD0],0x4DAE40):
    print("  0x%08X: %-24s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))

print("\n=== search direct calls to 0x6F9E50 (TechnoClass::AI) across .text ===")
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    code=data[r:r+rs]
    for ins in md.disasm(code,v):
        if ins.mnemonic=='call' and ins.op_str=='0x6f9e50':
            print("  0x%08X calls TechnoClass::AI"%(ins.address))
