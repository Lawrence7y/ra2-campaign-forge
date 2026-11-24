#!/usr/bin/env python3
"""S10-K1: dump MissionClass::AI jump table @ 0x5B34E8 (32 entries) and disassemble each target's entry."""
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

TABLE=0x5B34E8
o=va2off(TABLE)
print("=== MissionClass::AI dispatch table @ 0x%08X (32 entries) ==="%TABLE)
targets=[]
for i in range(32):
    val=struct.unpack_from('<I',data,o+4*i)[0]
    targets.append(val)
    print("  [%2d] 0x%08X -> 0x%08X"%(i,TABLE+4*i,val))
# also dump beyond to see where table ends
print("  --- next 4 dwords ---")
for i in range(32,36):
    val=struct.unpack_from('<I',data,o+4*i)[0]
    print("  [%2d] 0x%08X -> 0x%08X"%(i,TABLE+4*i,val))

# disassemble each unique target briefly
print("\n=== unique dispatch targets: first instructions ===")
seen=set()
for i,t in enumerate(targets):
    if t in seen: 
        print("  [%2d] -> 0x%08X (dupe)"%(i,t)); continue
    seen.add(t)
    o2=va2off(t)
    if o2 is None:
        print("  [%2d] -> 0x%08X (NO MAP)"%(i,t)); continue
    code=data[o2:o2+0x40]
    insns=[]
    for ins in md.disasm(code,t):
        insns.append("%s %s"%(ins.mnemonic,ins.op_str))
        if len(insns)>=6: break
    print("  [%2d] 0x%08X: %s"%(i,t,' | '.join(insns)))
