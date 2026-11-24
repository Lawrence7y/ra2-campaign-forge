#!/usr/bin/env python3
"""Correlate census addresses with each card's coverage_delta.tsv."""
import json, os
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
D = os.path.join(ROOT,'N_FIX','EVIDENCE')
data = json.load(open(os.path.join(D,'census_detailed.json'),encoding='utf-8'))
census = data['census']
census_addr = defaultdict(list)
for c in census:
    census_addr[c['addr']].append(c)
uaddr = set(census_addr)

percard = {}
for n in range(1,11):
    card = f"C{n:02d}"
    p = os.path.join(ROOT,f"{card}_census","coverage_delta.tsv")
    rows = []
    with open(p,encoding='utf-8',errors='replace') as fh:
        for line in fh:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 5 or parts[0]=='entry': continue
            rows.append({'addr_s':parts[0],'sub':parts[1],'name':parts[2],'reason':parts[3],'grade':parts[4],
                         'raw':line.rstrip('\n')})
    noinit_rows = [r for r in rows if 'noinit_t' in r['name']]
    at_census = [r for r in rows if int(r['addr_s'],16) in uaddr]
    mis = []
    for r in noinit_rows:
        a = int(r['addr_s'],16)
        if a in uaddr:
            mis.append((r, census_addr[a]))
    percard[card] = {'rows':len(rows),'noinit_rows':noinit_rows,'at_census':at_census,'mis':mis}
    print(f"\n===== {card} : rows={len(rows)} noinit_rows={len(noinit_rows)} rows@census={len(at_census)} MIS={len(mis)} =====")
    for r,cs in mis:
        should = ' || '.join(f"{c['real_cls']} | sig={c['sig_text'][:45]}" for c in cs)
        print(f"  {r['addr_s']} | {r['name']:<36} | {r['grade']:<10} | sub={r['sub']} | {should}")

json.dump({k:{
    'rows':v['rows'],
    'mis':[{'addr':r['addr_s'],'name':r['name'],'grade':r['grade'],'sub':r['sub'],'reason':r['reason'],
            'should':[{'real_cls':c['real_cls'],'sig':c['sig_text'],'file':c['file'],'line':c['noinit_line'],
                       'misjudged':c['misjudged_name']} for c in cs]}
           for r,cs in v['mis']],
    'noinit_rows_all':[{'addr':r['addr_s'],'name':r['name'],'grade':r['grade']} for r in v['noinit_rows']]
 } for k,v in percard.items()}, open(os.path.join(D,'percard_correlation.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("\nwrote percard_correlation.json")
