#!/usr/bin/env python3
# R131 r131a: disassemble the wrapper 0x6bedb0 fully, and trace where ecx / edx come
# from at the two indirect calls (0x6bee05 call [ecx], 0x6bee10 call [edx+8]).
# Single-target detail=True only (never whole .text).
import json, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131a_wrapper.json'

pe=pefile.PE(EXE, fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+s.SizeOfRawData, s)
lo,hi,s=secs['.text']
data=s.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)
md.detail=True   # ONLY used on bounded <=0x400 byte windows, never on all of .text

def off(va): return va-lo
def insns(va, n, maxbytes=0x400):
    start=off(va); blob=data[start:start+maxbytes]
    out=[]
    for i in md.disasm(blob, va):   # bounded window, detail=True
        out.append({'va':i.address,'size':i.size,'mn':i.mnemonic,'op':i.op_str,
                    'bytes':i.bytes.hex(),
                    'groups':[md.group_name(g) for g in i.groups],
                    'ops':[{'type':str(o.type),'reg':i.reg_name(o.reg) if o.type==1 else None,
                            'imm':o.imm if o.type==2 else None,
                            'mem_base':i.reg_name(o.mem.base) if o.type==3 else None,
                            'mem_disp':o.mem.disp if o.type==3 else None}
                           for o in i.operands]})
        if len(out)>=n: break
    return out

res={}
body=insns(0x6bedb0, 64)
res['wrapper']=body
res['text_range']=[hex(lo),hex(hi),len(data)]

# Where do ecx and edx get their values inside the wrapper? (all writes, in order)
def writes(reg, seq):
    hits=[]
    for k,i in enumerate(seq):
        mn=i['mn']
        ops=i['ops']
        if mn in ('mov','lea','xor','add','sub','pop') and ops:
            d=ops[0]
            if d['type']==1 and d['reg']==reg:
                hits.append({'k':k,'va':hex(i['va']),'mn':mn,'op':i['op'],'bytes':i['bytes']})
        if mn in ('call','jmp') and ops and ops[0]['type']==1:
            hits.append({'k':k,'va':hex(i['va']),'mn':mn,'op':i['op'],'bytes':i['bytes'],'note':'zeroes/'+mn})
    return hits
res['ecx_writes']=writes('ecx',body)
res['edx_writes']=writes('edx',body)
res['eax_writes']=writes('eax',body)

# imports: resolve IAT slots used in the body
pe2=pefile.PE(EXE)
imp={}
for e in getattr(pe2,'DIRECTORY_ENTRY_IMPORT',[]):
    for i in e.imports:
        if i.address: imp[i.address]= (e.dll.decode(), i.name.decode() if i.name else ('#%s'%i.ordinal))
res['iat_used']={}
for i in body:
    for o in i['ops']:
        if o['type']==3 and o['mem_base'] is None and o['mem_disp']:
            va=o['mem_disp']
            res['iat_used'][hex(va)]={'insn':hex(i['va']),'mn':i['mn'],'op':i['op'],
                                      'resolved':imp.get(va)}
json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
for i in body:
    print('%08x  %-24s %-22s %s'%(i['va'],i['bytes'],i['mn'],i['op']))
print('--- ecx writes ---'); [print(x) for x in res['ecx_writes']]
print('--- edx writes ---'); [print(x) for x in res['edx_writes']]
print('--- iat used ---'); [print(k,v) for k,v in res['iat_used'].items()]
