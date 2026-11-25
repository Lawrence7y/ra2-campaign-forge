#!/usr/bin/env python3
# R131 r131n: does ANY caller of family instantiation 0x41c250 sit inside a table-walking
# loop (mov head / add step / cmp bound / jl back-edge)? If yes, is there a SECOND
# (CLSID, dll) fixup table besides 0x7f3710?
import json, struct, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131n_feed.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)
IMM=re.compile(r'^(0[xX][0-9a-fA-F]+|\d+)$')
def imm(s):
    s=s.strip()
    return int(s,16) if s[:2].lower()=='0x' else (int(s,10) if IMM.match(s) else None)
CALLERS_41C=[0x416bc2,0x44e02c,0x4db8cc,0x4df85c,0x51b064,0x521fc2,0x5230dc,0x65f092,0x6cc999,0x710213,0x7354f2,0x742699,0x742a94]
CALLERS_6BE=[0x6bc364,0x6bc3aa]
FAM=CALLERS_41C+CALLERS_6BE
# For each caller, walk backwards up to 0x400 bytes and look for the loop idiom:
#   mov reg, imm       (table head, imm in a data section)
#   add reg, imm       (step)
#   cmp reg, imm       (bound)
#   jcc/jl back
def section_of(va):
    for nm,(lo,hi,s) in secs.items():
        if lo<=va<hi: return nm
    return None
R={'callers':{}}
for c in FAM:
    a=max(tlo, c-0x400)
    win=[]
    for i in md.disasm(data[a-tlo:a-tlo+(c-a)+8], a):
        win.append(i)
    head=step=bound=back=None
    for i in win:
        mn,ops=i.mnemonic,i.op_str
        if mn=='mov' and ',' in ops:
            d,s_=ops.split(',',1)
            v=imm(s_)
            if v and section_of(v) in ('.rdata','.data') and 'ptr' not in d:
                head=(i.address,d.strip(),v)
        if mn=='add' and ops.startswith('e') and ',' in ops:
            v=imm(ops.split(',')[1])
            if v in (4,8,0xc,0x10,0x70,0x2c,0x40): step=(i.address,ops,v)
        if mn in ('cmp','add') and ops.startswith('e') and ',' in ops:
            v=imm(ops.split(',')[1])
            if v and section_of(v) in ('.rdata','.data'): bound=(i.address,ops,v)
        if mn=='jl' and i.op_str:
            back=(i.address,i.op_str)
    R['callers'][hex(c)]={'head':head and [hex(head[0]),head[1],hex(head[2])],
                          'step':step and [hex(step[0]),step[1],step[2]],
                          'bound':bound and [hex(bound[0]),bound[1],hex(bound[2])],
                          'back':back and [hex(back[0]),back[1]]}
    print(hex(c),R['callers'][hex(c)])
# Summary: which callers look like they are in a table loop, and with what head
loops={}
for c,v in R['callers'].items():
    if v['head'] and v['step'] and v['bound'] and v['back']:
        loops.setdefault(v['head'][2],[]).append(c)
R['loop_heads']={k:v for k,v in loops.items()}
print('loop heads found around family callers:',json.dumps(loops,indent=1))
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
