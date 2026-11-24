#!/usr/bin/env python3
# W155: independent capstone loop/back-edge count for BulletClass::AI and its 33 Ghidra callees.
import os, pickle, re, sys
CARD=r'D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W155_dispatch'
EVID=os.path.join(CARD,'EVIDENCE')
with open(os.path.join(CARD,'work','maps.pkl'),'rb') as f: M=pickle.load(f)
FI=M['func_insns']; FA=M['func_at']; CAL=M['callees']

def back_edges(e):
    be=[]
    for va,sz,mnem,op,h in FI.get(e,[]):
        if not (mnem.startswith('j') or mnem.startswith('loop')): continue
        m=re.fullmatch(r'(0x[0-9a-f]+)',op.strip())
        if m:
            t=int(m.group(1),16)
            if t<=va: be.append((va,t,mnem))
    return be

def dump(e,label,out):
    be=back_edges(e)
    out.write('%s 0x%08X size=%d n=%d back_edges=%d %s\n'%(label,e,FA[e][1] if e in FA else -1,len(FI.get(e,[])),len(be),
        ' '.join('0x%X->0x%X(%s)'%x for x in be)))
    return len(be)

with open(os.path.join(EVID,'bullet_loops_capstone.txt'),'w',encoding='utf-8') as out:
    out.write('=== capstone linear-disasm back-edge analysis (byte channel) ===\n')
    n=dump(0x4666E0,'BulletClass::AI',out)
    out.write('\n=== 33 direct callees reported by Ghidra ===\n')
    cal=sorted(CAL.get(0x4666E0,[]))
    out.write('callee_count_field=%d\n'%len(cal))
    for c in cal:
        dump(c,'callee',out)
    out.write('\ntotal_callees=%d\n'%len(cal))
print('done')
