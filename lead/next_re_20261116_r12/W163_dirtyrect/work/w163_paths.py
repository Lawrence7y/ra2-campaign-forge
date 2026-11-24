"""W163: find shortest call paths ROOT->each dirty-cluster target in both channels,
with per-hop site addresses; and dump 0xA8E9A0 / 0xA8ED84 refs by function.
"""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

ROOT=0x4666E0
TARGETS=[0x6D2790,0x6D2B60,0x6D3D10,0x6D8DB0,0x6DA980]

def bfs_path(graph_sites, target):
    # graph_sites: caller -> {callee: [sites]}
    prev={ROOT:None}; q=collections.deque([ROOT])
    while q:
        u=q.popleft()
        if u==target: break
        for v in graph_sites.get(u,{}):
            if v not in prev:
                prev[v]=u; q.append(v)
    if target not in prev: return None
    path=[]; cur=target
    while cur is not None:
        path.append(cur); cur=prev[cur]
    path.reverse()
    hops=[]
    for i in range(len(path)-1):
        sites=graph_sites[path[i]][path[i+1]]
        hops.append((path[i],path[i+1],sites[:3]))
    return path,hops

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]
    by_caller_A,edges=w.load_calledges()
    # build A graph_sites
    ga=collections.defaultdict(lambda: collections.defaultdict(list))
    for c,cal,s in edges: ga[c][cal].append(s)
    calls,jmps,sweep=w.sweep_full_text(b)
    def caller_of(site):
        i=bisect.bisect_right(entries,site)-1
        return entries[i] if i>=0 else None
    gb=collections.defaultdict(lambda: collections.defaultdict(list))
    for tgt,sts in calls.items():
        for s in sts:
            c=caller_of(s)
            if c is not None: gb[c][tgt].append(s)

    print("=== SHORTEST PATHS ROOT %08X -> dirty targets ==="%ROOT)
    allp={}
    for name,g in (("A_ghidra",ga),("B_byte",gb)):
        print("CHANNEL",name)
        for t in TARGETS:
            r=bfs_path(g,t)
            if r is None:
                print("  -> %08X UNREACHABLE"%t)
            else:
                path,hops=r
                print("  -> %08X depth=%d"%(t,len(path)-1))
                for (fr,to,sites) in hops:
                    print("       %08X -> %08X @ %s"%(fr,to,[hex(x) for x in sites]))
            allp.setdefault("%08X"%t,{})[name]=None if r is None else r[0]

    # 0xA8E9A0 and 0xA8ED84 refs grouped by fn
    print("=== 0xA8E9A0 refs grouped by function ===")
    m=w.md32(skipdata=True); data=b.section_bytes(".text")
    gref=collections.defaultdict(lambda: collections.defaultdict(list))
    for insn in m.disasm(data,b.text["va"]):
        if insn.id==0: continue
        for op in insn.operands:
            if op.type==capstone.x86.X86_OP_MEM:
                mem=op.mem
                if mem.base==0 and mem.index==0:
                    d=mem.disp&0xFFFFFFFF
                    if d in (0xA8E9A0,):
                        c=caller_of(insn.address)
                        gref[d][c].append((insn.address,"%s %s"%(insn.mnemonic,insn.op_str),op.access))
    for d,byfn in gref.items():
        for fn,lst in sorted(byfn.items(),key=lambda x:(x[0] is None,x[0])):
            print("  fn=%s n=%d"%(hex(fn) if fn else "NONE",len(lst)))
            for va,s,acc in lst:
                print("     %08X access=%d %s"%(va,acc,s))

    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","EVIDENCE","shortest_paths.json")
    with open(out,"w",encoding="utf-8") as f: json.dump(allp,f,indent=1)

if __name__=="__main__": main()
