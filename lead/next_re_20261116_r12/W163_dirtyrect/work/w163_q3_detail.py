"""W163: identify 0x421EA0 class via COL name; disasm 0x5F3B80 nested loops;
shortest paths ROOT->count-scanning suspect functions (dual channel)."""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

ROOT=0x4666E0
CANDS=[0x4F9B70,0x509400,0x50D6D0,0x5F3B80,0x6DD8B0,0x71E940,0x6EAEE0,0x63B0A0,0x63B150]

def colname(b,p):
    try: d=b.read(p,0xA0)
    except: return []
    out=[]; cur=bytearray()
    for x in d:
        if 32<=x<127: cur.append(x)
        else:
            if len(cur)>=4: out.append(cur.decode('ascii','replace'))
            cur=bytearray()
    if len(cur)>=4: out.append(cur.decode('ascii','replace'))
    return out[:8]

def bfs_path(g,t):
    prev={ROOT:None}; q=collections.deque([ROOT])
    while q:
        u=q.popleft()
        if u==t: break
        for v in g.get(u,{}):
            if v not in prev: prev[v]=u; q.append(v)
    if t not in prev: return None
    p=[]; c=t
    while c is not None: p.append(c); c=prev[c]
    p.reverse(); return p

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
    print("=== COL names for 0x421EA0 vtable COL pointers ===")
    for p in (0x7FB9C0,0x7FB9D8):
        print(" %08X:"%p, colname(b,p), "raw:", " ".join("%02X"%x for x in b.read(p,32)))
    # Also look at the vtables_canonical.json which may map these vt offsets
    print("=== canonical json search 7e3328/7e3354 ===")
    import json as J
    txt=open(w.VTABLES_CANON,'r',encoding='utf-8',errors='replace').read()
    for s in ('7e3328','7E3328','7e3354','7E3354','00410590','410590'):
        i=txt.find(s); print("  ",s,i, (txt[max(0,i-160):i+160] if i>=0 else ''))

    # build graphs
    byA,_=w.load_calledges()
    ga=collections.defaultdict(lambda: collections.defaultdict(list))
    for c,cal,s in w.load_calledges()[1]: ga[c][cal].append(s)
    calls,jmps,sweep=w.sweep_full_text(b)
    def caller_of(site):
        i=bisect.bisect_right(entries,site)-1
        return entries[i] if i>=0 else None
    gb=collections.defaultdict(lambda: collections.defaultdict(list))
    for tgt,sts in calls.items():
        for s in sts:
            c=caller_of(s)
            if c is not None: gb[c][tgt].append(s)
    print("=== shortest paths ROOT -> count-scan candidates ===")
    for t in CANDS:
        pa=bfs_path(ga,t); pb=bfs_path(gb,t)
        print("TARGET %08X"%t)
        print("  A: %s"%(" -> ".join(hex(x) for x in pa) if pa else "UNREACHABLE"))
        print("  B: %s"%(" -> ".join(hex(x) for x in pb) if pb else "UNREACHABLE"))

    print("=== disasm 0x5F3B80 (AbstractClass Count scanner) ===")
    m=w.md32(skipdata=True); f=0x5F3B80; sz=int(atlas[f]["size"],10)
    for insn in m.disasm(b.read(f,sz),f):
        if insn.id==0: continue
        print("  %08X %-8s %s"%(insn.address,insn.mnemonic,insn.op_str))

if __name__=="__main__": main()
