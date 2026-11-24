"""W163 final checks:
1) caller chain of 0x6D3D10 (render/flush) and 0x4F4480 -> main loop?
2) decode COL name at pointer chain for dirty rect vtables (7F429C/7F42BC trailing COL 80B860/80B8C8)
3) per-bullet: how many call sites to 0x421EA0 in Bullet AI and is there an alloc before?
"""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
    byA,edges=w.load_calledges()
    calls,jmps,sweep=w.sweep_full_text(b)
    def caller_of(site):
        i=bisect.bisect_right(entries,site)-1
        return entries[i] if i>=0 else None
    byB=collections.defaultdict(set)
    for tgt,sts in calls.items():
        for s in sts:
            c=caller_of(s)
            if c is not None: byB[c].add(tgt)

    print("=== caller chain: 6D3D10 <- 4F4480 <- ? ===")
    for t in (0x6D3D10,0x4F4480,0x6DD8B0,0x7265C0,0x6E53A0,0x4690B0,0x468D80):
        ca=sorted({c for c,cs in byA.items() if t in cs})
        cb=sorted({c for c,cs in byB.items() if t in cs})
        print("  %08X A_callers=%s B_callers=%s"%(t,[hex(x) for x in ca],[hex(x) for x in cb]))

    # 2) COL name: 0x80B860 holds a structure whose +8 is 0x80B850; look further
    print("=== COL chain for dirty rect vtable trailing dwords ===")
    def dump_col(p,label):
        print("  %s @%08X"%(label,p))
        for va in range(p-0x10,p+0x50,4):
            v=b.u32(va); s=b.sec_of(v)
            print("    %08X=%08X%s"%(va,v," ->"+s["name"] if s else ""))
    dump_col(0x80B850,"COL_for_7F429C?")
    dump_col(0x80B858,"COL2")
    # search for ".?AV" strings near 0x80B800..0x80B980 by raw ascii
    raw=b.read(0x80B000,0x1000)
    import re
    for m in re.finditer(rb'\.\?AV[^@\x00]{3,60}',raw):
        print("  ASCII @%08X: %s"%(0x80B000+m.start(), m.group().decode('ascii','replace')))

    # 3) count call sites to 0x421EA0 in Bullet AI and check allocations before them
    print("=== 0x421EA0 call sites in 0x4666E0 (dual channel) ===")
    la=[(c,s) for (c,cal,s) in edges if cal==0x421EA0 and c==0x4666E0]
    lb=[(tgt,s) for tgt,sts in calls.items() if tgt==0x421EA0 for s in sts if caller_of(s)==0x4666E0]
    print("  A:",[(hex(c),hex(s)) for c,s in la])
    print("  B:",[(hex(t),hex(s)) for t,s in lb])

    # 0x55BAA0 registration path gating check
    print("=== does 0x5F4EC0 call 0x55BAA0 (LogicClass register)? ===")
    print("  A:", [s for (c,cal,s) in edges if c==0x5F4EC0 and cal==0x55BAA0])
    print("  B:", [s for tgt,sts in calls.items() if tgt==0x55BAA0 for s in sts if caller_of(s)==0x5F4EC0])

if __name__=="__main__": main()
