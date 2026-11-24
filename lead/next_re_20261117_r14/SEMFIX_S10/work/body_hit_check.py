# -*- coding: utf-8 -*-
import os, re, json
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10"
EV = os.path.join(CARD,'EVIDENCE')
D = json.load(open(os.path.join(EV,'DISASM_25.json'),encoding='utf-8'))
DEL = open(os.path.join(CARD,'coverage_delta.tsv'),encoding='utf-8').read().split('\n')
def body_vals(e):
    s=set()
    for i in D.get(e,[]):
        s.add(int(i['a'],16))
        for m in re.finditer(r'0x[0-9a-fA-F]+', i['m']+' '+i['o']): s.add(int(m.group(0),16))
        for m in re.finditer(r'\+\s*(\d+)\]', i['o']): s.add(int(m.group(1)))
    return s
tot=hit=0; per=[]
for ln in DEL[1:]:
    if not ln.strip(): continue
    c=ln.split('\t'); e,sem=c[0],c[3]
    toks=set(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)', sem))
    bv=body_vals(e)
    h=sum(1 for t in toks if t in bv)
    tot+=len(toks); hit+=h
    per.append((e,len(toks),h))
print('BODY-HIT (all 25): %d/%d = %.1f%%'%(hit,tot,100*hit/tot))
for e,n,h in per: print('  %s %d/%d'%(e,h,n))
