#!/usr/bin/env python3
# R131 r131o: which of the 117 table-iteration loops (R130 census) contain a call to ANY
# member of the wrapper template family (0x6bedb0, 0x41c250)? This scopes R130's claim
# "the only feeding loop is 0x6bc34d" -- R130 only looked at calls to 0x6bedb0.
import json, io
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131o_loops_of_family.json'
cen=json.load(io.open('/home/t628/projects/ra2-campaign-forge/_r130/r130b_tables.json',encoding='utf-8'))
fam=input if False else None
CALLERS=[0x416bc2,0x44e02c,0x4db8cc,0x4df85c,0x51b064,0x521fc2,0x5230dc,0x65f092,
         0x6cc999,0x710213,0x7354f2,0x742699,0x742a94,0x6bc364,0x6bc3aa]
R={'family_call_sites':[hex(c) for c in CALLERS],'census_loops':len(cen['hits'])}
feeds=[]
for h in cen['hits']:
    lh=int(h['loop_head'],16); be=int(h['back_edge'],16)
    ins=[c for c in CALLERS if lh<=c<=be]
    if ins:
        feeds.append({'loop_head':h['loop_head'],'back_edge':h['back_edge'],
                      'table_head':h['table_head'],'bound':h['bound'],'step':h['step'],
                      'count':h['count'],'call_sites':[hex(c) for c in ins]})
R['loop_containing_family_call']=feeds
print('family call sites:',len(CALLERS))
print('census loops:',len(cen['hits']))
print('loops containing a family call:',len(feeds))
for f in feeds: print('  ',f)
# control: a call site NOT in the family must fall in 0 loops
ctl=0x6bc315   # call 0x734fe0, right before the loop
R['control_0x6bc315_in_loops']=[f['loop_head'] for f in feeds if int(f['loop_head'],16)<=ctl<=int(f['back_edge'],16)]
print('control call 0x6bc315 in loops:',R['control_0x6bc315_in_loops'])
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
