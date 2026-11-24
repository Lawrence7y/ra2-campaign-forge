"""W163: scan .text (skipdata=True, independent of atlas) for all absolute
memory operands whose disp falls in [LO,HI] around 0xB0CE88.

Discover the DVC layout empirically: which field offsets are referenced,
by which instructions, and in which functions (nearest preceding atlas entry,
for reference only -- counting is done on raw bytes).
"""
import sys, os, bisect, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

LO = 0xB0CE50
HI = 0xB0CEC0

def main():
    b = w.Bin()
    rows,hdr = w.load_atlas()
    entries = [va for va,_ in rows]
    atlas = {va:rec for va,rec in rows}
    m = w.md32(skipdata=True)
    data = b.section_bytes(".text")
    found = []
    nskip = 0
    for insn in m.disasm(data, b.text["va"]):
        if insn.id == 0:
            nskip += insn.size
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0:
                    d = mem.disp & 0xFFFFFFFF
                    if LO <= d < HI:
                        i = bisect.bisect_right(entries, insn.address)-1
                        fn = entries[i] if i>=0 else None
                        found.append(dict(va=insn.address, disp=d,
                                          insn="%s %s"%(insn.mnemonic,insn.op_str),
                                          fn=fn, access=op.access))
    print("SKIP_BYTES", nskip, "FOUND", len(found))
    # group by disp
    bydisp = {}
    for r in found:
        bydisp.setdefault(r["disp"], []).append(r)
    for d in sorted(bydisp):
        print("=== disp %08X (n=%d) ==="%(d,len(bydisp[d])))
        for r in bydisp[d]:
            print("  %08X fn=%s access=%s :: %s"%(r["va"], hex(r["fn"]) if r["fn"] else "NONE", r["access"], r["insn"]))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","EVIDENCE","refs_B0CE88_window.json"),"w",encoding="utf-8") as f:
        json.dump(dict(LO=LO,HI=HI,skipped=nskip,found=found),f,indent=1)

if __name__=="__main__":
    main()
