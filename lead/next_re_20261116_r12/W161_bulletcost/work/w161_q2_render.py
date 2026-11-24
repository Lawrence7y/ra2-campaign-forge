"""W161 Q2.1c: verify DrawIfVisible->Draw slot link, analyze draw helper 0x4AED70.
Q2.2: locate render dispatch - all call[reg+0x114]/call[reg+0x104] sites, all refs to
bullet container (0xA8ED40/44/50), and inspect known render cluster.
All byte hits boundary-checked; two channels (full byte sweep + atlas)."""
import sys, os, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
rows, hdr = w.load_atlas()
entries = [va for va,_ in rows]
atlas = {va:rec for va,rec in rows}

def containing_entry(va):
    i = bisect.bisect_right(entries, va)-1
    return entries[i] if i>=0 else None

def disasm_range(b, va, size):
    m = w.md32(skipdata=True)
    return [(i.address,i.mnemonic,i.op_str,i.size) for i in m.disasm(b.read(va,size),va) if i.id!=0]

def scan_call_slot(b, slot):
    """find 'call [reg+slot]' = FF 5x <slot> byte pattern, boundary-checked."""
    m = w.md32(skipdata=True)
    data = b.section_bytes(".text")
    hits=[]
    valid_boundaries=set()
    for insn in m.disasm(data, b.text["va"]):
        if insn.id==0: continue
        valid_boundaries.add(insn.address)
    for i in range(len(data)-2):
        if data[i]==0xFF and (data[i+1] & 0xF8)==0x50 and data[i+2]==slot:
            va=b.text["va"]+i
            hits.append((va, data[i:i+3].hex(), va in valid_boundaries))
    return hits

def main():
    b=w.Bin()
    print("=== Q2.1c: DrawIfVisible 0x5F4B10 full disasm ===")
    for a,mn,op,sz in disasm_range(b,0x5F4B10,511):
        print("  %08X  %-6s %s" % (a,mn,op))
    ok,insn,why=w.boundary_check(b,0x5F4B10,0x5F4CFD)
    print("BOUNDARY 0x5F4CFD from 0x5F4B10 entry:",ok,why)

    print("\n=== Q2.1c: draw helper 0x4AED70 (1317B) first 60 insns ===")
    for a,mn,op,sz in disasm_range(b,0x4AED70,400)[:60]:
        print("  %08X  %-6s %s" % (a,mn,op))

    print("\n=== Q2.2: call [reg+0x114] sites (Draw slot) ===")
    h114=scan_call_slot(b,0x114)
    print("  raw hits:",len(h114)," boundary-valid:",sum(1 for x in h114 if x[2]))
    for va,by,ok in h114:
        ce=containing_entry(va)
        print("    %08X bytes=%s boundary=%s containing_fn=%s" % (va,by,ok,hex(ce) if ce else "?"))

    print("\n=== Q2.2: call [reg+0x104] sites (DrawIfVisible slot) ===")
    h104=scan_call_slot(b,0x104)
    print("  raw hits:",len(h104)," boundary-valid:",sum(1 for x in h104 if x[2]))
    for va,by,ok in h104:
        ce=containing_entry(va)
        print("    %08X bytes=%s boundary=%s containing_fn=%s" % (va,by,ok,hex(ce) if ce else "?"))

    print("\n=== Q2.2: absolute refs to bullet container ===")
    for tgt in (0xA8ED40,0xA8ED44,0xA8ED50,0xA8ED3C):
        found=w.sweep_disps_to(b,tgt)
        print("  refs to %08X: %d" % (tgt,len(found)))
        for f in found[:40]:
            ce=containing_entry(f['va'])
            print("    %08X %-40s fn=%s" % (f['va'],f['insn'][:40],hex(ce) if ce else "?"))

    with open(os.path.join(OUT,"Q2_render_scan.json"),"w",encoding="utf-8") as fo:
        json.dump(dict(call114=h114,call104=h104),fo,indent=1)

if __name__=="__main__":
    main()
