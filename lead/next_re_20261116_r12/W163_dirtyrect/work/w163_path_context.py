"""W163: disasm intermediate functions on the Bullet->dirtyAdd path and
the call-site contexts in BulletClass::AI. Also verify instruction boundaries
of all call sites on the two discovered paths (boundary_check returns UNKNOWN
when span too large / undecodable -- never False-on-bail).
"""
import sys, os, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

def disasm_range(b, start, end):
    m=w.md32(skipdata=True)
    data=b.read(start,end-start)
    for insn in m.disasm(data,start):
        if insn.id==0: continue
        print("  %08X  %-8s %s"%(insn.address,insn.mnemonic,insn.op_str))

def main():
    b=w.Bin()
    rows,hdr=w.load_atlas(); atlas={va:r for va,r in rows}
    def show_fn(va, maxins=200):
        rec=atlas.get(va)
        if rec is None:
            print("FUNC %08X NOT_IN_ATLAS"%va); return
        sz=int(rec["size"],10)
        print("=== FUNC %08X size=%d ==="%(va,sz))
        m=w.md32(skipdata=True); data=b.read(va,sz); n=0
        for insn in m.disasm(data,va):
            if insn.id==0: continue
            print("  %08X  %-8s %s"%(insn.address,insn.mnemonic,insn.op_str))
            n+=1
            if n>=maxins: print("  ..."); break
    for f in (0x421EA0,0x5F4EC0,0x5F4B10,0x445880,0x4F4480):
        show_fn(f, 180)

    print("=== Bullet AI call-site contexts ===")
    for va in (0x4668B8,0x467F2D,0x466771,0x467FA2):
        print("--- around %08X ---"%va)
        disasm_range(b, va-0x10, va+0x10)

    print("=== boundary verification of path call sites ===")
    # for each call site, verify it is an instruction boundary by linear disasm
    # from the enclosing function entry, using skipdata=False; UNKNOWN on bail.
    checks=[(0x4666E0,0x4668B8),(0x4666E0,0x467F2D),(0x4666E0,0x466771),(0x4666E0,0x467FA2),
            (0x421EA0,0x4222E0),(0x421EA0,0x422433),(0x421EA0,0x4224E0),
            (0x5F4EC0,0x5F5146),(0x4F4480,0x4F44DF),(0x6D3D10,0x6D4471)]
    for entry,site in checks:
        if site<entry:
            print("  site %08X entry %08X -> BELOW_ENTRY"%(site,entry)); continue
        span=site-entry
        if span>=0x8000:
            print("  site %08X entry %08X -> UNKNOWN(span)"%(site,entry)); continue
        try:
            m=w.md32(skipdata=False)
            data=b.read(entry,span+32)
            ok=False; hit=None
            for insn in m.disasm(data,entry):
                if insn.address==site: ok=True; hit="%s %s"%(insn.mnemonic,insn.op_str); break
                if insn.address>site: break
            print("  site %08X entry %08X -> %s %s"%(site,entry,"BOUNDARY" if ok else "UNKNOWN(not-reached)",hit or ""))
        except Exception as e:
            print("  site %08X entry %08X -> UNKNOWN(%s)"%(site,entry,e))

if __name__=="__main__": main()
