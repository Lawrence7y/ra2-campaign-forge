# -*- coding: utf-8 -*-
import json,sys,re
sys.stdout.reconfigure(encoding='utf-8')
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
d=json.load(open(BASE+r'\S13_K8\EVIDENCE\analysis_full.json',encoding='utf-8'))
rs=d['results']
AUDIT18=set('0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split())
def demangle(cn):
    if not cn: return '?'
    s=cn
    for p in ('.?AV','.?AU'): 
        if s.startswith(p): s=s[4:];break
    m=re.match(r'\?\$(\w+)@PA[UV](\w+)@@@@',s)
    if m: return m.group(1)+'<'+m.group(2)+'*>'
    if s.endswith('@@'): return s[:-2]
    return s
hdr='entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t缺环说明'
lines=[hdr]
for r in rs:
    ea=r['ea']
    ev='EVIDENCE/analysis_full.json;EVIDENCE/bodies_audit18.txt;EVIDENCE/entry_vt_slots.tsv'
    if r['grade']=='[已证]' and ea in AUDIT18:
        cl=demangle(r['cnames'][0]) if r['cnames'] else '?'
        nm=cl+'::scalar_deleting_dtor'
        sem='scalar deleting dtor: re-install vptr + release registry/array + conditional operator delete + ret 4'
        nk='behavioral'
        miss='四环齐全:①vftable槽值 ②RTTI类属 ③体内vptr写+delete+ret4 ④ctor装v表(imm32引用)'
    else:
        nm=r['name']; sem='[静态推断] 占位名(slot/vslot/sub),缺具名语义'; nk='placeholder'
        if r['grade']=='[未证]': sem='[未证] 非虚表槽/无RTTI类属/无具名语义'
        mm=[]
        if not r['r1']:mm.append('①入口')
        if not r['r2']:mm.append('②类属')
        if not r['r3']:mm.append('③语义')
        if not r['r4']:mm.append('④见证')
        miss='缺'+'+'.join(mm) if mm else '三环齐全但③仅为占位名(不升具名)'
    lines.append('\t'.join([ea,'S13',nm,sem,r['grade'],ev,nk,miss]))
open(BASE+r'\S13_K8\coverage_delta.tsv','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('delta rows',len(lines)-1,'cols',len(lines[1].split(chr(9))))
for r in rs:
    if r['ea'] in AUDIT18:
        print(r['ea'],demangle(r['cnames'][0]))
