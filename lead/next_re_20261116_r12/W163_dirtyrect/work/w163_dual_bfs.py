"""W163: dual-channel callers + depth-8 BFS from BulletClass::AI + G_INGAME scan.

Channel A: Ghidra calledges.raw.log (caller->callees).
Channel B: full .text byte sweep skipdata=True, call site -> target, caller mapped by
           nearest preceding atlas ENTRY only (not size), so atlas-boundary orphans
           still get their target from raw bytes.

Targets of interest:
  dirty cluster: 6D2790(Add), 6D3D10(flush/render), 6D1810(ctor), 6D2B60, ...
  expensive subsystems: detect by callee names from a curated set + report all
                        backedges in reachable functions.
  G_INGAME: 0xA8E9A0 absolute refs.
"""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

ROOT = 0x4666E0
DEPTH = 8
DIRTY = {0x6D1810,0x6D2790,0x6D2B60,0x6D2DE0,0x6D3040,0x6D3290,0x6D3470,
         0x6D3660,0x6D3870,0x6D3AC0,0x6D3D10,0x6DA980,0x6D8DB0}

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
    by_caller_A, edges = w.load_calledges()
    calls, jmps, sweep = w.sweep_full_text(b)
    def caller_of(site):
        i=bisect.bisect_right(entries,site)-1
        return entries[i] if i>=0 else None
    by_caller_B=collections.defaultdict(set)
    for tgt, sites in calls.items():
        for s in sites:
            c=caller_of(s)
            if c is not None: by_caller_B[c].add(tgt)
    by_caller_B=dict(by_caller_B)

    print("SWEEP", json.dumps(sweep))

    # --- callers of dirty-cluster fns, dual channel ---
    print("=== CALLERS of dirty-cluster functions ===")
    callers_report={}
    for t in sorted(DIRTY):
        ca=sorted({c for c,cs in by_caller_A.items() if t in cs})
        la=[(c,s) for (c,cal,s) in edges if cal==t]
        cb=sorted({c for c,cs in by_caller_B.items() if t in cs})
        lb=[(c,s) for tgt,sts in calls.items() if tgt==t for s in sts for c in [caller_of(s)]]
        print("TARGET %08X | Ghidra callers n=%d %s"%(t,len(ca),[hex(x) for x in ca[:20]]))
        print("           | Ghidra sites n=%d %s"%(len(la),[(hex(c),hex(s)) for c,s in la[:20]]))
        print("           | Byte   callers n=%d %s"%(len(cb),[hex(x) for x in cb[:20]]))
        print("           | Byte   sites    n=%d %s"%(len(lb),[(hex(c),hex(s)) for c,s in lb[:20]]))
        callers_report["%08X"%t]=dict(ghidra_callers=ca,ghidra_sites=la,byte_callers=cb,byte_sites=lb)

    # --- depth-8 BFS both channels ---
    def bfs(graph):
        seen={ROOT}; frontier={ROOT}; reach=[]
        for d in range(1,DEPTH+1):
            nxt=set()
            for f in frontier:
                for c in graph.get(f,()):
                    if c not in seen:
                        seen.add(c); nxt.add(c)
            frontier=nxt; reach.append((d,sorted(nxt)))
        return seen, reach
    print("=== BFS depth<=%d from %08X ==="%(DEPTH,ROOT))
    bfsrep={}
    for name,graph in (("A_ghidra",by_caller_A),("B_byte",by_caller_B)):
        seen,reach=bfs(graph)
        hit=sorted(seen & DIRTY)
        print("CHANNEL",name,"total_reached",len(seen))
        for d,nxt in reach:
            print("  depth %d: n=%d"%(d,len(nxt)))
        print("  DIRTY_CLUSTER hit:",[hex(x) for x in hit])
        bfsrep[name]=dict(total=len(seen),dirty_hit=hit,
                          layers=[(d,nxt) for d,nxt in reach],all=sorted(seen))

    # --- G_INGAME 0xA8E9A0 and frame 0xA8ED84 abs refs ---
    print("=== absolute refs to 0xA8E9A0 / 0xA8ED84 / 0xA8B238 ===")
    m=w.md32(skipdata=True); data=b.section_bytes(".text")
    gref=collections.defaultdict(list)
    for insn in m.disasm(data,b.text["va"]):
        if insn.id==0: continue
        for op in insn.operands:
            if op.type==capstone.x86.X86_OP_MEM:
                mem=op.mem
                if mem.base==0 and mem.index==0:
                    d=mem.disp&0xFFFFFFFF
                    if d in (0xA8E9A0,0xA8ED84,0xA8B238):
                        c=caller_of(insn.address)
                        gref[d].append(dict(va=insn.address,fn=c,insn="%s %s"%(insn.mnemonic,insn.op_str),access=op.access))
    for d in (0xA8E9A0,0xA8ED84,0xA8B238):
        print("ADDR %08X n=%d"%(d,len(gref[d])))
        for r in gref[d]:
            print("  %08X fn=%s access=%s :: %s"%(r["va"],hex(r["fn"]) if r["fn"] else "NONE",r["access"],r["insn"]))

    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","EVIDENCE","dual_bfs_callers.json")
    with open(out,"w",encoding="utf-8") as f:
        json.dump(dict(callers=callers_report,bfs=bfsrep,gref={hex(k):v for k,v in gref.items()},sweep=sweep),f,indent=1)

if __name__=="__main__":
    main()
