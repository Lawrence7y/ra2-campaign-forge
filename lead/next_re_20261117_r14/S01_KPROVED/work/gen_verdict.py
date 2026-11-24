# -*- coding: utf-8 -*-
"""Generate per-row four-ring verdict for all 47 unproven S01 rows."""
import json
d=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01_KPROVED\EVIDENCE\scan_main.json"))
sig=d['signals']; direct=d['direct']
# coverage grades/names
rows={}
for line in open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv",encoding='utf8').read().splitlines()[1:]:
    f=line.split('\t')
    if len(f)>=5 and f[1]=='S01': rows[f[0].upper()]={'name':f[2],'grade':f[4]}
# ② channel facts
RTTI={'00554400','00643E80'}  # only S01 entries appearing as .rdata dword (vtable ref)
YRPP={'0069AE90': 'JMP_STD(0x69AE90)+SET_REG32(ECX,0xA8B238) Unsorted.h:43; NO Game-class declared member matched in body'}
out=['entry\tname\tgrade\t①entry\t②channel\t③b\t④direct#\tVERDICT\treason']
for e in sorted(sig):
    r=rows[e]; s=sig[e]; nd=len(direct.get(e,[]))
    ch2='NONE'
    if e in RTTI: ch2='RTTI/vtable(slot0)'
    if e in YRPP: ch2='YRpp(JMP_STD)'
    b3=[]
    if s['jt']>=1: b3.append('jumptbl')
    if s['loops']>=1 and s['cond']>=1: b3.append('loopIO?')
    if s['cond']>=3: b3.append('multi-cond?')
    b3s='+'.join(b3) if b3 else 'no'
    verdict='NO'; reason='② no RTTI & no YRpp binding'
    if e in RTTI:
        verdict='NO'; reason='② RTTI ok BUT ③ thin shell/2-guard handler = ③a, not ③b'
    elif e in YRPP:
        verdict='NO'; reason='② FAILS strict: JMP_STD not CALL/JMP_THIS; body uses only generic YRpp globals (Session/Scenario/Armageddon/ProgressScreen), NO Game-class declared member/offset/constant matched -> single-point, D-42细则3'
    out.append('\t'.join([e,r['name'],r['grade'],'atlas',ch2,b3s,str(nd),verdict,reason]))
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01_KPROVED\EVIDENCE\per_row_verdict.tsv",'w',encoding='utf8').write('\n'.join(out)+'\n')
print('\n'.join(out))
