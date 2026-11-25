#!/usr/bin/env python3
# R131 r131c: the call site of wrapper 0x6bedb0 inside loop 0x6bc34d -- push bytes,
# ecx (this) provenance, and stack-arg identity (rclsid must equal table+0 = 0x7e9500).
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131c_site.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)
R={}

def dis(va, nbytes):
    o=va-tlo; out=[]
    for i in md.disasm(data[o:o+nbytes], va):
        out.append(i)
    return out

# whole loop region, linear walk, list with bytes
seq=dis(0x6bc30a, 0x120)
R['loop_region']=[{'va':'%08x'%i.address,'bytes':i.bytes.hex(),'mn':i.mnemonic,'op':i.op_str} for i in seq]
for x in R['loop_region']:
    print('%-10s %-22s %-9s %s'%(x['va'],x['bytes'],x['mn'],x['op']))

# direct call targets (E8 rel32) inside region -> confirm 0x6bedb0 reached directly
def call_targets(va0, va1):
    out=[]
    va=va0
    while va<va1:
        i=next(md.disasm(data[va-tlo:va-tlo+16], va), None)
        if i is None: va+=1; continue
        if i.mnemonic=='call' and i.bytes[0]==0xe8:
            rel=struct.unpack('<i', i.bytes[1:5])[0]
            out.append({'at':'%08x'%va,'target':'%08x'%(va+5+rel)})
        va+=i.size
    return out
R['calls_in_region']=call_targets(0x6bc30a,0x6bc42a)
print('CALLS:',R['calls_in_region'])
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
