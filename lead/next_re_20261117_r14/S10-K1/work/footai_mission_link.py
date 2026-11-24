#!/usr/bin/env python3
"""S10-K1: v[23] across vtables; scan FootClass::AI for mission dispatch; find callers of mission setters."""
import struct, re
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
def vf(base,slot):
    o=va2off(base); return struct.unpack_from('<I',data,o+4*slot)[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

print("=== v[23] (+0x5C) across vtables ===")
for name,b in {'MissionClass':0x7EDCC0,'RadioClass':0x7F0508,'TechnoClass':0x7F4960,
               'FootClass':0x7E8C94,'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4,
               'BuildingClass':0x7E3EBC}.items():
    print("  %-14s v[23]=0x%08X"%(name,vf(b,23)))

# scan FootClass::AI 0x4DA530 .. +0x1000 for calls/jmps and mark interesting targets
print("\n=== FootClass::AI 0x4DA530: calls to mission funcs / jump table / v[23] ===")
start=0x4DA530; end=0x4DB000
o=va2off(start); code=data[o:va2off(end)]
mission_setters={0x5B2FD0:'SetMission?',0x5B3570:'SetMission2?',0x5B35E0:'QueueMission',0x5B3650:'SetMission3?',0x5B3060:'MissionClass::AI',0x5B3040:'GetCurrentMission'}
for ins in md.disasm(code,start):
    if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
        t=int(ins.op_str,16)
        if t in mission_setters:
            print("  0x%08X: %s 0x%X -> %s"%(ins.address,ins.mnemonic,t,mission_setters[t]))
        if 0x5B3000<=t<=0x5B3FFF:
            print("  0x%08X: %s 0x%X (mission region)"%(ins.address,ins.mnemonic,t))
    # indirect call [reg+off] - list ones with off in mission slot range
    if ins.mnemonic=='call' and 'dword ptr [' in ins.op_str:
        m=re.search(r'\+\s*(0x[0-9a-f]+)',ins.op_str)
        if m:
            off=int(m.group(1),16)
            if off in range(0x204,0x274,4) or off==0x5C:
                print("  0x%08X: call [..+0x%X] (mission slot / AI)"%(ins.address,off))

# all direct callers of mission setters across .text
print("\n=== direct callers of mission setters across .text ===")
for target,label in mission_setters.items():
    needle=struct.pack('<I',target)
    sites=[]
    for n,v,vs,r,rs in secs:
        if n!='.text': continue
        blob=data[r:r+rs]; s=0
        while True:
            i=blob.find(needle,s)
            if i<0: break
            # check preceding byte is E8
            if i>0 and blob[i-1]==0xE8:
                sites.append(v+i-1)
            s=i+1
    print("  %s (0x%X): %d direct callers: %s"%(label,target,len(sites),', '.join('0x%X'%x for x in sites[:20])))
