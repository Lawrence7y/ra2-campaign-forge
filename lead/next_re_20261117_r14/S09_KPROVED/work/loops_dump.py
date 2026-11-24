#!/usr/bin/env python3
"""Extract loop-body instruction ranges (back-edge target -> source) from dis_*.txt for ③b④."""
import os,re
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
ENTRIES=['005BDF70','006A5310','006A7780','004ACE70','006ABD30','0063FEA0','004AB9B0']
lr=re.compile(r'^([0-9A-F]{8})\s+([0-9a-f]+)\s+(\S+)\s*(.*)$')
for e in ENTRIES:
    ins=[]
    for ln in open(os.path.join(EV,'dis_%s.txt'%e),encoding='utf-8'):
        m=lr.match(ln.rstrip('\n'))
        if m: ins.append((int(m.group(1),16),m.group(2),m.group(3),m.group(4)))
    idx={a:i for i,(a,_,_,_) in enumerate(ins)}
    loops=[]
    for i,(a,b,mn,op) in enumerate(ins):
        if mn.startswith('j'):
            mm=re.search(r'(0x[0-9a-f]+)',op)
            if mm:
                t=int(mm.group(1),16)
                if t<a and t in idx: loops.append((t,a,mn))
    # dedupe by target
    seen=set(); uniq=[]
    for t,a,mn in loops:
        if (t,a) in seen: continue
        seen.add((t,a)); uniq.append((t,a,mn))
    out=['=== loops %s ==='%e]
    for t,a,mn in uniq:
        i0=idx[t]; i1=idx[a]
        body=ins[i0:i1+1]
        out.append('LOOP target 0x%08X .. backedge @0x%08X (%s) : %d insns'%(t,a,mn,len(body)))
        for aa,bb,mm,oo in body[:22]:
            out.append('  %08X %-18s %-7s %s'%(aa,bb,mm,oo))
        if len(body)>22: out.append('  ... (%d more)'%(len(body)-22))
    open(os.path.join(EV,'loops_%s.txt'%e),'w',encoding='utf-8').write('\n'.join(out)+'\n')
    print(e,'loops',len(uniq))
