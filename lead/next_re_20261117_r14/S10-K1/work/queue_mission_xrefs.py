#!/usr/bin/env python3
"""S10-K1: find all indirect calls to mission setter slots (0x1E8 etc)."""
import pefile, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
want={0x1E8:'QueueMission_v122',0x1EC:'SetM_v123',0x1F0:'SetM_v124',0x1F4:'SetM_v125'}
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    insns=list(md.disasm(data[r:r+rs],v))
    for idx,ins in enumerate(insns):
        if ins.mnemonic=='call' and 'dword ptr [' in ins.op_str:
            m=re.search(r'\+\s*(0x[0-9a-f]+)',ins.op_str)
            if m and int(m.group(1),16) in want:
                off=int(m.group(1),16)
                print("\n=== %s (+0x%X) @ 0x%08X ==="%(want[off],off,ins.address))
                for j in range(max(0,idx-10),min(len(insns),idx+2)):
                    x=insns[j]
                    print("  0x%08X: %-22s %s %s%s"%(x.address,x.bytes.hex(),x.mnemonic,x.op_str,' <==CALL' if j==idx else ''))
