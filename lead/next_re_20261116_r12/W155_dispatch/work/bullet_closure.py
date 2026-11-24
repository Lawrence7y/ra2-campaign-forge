#!/usr/bin/env python3
# W155: BFS depth-4 closure of BulletClass::AI, check for any array Count references.
import os,pickle,collections
CARD=r'D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W155_dispatch'
with open(os.path.join(CARD,'work','maps.pkl'),'rb') as f:M=pickle.load(f)
CAL=M['callees']; FI=M['func_insns']; CA=M['count_addrs']
start=0x4666E0
seen={start:0}; q=collections.deque([start])
while q:
    u=q.popleft(); d=seen[u]
    if d>=4: continue
    for v in CAL.get(u,[]):
        if v not in seen:
            seen[v]=d+1; q.append(v)
hits=[]
for f,d in sorted(seen.items(),key=lambda x:(x[1],x[0])):
    globals_=set()
    for va,sz,mnem,op,h in FI.get(f,[]):
        import re
        for x in re.findall(r'0x([0-9a-f]{6,8})',op):
            v=int(x,16)
            if v in CA: globals_.add(v)
    if globals_: hits.append((f,d,sorted(globals_)))
with open(os.path.join(CARD,'EVIDENCE','bullet_closure_counts.txt'),'w',encoding='utf-8') as out:
    out.write('BFS closure from 0x4666E0 depth<=4: %d functions\n'%len(seen))
    out.write('functions referencing any known array Count: %d\n'%len(hits))
    for f,d,g in hits:
        out.write('0x%08X depth=%d counts=%s\n'%(f,d,','.join('0x%X'%x for x in g)))
print('closure=%d count-refs=%d'%(len(seen),len(hits)))
