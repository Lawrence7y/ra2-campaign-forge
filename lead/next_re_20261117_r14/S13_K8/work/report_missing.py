# -*- coding: utf-8 -*-
import json,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\EVIDENCE\analysis_full.json',encoding='utf-8'))
rs=d['results']
print('counts',d['counts'])
print('baseline',d['baseline'])
print()
print('=== [未证] rows (which rings missing) ===')
miss=collections.Counter()
for r in rs:
    if r['grade']=='[未证]':
        mm=''.join([k for k,v in [('1',r['r1']),('2',r['r2']),('3',r['r3']),('4',r['r4'])] if not v])
        miss[mm]+=1
        print(r['ea'],r['name'][:34],'missing',mm,'old',r['oldgrade'])
print('missing pattern counts',dict(miss))
print()
print('=== [静态推断] missing-ring patterns ===')
c=collections.Counter()
for r in rs:
    if r['grade']=='[静态推断]':
        mm=''.join([k for k,v in [('1',r['r1']),('2',r['r2']),('3',r['r3']),('4',r['r4'])] if not v])
        c[mm]+=1
print(dict(c))
