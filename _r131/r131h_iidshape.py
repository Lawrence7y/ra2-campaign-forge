#!/usr/bin/env python3
# R131 r131h: canonical QueryInterface call shape in this binary. Dump instruction windows
# around every imm32 reference of IID_IUnknown (0x817bc0) and print the push/call shape.
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131h_iidshape.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)
SITES=[0x413dd9,0x41c272,0x437f59,0x517b6c,0x67d0d1,0x67e5b5,0x6bedd2,0x6bedfe,0x6bee20]
def win(va, back=0x24, fwd=0x2a):
    a=va-back; out=[]
    for i in md.disasm(data[a-tlo:a-tlo+back+fwd], a):
        out.append('%08x %-18s %-9s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    return out
R={}
for s in SITES:
    w=win(s); R['%08x'%s]=w
    print('=== IID ref site 0x%08x ==='%s)
    for l in w: print('   '+l)
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
