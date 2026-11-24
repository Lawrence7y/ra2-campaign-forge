"""W161 Q2.1b: deeply inspect draw-candidate slots - actual callees, surface ops,
string xrefs. Determine which slot 'looks like Draw' independently of the ledger claim."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
rows, hdr = w.load_atlas()
atlas = {va: rec for va, rec in rows}

CANDIDATES = {
    0x468090: "slot69 +0x114 (claimed BulletClass::Draw)",
    0x5F4B10: "slot65 +0x104 (DrawIfVisible per ledger v65)",
    0x5F4D30: "slot53 +0xD4",
    0x468670: "slot124 +0x1F0 (biggest slot)",
    0x4666E0: "slot23 +0x5C (AI, control)",
    0x5F5390: "slot91 +0x16C (410 insn)",
}

def name_of(va):
    return atlas.get(va, {}).get("strings", "") or ""

def dump_callees(b, va, size):
    m = w.md32(skipdata=True)
    data = b.read(va, size)
    out = []
    for insn in m.disasm(data, va):
        if insn.id == 0: continue
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                t = op.imm
                sz = atlas.get(t, {}).get("size", "?")
                st = name_of(t)
                out.append((insn.address, t, sz, st))
            else:
                out.append((insn.address, None, op.type, insn.op_str))
    return out

def main():
    b = w.Bin()
    report = {}
    for va, label in CANDIDATES.items():
        rec = atlas.get(va)
        size = int(rec["size"],10) if rec else 64
        print("\n===== %s : %08X size=%d ni=%s =====" % (label, va, size, rec.get("n_instr") if rec else "?"))
        cl = dump_callees(b, va, size)
        report[va] = dict(label=label, size=size, callees=[])
        print("  direct callees (%d):" % len(cl))
        for site, t, sz, st in cl:
            if t is not None:
                print("    @%08X -> %08X size=%-5s str=%s" % (site, t, sz, st[:40]))
                report[va]["callees"].append(dict(site=site, target=t, size=sz))
            else:
                print("    @%08X -> [indirect] %s" % (site, st))

    by_caller, edges = w.load_calledges()
    BLIT_KW = ("Blit", "blt", "Surface", "DSurface", "memcpy", "RLE")
    print("\n===== blit/surface-like named callees in depth<=4 closure =====")
    for root in (0x468090, 0x5F4B10):
        seen=set(); frontier=[(root,0)]; found=[]
        while frontier:
            cur,d = frontier.pop(0)
            if d>=4: continue
            for c in by_caller.get(cur,()):
                st=name_of(c)
                if st and any(k.lower() in st.lower() for k in BLIT_KW):
                    found.append((d+1,c,st))
                if c not in seen:
                    seen.add(c); frontier.append((c,d+1))
        print("  root %08X closure=%d funcs; blit/surface-named:" % (root, len(seen)))
        for d,c,st in found[:30]:
            print("    d%d %08X %s" % (d,c,st[:60]))

    with open(os.path.join(OUT,"Q2_draw_candidates.json"),"w",encoding="utf-8") as f:
        json.dump(report,f,indent=1)

if __name__=="__main__":
    main()
