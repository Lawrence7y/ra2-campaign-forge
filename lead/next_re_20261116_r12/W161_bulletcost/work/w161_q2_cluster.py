"""W161 Q2.2b: examine render cluster 0x6D8DB0 loop structure and what it iterates.
Look for layer arrays/visible lists and whether the bullet container is walked."""
import sys, os, json, bisect
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w
import capstone
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
def containing(va):
    i=bisect.bisect_right(entries,va)-1
    return entries[i] if i>=0 else None
def insns_of(b,va,size):
    m=w.md32(skipdata=True); out=[]
    for insn in m.disasm(b.read(va,size),va):
        if insn.id==0: continue
        out.append((insn.address,insn.mnemonic,insn.op_str,insn.size))
    return out

def main():
    b=w.Bin()
    # Render cluster: dump around the 5 DrawIfVisible call sites
    print("=== 0x6D8DB0 render cluster: calls + loops + array bases ===")
    for fn,size in ((0x6D8DB0,0x1500),(0x6D97D0,0x300),(0x6D9920,0x300)):
        ins=insns_of(b,fn,size)
        print("\n--- fn %08X atlas_size=%s insns=%d ---"%(fn,atlas.get(fn,{}).get('size'),len(ins)))
        for a,mn,op,sz in ins:
            interesting = (mn=="call" or "ptr" in op or mn.startswith("j") or
                           "[0x" in op.lower() or "0x6d" in op.lower())
            # print calls and key memory/loops
            if mn=="call" or (mn.startswith("j") and op.startswith("0x")):
                print("  %08X %-6s %s"%(a,mn,op))
        # count DrawIfVisible calls
        n104=sum(1 for a,mn,op,sz in ins if mn=="call" and "0x104" in op)
        print("  >>> call[reg+0x104] count=%d"%n104)
        # find all absolute array globals referenced
        globs=sorted(set(op.lower() for a,mn,op,sz in ins if op.lower().startswith("dword ptr [0x") or "[0x" in op.lower()))
        print("  globals/refs sample:", globs[:40])

    # search: does anything add bullet vtable 0x7E46E4 to a layer? Check calls to bullet container funcs
    print("\n=== who references 0x6D8DB0 (render cluster dispatcher) ===")
    calls,jmps,stats=w.sweep_full_text(b)
    for s in calls.get(0x6D8DB0,[]):
        print("  call site %08X fn=%s"%(s,hex(containing(s)) if containing(s) else "?"))
    # DrawIfVisible slot 0x104 - is bullet vtable target 0x5F4B10 too? (slot65=0x5F4B10 yes)
    print("\n=== check 0x6D8DB0 loop: container setup near 0x6D909E ===")
    ins=insns_of(b,0x6D8F00,0x400)
    for a,mn,op,sz in ins:
        print("  %08X %-6s %s"%(a,mn,op))

if __name__=="__main__":
    main()
