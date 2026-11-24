#!/usr/bin/env python3
"""S10-K1: disasm 0x709290 (post-mission auto-acquire?) and 0x6FA690..0x6FA700; find callers of 0x709290."""
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
print("=== 0x709290 (function head) ===")
o=va2off(0x709290)
for ins in md.disasm(data[o:o+0x180],0x709290):
    print("  0x%08X: %-26s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    if ins.mnemonic.startswith('ret') and ins.address>0x7092C0: break

print("\n=== callers of 0x709290 ===")
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    code=data[r:r+rs]
    for ins in md.disasm(code,v):
        if ins.mnemonic=='call' and ins.op_str=='0x709290':
            print("  0x%08X"%(ins.address))
