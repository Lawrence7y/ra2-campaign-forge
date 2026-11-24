#!/usr/bin/env python3
"""Exhaustive survey of all 193 non-proved S13 rows by provability category.
Counts every row; identifies thunks/simple stubs among placeholders. Read-only.
Emits EVIDENCE/exhaustive_survey.tsv + summary to stdout."""
import csv, struct, pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TARGETS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\TARGETS.tsv"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\EVIDENCE\exhaustive_survey.tsv"
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase; DATA=open(EXE,'rb').read()
SECS=[]
for s in pe.sections:
    nm=s.Name.decode('ascii','replace').rstrip('\x00'); lo=IB+s.VirtualAddress
    hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData); rl=s.PointerToRawData; rh=rl+s.SizeOfRawData
    SECS.append((nm,lo,hi,rl,rh))
def off_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi:
            o=rl+(va-lo)
            if o<rh: return o
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

rows=list(csv.DictReader(open(TARGETS,encoding='utf-8',errors='replace'),delimiter='\t'))
B8_NEW={0x4393D0,0x4393E0,0x62AF50,0x62AF60,0x65B3A0,0x65B3C0}
B8_K2={0x46B540,0x46B550,0x46C850,0x46C860,0x75E4F0,0x75E500,0x7730D0,0x7730E0}
BEHAV7={0x46BEE0,0x46C790,0x75CEC0,0x75D3A0,0x75E3B0,0x771C70,0x772080}

def cat(r):
    va=int(r['entry'],16); nm=r['name']
    if va in B8_K2: return 'B8_claimed_K2'
    if va in B8_NEW: return 'B8_NEW_provable'
    if va in BEHAV7: return 'BEHAVIORAL_provable'
    if nm.startswith('sub_'): return 'sub_placeholder'
    if '::sub_' in nm: return 'Class::sub_placeholder'
    import re
    if re.search(r'::slot\d+$',nm): return 'Class::slotN_placeholder'
    if re.search(r'::vslot\d+$',nm): return 'vslotN_placeholder'
    if '::' in nm: return 'Class::named_other'
    return 'other'

from collections import Counter
ct=Counter()
out=[]
for r in rows:
    if r['proved']=='1': continue
    c=cat(r); ct[c]+=1
    va=int(r['entry'],16); sz=int(r['atlas_size'])
    o=off_of(va); code=DATA[o:o+min(sz,24)]
    ins=[]
    for i in md.disasm(code,va):
        ins.append(f'{i.mnemonic} {i.op_str}')
        if len(ins)>=4: break
    # detect pure thunk: first ins jmp
    thunk = 'YES' if ins and ins[0].startswith('jmp ') else ''
    out.append((r['entry'],r['name'],r['grade'],c,thunk,' | '.join(ins)))

with open(OUT,'w',encoding='utf-8',newline='') as fh:
    w=csv.writer(fh,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','name','grade','category','pure_jmp_thunk','first4_insns'])
    for x in out: w.writerow(x)
print('non-proved total:',len(out))
for k,v in ct.items(): print(f'  {k}: {v}')
thunks=[x for x in out if x[4]=='YES']
print('pure-jmp thunks among non-proved:',len(thunks))
for x in thunks[:30]: print('  ',x[0],x[1],'|',x[5])
print('wrote',OUT)
