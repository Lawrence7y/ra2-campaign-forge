#!/usr/bin/env python3
# R129 auditor: single unchunked disasm_lite pass over .text (skipdata=True),
# counting every 'mov dword ptr [abs], imm32'. Streaming tuples only, no detail.
import re, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
IB=0x400000
pe=pefile.PE(EXE,fast_load=False)
print('sha256',hashlib.sha256(open(EXE,'rb').read()).hexdigest())
s=[x for x in pe.sections if x.Name.rstrip(b'\0')==b'.text'][0]
data=bytes(pe.__data__[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData])
base=IB+s.VirtualAddress
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
pat=re.compile(r'^mov dword ptr \[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$')
n=0; nins=0; hits=[]
for a,sz,m,op in md.disasm_lite(data,base):
    nins+=1
    if m=='mov':
        mm=pat.match(m+' '+op)
        if mm:
            hits.append((a,int(mm.group(1),16),int(mm.group(2),16),data[a-base:a-base+sz].hex()))
print('decoded instructions:',nins)
print('mov dword ptr [abs],imm32 sites:',len(hits))
DATA_LO,DATA_HI=0x812000,0xb79be4
RD_LO,RD_HI=0x7e1000,0x812000
print('  target in .data proper:',sum(1 for a,t,i,b in hits if DATA_LO<=t<DATA_HI))
print('  imm in .rdata range:',sum(1 for a,t,i,b in hits if RD_LO<=i<RD_HI))
print('  target==0xa8e8c8:',[(hex(a),hex(i)) for a,t,i,b in hits if t==0xa8e8c8])
import json
json.dump(hits,open('/tmp/r129_movabs_full.json','w'))
