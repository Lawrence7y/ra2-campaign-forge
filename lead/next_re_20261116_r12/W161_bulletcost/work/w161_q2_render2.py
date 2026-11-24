"""W161 Q2.2: correct call-slot scan (FF 9x disp32 for +0x114/+0x104), inspect
container-ref functions (0x534450,0x7192F0,0x67C690), and the render cluster 0x6D8DB0.
Determine whether any code traverses the bullet array and calls Draw."""
import sys, os, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
rows,hdr=w.load_atlas(); entries=[va for va,_ in rows]; atlas={va:r for va,r in rows}
def containing(va):
    i=bisect.bisect_right(entries,va)-1
    return entries[i] if i>=0 else None

def scan_call_mem_disp32(b, slot):
    """scan .text for call [reg+disp32]==FF 9x <slot32> ; also FF 8x (mod=10). disp32=slot."""
    m=w.md32(skipdata=True); data=b.section_bytes(".text")
    boundaries=set()
    for insn in m.disasm(data,b.text["va"]):
        if insn.id==0: continue
        boundaries.add(insn.address)
    lo=slot & 0xFF; hi=(slot>>8)&0xFF
    hits=[]
    # FF 9x xx xx 00 00  (mod=10 reg=001 rm=x) ; disp32 little endian
    for i in range(len(data)-5):
        if data[i]==0xFF and (data[i+1] & 0xF8)==0x90 and data[i+2]==lo and data[i+3]==hi and data[i+4]==0 and data[i+5]==0:
            va=b.text["va"]+i
            hits.append((va,data[i:i+6].hex(),va in boundaries))
    return hits

def insns_of(b,va,size,limit=None):
    m=w.md32(skipdata=True); out=[]
    for insn in m.disasm(b.read(va,size),va):
        if insn.id==0: continue
        out.append((insn.address,insn.mnemonic,insn.op_str))
        if limit and len(out)>=limit: break
    return out

def summarize_fn(b,va):
    rec=atlas.get(va); size=int(rec["size"],10) if rec else 64
    ins=insns_of(b,va,size)
    calls=[(a,op) for a,mn,op in ins if mn=="call"]
    # classify calls
    drawlike=sum(1 for a,op in calls if ("0x114" in op or "0x104" in op or "0x5f4b10" in op.lower() or "0x468090" in op.lower()))
    mem=[(a,mn,op) for a,mn,op in ins if "call" in mn and "ptr" in op]
    print("  fn %08X size=%s insns=%d callsimm=%d callmem=%d draw_calls=%d" %
          (va,size,len(ins),len(calls)-len(mem),len(mem),drawlike))
    return ins

def main():
    b=w.Bin()
    print("=== Q2.2 corrected: call [reg+0x114] (Draw slot) disp32 ===")
    h114=scan_call_mem_disp32(b,0x114)
    print("  hits=%d boundary_valid=%d"%(len(h114),sum(1 for x in h114 if x[2])))
    for va,by,ok in h114:
        print("    %08X %s boundary=%s fn=%s"%(va,by,ok,hex(containing(va)) if containing(va) else "?"))
    print("=== Q2.2 corrected: call [reg+0x104] (DrawIfVisible slot) disp32 ===")
    h104=scan_call_mem_disp32(b,0x104)
    print("  hits=%d boundary_valid=%d"%(len(h104),sum(1 for x in h104 if x[2])))
    for va,by,ok in h104:
        print("    %08X %s boundary=%s fn=%s"%(va,by,ok,hex(containing(va)) if containing(va) else "?"))

    print("\n=== Q2.2: container-ref functions summaries ===")
    for va in (0x466380,0x466560,0x534450,0x55B880,0x64DEA0,0x67C690,0x7192F0):
        summarize_fn(b,va)

    print("\n=== Q2.2: who calls DrawIfVisible 0x5F4B10 directly (rel calls) ===")
    calls,jmps,stats=w.sweep_full_text(b)
    sites=calls.get(0x5F4B10,[])
    print("  direct call sites to 0x5F4B10: %d"%len(sites))
    for s in sites:
        print("    %08X fn=%s"%(s,hex(containing(s)) if containing(s) else "?"))
    print("=== who calls Draw 0x468090 directly (rel calls) ===")
    sites=calls.get(0x468090,[])
    print("  direct call sites to 0x468090: %d"%len(sites))
    for s in sites:
        print("    %08X fn=%s"%(s,hex(containing(s)) if containing(s) else "?"))

    with open(os.path.join(OUT,"Q2_render_scan2.json"),"w",encoding="utf-8") as f:
        json.dump(dict(call114=h114,call104=h104,drawif_visible_sites=sites),f,indent=1)

if __name__=="__main__":
    main()
