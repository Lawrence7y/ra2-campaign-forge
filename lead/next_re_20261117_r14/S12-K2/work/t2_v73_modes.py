"""T2 equivalence-form supplement: for every call [reg+0x124] site inside an
atlas function, disassemble from that function entry (aligned) and record
immediate push values 0..3 in the preceding instruction window (mode combos).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, md, fmt_insn, load_atlas, EVID
from collections import Counter
b=Bin(); L=[]
m=md(skipdata=True)
rows,_=load_atlas()
sites=[]; per_fn=0
for r in rows:
    a=r['_va']; n=r['_size']
    if n<=0 or n>0x20000: continue
    try: insns=list(m.disasm(b.read(a,n),a))
    except Exception: continue
    insns=[i for i in insns if i.id!=0]
    local=[]
    for idx,ins in enumerate(insns):
        if ins.mnemonic!='call': continue
        if any(op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0 and op.mem.disp==0x124 for op in ins.operands):
            local.append((idx,ins,a))
    if local: per_fn+=1
    sites.extend(local)
L.append("call [reg+0x124] sites inside atlas functions = %d across %d functions"%(len(sites),per_fn))
mc=Counter(); recs=[]
for idx,ins,fa in sites:
    # align by function-relative instruction index
    insns=[i for i in m.disasm(b.read(fa,(ins.address+16)-fa if ins.address+16>fa else 16),fa) if i.id!=0]
    # rebuild preceding window from function start up to ins.address
    seq=[i for i in m.disasm(b.read(fa,ins.address+8-fa),fa) if i.id!=0]
    pos=None
    for k,x in enumerate(seq):
        if x.address==ins.address: pos=k; break
    win=seq[max(0,(pos or 0)-16):pos or 0]
    pushes=[]
    for w in win:
        if w.mnemonic=='push':
            s=w.op_str.strip().lower()
            try:
                v=int(s,16) if s.startswith('0x') else int(s,10)
            except Exception:
                v=None
            if v in (0,1,2,3): pushes.append((w.address,v))
    key=tuple(sorted(set(v for _,v in pushes)))
    mc[key]+=1
    recs.append((ins.address,fa,pushes))
L.append("preceding-window push-immediate mode-value combinations:")
for k,c in sorted(mc.items(), key=lambda kv:(-kv[1],kv[0])):
    L.append("  values=%s sites=%d"%(str(k),c))
L.append("")
L.append("sites with any mode push (site, function, preceding pushes within 16 aligned insns):")
for a,fa,pushes in recs:
    if pushes:
        L.append("  %08X fn=%08X pushes=%s"%(a,fa," ".join("%08X:%d"%p for p in pushes)))
out=os.path.join(EVID,'t2_v73_mode_combos.txt')
open(out,'w',encoding='utf-8').write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L),"sites",len(sites))
