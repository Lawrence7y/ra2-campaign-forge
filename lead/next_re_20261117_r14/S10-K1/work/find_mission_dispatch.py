#!/usr/bin/env python3
"""S10-K1: find indirect jump tables and disassemble MissionClass method region."""
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

print("=== 'jmp dword ptr [reg*4+disp32]' sites (FF 24 8x) in .text ===")
for n,v,vs,r,rs in secs:
    if n!='.text': continue
    code=data[r:r+rs]
    for i in range(len(code)-7):
        if code[i]==0xFF and code[i+1]==0x24 and 0x80<=code[i+2]<=0x87:
            va=v+i
            for ins in md.disasm(code[i:i+8], va):
                print("  0x%08X: %s  %s %s"%(va,ins.bytes.hex(),ins.mnemonic,ins.op_str))
                break

funcs=[0x5B2E10,0x5B2FD0,0x5B3040,0x5B3060,0x5B3570,0x5B35E0,0x5B3650,0x5B36B0,0x5B3740,0x5B3910,0x5B3940,0x5B3A10,0x5B3A50,0x5B3A60]
for fva in funcs:
    o=va2off(fva)
    print("\n=== disasm @ 0x%08X ==="%fva)
    code=data[o:o+0x120]
    cnt=0
    for ins in md.disasm(code,fva):
        print("  0x%08X: %-26s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        cnt+=1
        if ins.mnemonic=='ret' or cnt>=45: break
