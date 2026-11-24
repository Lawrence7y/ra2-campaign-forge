#!/usr/bin/env python3
"""Consolidate 4-ring evidence for the 8 rows into EVIDENCE/ring_8.tsv."""
import os,csv,re
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
E=['004AAE90','005BDF70','006A5310','004AB9B0','0063FEA0','006A7780','004ACE70','006ABD30']
out=['entry\tname\tvt\tslot\trtti_class\tvt_slot_eq\tsites_4\tsite_count\tgrade']
for e in E:
    txt=open(os.path.join(EV,'rtti_%s.txt'%e),encoding='utf-8').read().splitlines()
    d={}
    for ln in txt:
        m=re.match(r'② vt=(0x[0-9A-F]+) slot=(\d+)',ln)
        if m:d['vt']=m.group(1);d['slot']=m.group(2)
        if 'COL)' in ln: d['col']=ln.split('= ')[-1].replace(' (COL)','')
        if 'TD)' in ln: d['td']=ln.split('= ')[-1].replace(' (TD)','')
        if '"' in ln and 'TD+8' in ln: d['name']=ln.split('"')[1]
        if '==entry?' in ln: d['eq']=ln.split('?')[-1].strip()
        if ln.startswith('  site '):
            site=ln.split()[1]
            d.setdefault('sites',[]).append(site)
    cls=d.get('name','')
    if cls.startswith('.?AV') and cls.endswith('@@'):
        cls=cls[4:-2]
    nm='%s::slot%s'%(cls,d.get('slot','?'))
    out.append('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t[已证]'%(e,nm,d['vt'],d['slot'],d.get('name',''),d.get('eq',''),','.join(d.get('sites',[])),len(d.get('sites',[]))))
open(os.path.join(EV,'ring_8.tsv'),'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('\n'.join(out))
