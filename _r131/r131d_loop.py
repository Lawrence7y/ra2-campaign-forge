#!/usr/bin/env python3
# R131 r131d: disassemble loop body starting at a KNOWN boundary 0x6bc342 (r130: mov esi,0x7f3710)
# and print each instruction with its stack pushes; identify the 3 wrapper args.
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131d_loop.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True
START=0x6bc342
seq=[]
for i in md.disasm(data[START-tlo:START-tlo+0x120], START):
    seq.append(i)
    if i.address>0x6bc420: break
rows=[]
for i in seq:
    rows.append({'va':'%08x'%i.address,'bytes':i.bytes.hex(),'mn':i.mnemonic,'op':i.op_str})
    print('%08x  %-24s %-10s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
json.dump({'start':hex(START),'rows':rows},open(OUT,'w'),indent=1,ensure_ascii=False)
