"""W163 Q2/Q3:
(A) which callers of 0x6D2790 (dirty Add) are in Bullet-AI depth<=8 closure? dual channel.
(B) nested-loop / global-Count scanning detector over all functions in the closure:
    for each function: backedges; for each loop, list global [0xADDR] Count-like reads
    inside; flag functions with >=2 backedges whose loops read different globals.
(C) resolve vtables of 0x421EA0 (PTR_FUN_007e33xx) to identify the class.
"""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

ROOT=0x4666E0
ADD=0x6D2790
DEPTH=8
JCC={"jmp","je","jne","jz","jnz","ja","jae","jb","jbe","jg","jge","jl","jle",
     "jc","jnc","jo","jno","js","jns","jp","jnp","loop","loope","loopne"}

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
    byA,_=w.load_calledges()
    calls,jmps,sweep=w.sweep_full_text(b)
    def caller_of(site):
        i=bisect.bisect_right(entries,site)-1
        return entries[i] if i>=0 else None
    byB=collections.defaultdict(set)
    for tgt,sts in calls.items():
        for s in sts:
            c=caller_of(s)
            if c is not None: byB[c].add(tgt)
    byB=dict(byB)

    add_callers_A={c for c,cs in byA.items() if ADD in cs}
    add_callers_B={c for c,cs in byB.items() if ADD in cs}
    print("ADD_CALLERS_A n=%d"%len(add_callers_A),[hex(x) for x in sorted(add_callers_A)])
    print("ADD_CALLERS_B n=%d"%len(add_callers_B),[hex(x) for x in sorted(add_callers_B)])

    def closure(graph):
        seen={ROOT}; fr={ROOT}
        for d in range(DEPTH):
            nx=set()
            for f in fr:
                for c in graph.get(f,()):
                    if c not in seen: seen.add(c); nx.add(c)
            fr=nx
        return seen
    clA=closure(byA); clB=closure(byB)
    print("CLOSURE_A n=%d CLOSURE_B n=%d"%(len(clA),len(clB)))
    interA=sorted(add_callers_A & clA); interB=sorted(add_callers_B & clB)
    print("ADD_CALLERS∩CLOSURE_A n=%d %s"%(len(interA),[hex(x) for x in interA]))
    print("ADD_CALLERS∩CLOSURE_B n=%d %s"%(len(interB),[hex(x) for x in interB]))
    print("ADD_CALLERS∩CLOSURE_union %s"%[hex(x) for x in sorted((add_callers_A|add_callers_B)&(clA|clB))])

    # (B) nested-loop / global-count detector on union closure (functions with atlas size)
    m=w.md32(skipdata=True)
    suspects=[]
    for f in sorted(clA|clB):
        rec=atlas.get(f)
        if rec is None: continue
        sz=int(rec["size"],10)
        if sz<=0 or sz>0x20000: continue
        try: data=b.read(f,sz)
        except: continue
        insns=[i for i in m.disasm(data,f) if i.id!=0]
        backs=[]
        for i in insns:
            if i.mnemonic in JCC:
                for op in i.operands:
                    if op.type==capstone.x86.X86_OP_IMM and op.imm<=i.address:
                        backs.append((i.address,op.imm))
        if len(backs)<2: continue  # need nested (>=2 backedges) to be a candidate
        # global absolute-mem reads within the function, count distinct addresses
        gl=collections.Counter()
        for i in insns:
            for op in i.operands:
                if op.type==capstone.x86.X86_OP_MEM:
                    mem=op.mem
                    if mem.base==0 and mem.index==0:
                        d=mem.disp&0xFFFFFFFF
                        if d>=0x800000: gl[d]+=1
        suspects.append((f,sz,len(insns),len(backs),backs[:12],[(hex(a),n) for a,n in gl.most_common(10)]))
    print("=== functions in closure with >=2 backedges: n=%d ==="%len(suspects))
    for f,sz,ni,nb,backs,gl in suspects:
        print("  %08X size=%d insn=%d backedges=%d :: %s"%(f,sz,ni,nb,[(hex(a),hex(t)) for a,t in backs]))
        print("     globals:",gl)

    # (C) vtables of 0x421EA0
    print("=== 0x421EA0 vtable pointers ===")
    for vt in (0x7E3328,0x7E3330,0x7E3338,0x7E3354):
        print("  vt %08X:"%vt)
        for va in range(vt, vt+0x10,4):
            v=b.u32(va); s=b.sec_of(v)
            print("    %08X=%08X%s"%(va,v," ->"+s["name"] if s else ""))

    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","EVIDENCE","q23_addcallers_loops.json")
    with open(out,"w",encoding="utf-8") as fo:
        json.dump(dict(add_callers_A=sorted(add_callers_A),add_callers_B=sorted(add_callers_B),
                       interA=interA,interB=interB,closureA=sorted(clA),closureB=sorted(clB),
                       suspects=suspects),fo,indent=1)

if __name__=="__main__": main()
