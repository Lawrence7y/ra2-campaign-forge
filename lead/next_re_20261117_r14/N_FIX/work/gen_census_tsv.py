#!/usr/bin/env python3
"""Format existing analysis into NOINIT_CENSUS.tsv; print the few checks needed for the reports."""
import json, os
from collections import defaultdict
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
D=os.path.join(ROOT,'N_FIX','EVIDENCE')
data=json.load(open(os.path.join(D,'census_detailed.json'),encoding='utf-8'))
census=data['census']

# map addr -> (card, name, grade) from coverage_delta
addr2row={}
for n in range(1,11):
    card=f"C{n:02d}"
    for line in open(os.path.join(ROOT,f"{card}_census","coverage_delta.tsv"),encoding='utf-8',errors='replace'):
        p=line.rstrip('\n').split('\t')
        if len(p)<5 or p[0]=='entry': continue
        a=int(p[0],16)
        addr2row.setdefault(a,[]).append((card,p[2],p[4]))

def should_name(c):
    sig=c['sig_text'].strip()
    cls=c['real_cls']
    # clean leading comment / parameter-tail artifacts
    if sig.startswith('//'): sig=sig[2:].strip()
    if sig.startswith(cls+'(') or sig.startswith(cls+' ('):
        return f"{cls}::{sig}" if '::' not in sig.split('(')[0] else sig
    return f"{cls}::{cls}<see {c['file']}:{c['noinit_line']}>"

rows=[]
missing=[]
for c in sorted(census,key=lambda x:(x['addr'],x['file'])):
    a=c['addr']
    hits=addr2row.get(a,[])
    if hits:
        # normally exactly one card owns the address
        card,name,grade=hits[0]
        if len(hits)>1: card='/'.join(h[0] for h in hits)
    else:
        card,name,grade='NONE','(not in any coverage_delta.tsv)','-'
        missing.append((a,c['file'],c['noinit_line'],c['real_cls']))
    rows.append(f"0x{a:08X}\t{card}\t{name}\t{grade}\t{should_name(c)}\t[已证]\t{c['file']}:{c['noinit_line']}")

hdr="addr\tcard\tcurrent_name\tcurrent_grade\tshould_be_name\tshould_be_grade\tevidence_yrpp_line\n"
out=os.path.join(ROOT,'N_FIX','NOINIT_CENSUS.tsv')
open(out,'w',encoding='utf-8').write(hdr+"\n".join(rows)+"\n")
print("wrote",out,"rows",len(rows))
print("\ncensus addrs NOT in any coverage_delta.tsv:")
for a,f,l,cls in missing: print(f"  0x{a:08X} {f}:{l} {cls}")
print("count",len(missing))
# pure stub breakdown
stubs=data['pure_stubs']
print("\npure_stubs count",len(stubs))
for s in stubs:
    print(f"  {s['file']}:{s['line']} cls={s['cls']} | {s['text'][:70]}")
