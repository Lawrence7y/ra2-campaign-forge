#!/usr/bin/env python3
"""S10-K1: correctly find direct callers via capstone (resolve E8 rel32)."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
targets={0x5B2FD0:'SetMission(v124)',0x5B3570:'SetMission2(v123)',0x5B35E0:'QueueMission(v122)',
         0x5B3650:'SetMission3(v125)',0x5B3060:'MissionClass::AI(v23 base)',0x5B3040:'GetCurrentMission(v97)'}
callers={t:[] for t in targets}
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    code=data[r:r+rs]
    for ins in md.disasm(code,v):
        if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
            try: t=int(ins.op_str,16)
            except: continue
            if t in callers: callers[t].append((ins.address,ins.mnemonic))
for t,lbl in targets.items():
    c=callers[t]
    print("%s (0x%X): %d call/jmp sites"%(lbl,t,len(c)))
    for a,m in c[:40]: print("   0x%08X %s"%(a,m))
