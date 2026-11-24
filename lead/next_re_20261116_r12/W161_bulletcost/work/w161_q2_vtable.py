"""W161 Q2.1: dump BulletClass main vtable 0x007E46E4 slots, and independently classify
which slot looks like Draw using (a) first instructions, (b) direct callees, (c) calls to
known draw/blit primitives, (d) surface/pitch/memcpy-style memory operations.

dual-channel: slot addresses read from raw .rdata bytes (byte channel) AND cross-checked
against vtable_members.tsv (atlas channel).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
VT = 0x007E46E4

DRAW_PRIMS = {
    0x494B60: "BlitTransXlatAlphaZRead", 0x4912B0: "BlitTransXlat",
    0x4960A0: "RLEBlitTransXlat", 0x7BC890: "BlitTrans",
    0x492670: "BlitTransDarken", 0x7BC7F0: "BlitPlain",
    0x4144B0: "AircraftClass::Draw", 0x43D290: "BuildingClass::Draw",
    0x468090: "BulletClass::Draw(claimed)", 0x5F4B10: "DrawIfVisible",
}

def callees_of(va, size, b):
    m = w.md32(skipdata=True)
    data = b.read(va, min(size, 0x20000))
    out = []
    for insn in m.disasm(data, va):
        if insn.id == 0:
            continue
        if insn.mnemonic == "call" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_IMM:
            out.append(insn.operands[0].imm)
    return out

def closure(va, by_caller, max_depth=3):
    seen = {va}; frontier = [(va, 0)]; hits = []
    while frontier:
        cur, d = frontier.pop(0)
        if d >= max_depth: continue
        for c in by_caller.get(cur, ()):
            hits.append((c, d+1))
            if c not in seen:
                seen.add(c); frontier.append((c, d+1))
    return hits

def main():
    b = w.Bin()
    rows, hdr = w.load_atlas()
    atlas = {va: rec for va, rec in rows}
    vtmem = w.load_vtable_members()
    by_caller, edges = w.load_calledges()

    N = 126
    slots = [b.u32(VT + 4*i) for i in range(N)]

    print("=== BulletClass main vtable %08X: first %d slots (byte channel from .rdata) ===" % (VT, N))
    result = []
    m = w.md32(skipdata=True)
    for i, tgt in enumerate(slots):
        toff = 4*i
        if tgt == 0:
            result.append(dict(slot=i, toff=toff, target=None, kind="null"))
            continue
        ar = atlas.get(tgt)
        size = int(ar["size"],10) if ar else None
        ninstr = ar.get("n_instr") if ar else None
        sec = b.sec_of(tgt)
        first = []
        try:
            data = b.read(tgt, 48)
            for insn in m.disasm(data, tgt):
                first.append("%s %s" % (insn.mnemonic, insn.op_str))
                if len(first) >= 6: break
        except Exception as e:
            first = ["ERR:%s" % e]
        cl = callees_of(tgt, size or 64, b) if size else []
        prims = sorted(set(DRAW_PRIMS.get(c, "") for c in cl if c in DRAW_PRIMS))
        ch = closure(tgt, by_caller, 3)
        prims_closure = sorted(set(DRAW_PRIMS.get(c, "") for c,_ in ch if c in DRAW_PRIMS))
        ni = nm = nc = 0
        if size and 0 < size < 0x20000:
            ni, nm, nc, _, _, _, _ = w.insn_stats(b, tgt, size)
        kind = "code" if sec and sec["name"]==".text" else (sec["name"] if sec else "outside")
        rec = dict(slot=i, toff=toff, target=tgt, atlas_size=size, atlas_ninstr=ninstr,
                   first=first, direct_prims=prims, closure_prims=prims_closure,
                   n_insn=ni, n_mem=nm, n_call=nc, kind=kind, n_direct_callees=len(cl))
        result.append(rec)
        print("slot %3d (+0x%03X) tgt=%08X size=%-6s ni=%-5s mem=%-5d call=%-3d prims=%s closure=%s | %s" % (
            i, toff, tgt, size, ninstr, nm, nc, ",".join(prims) or "-",
            ",".join(prims_closure) or "-", first[0] if first else ""))

    with open(os.path.join(OUT, "Q2_vtable_dump.json"), "w", encoding="utf-8") as f:
        json.dump(dict(vt=VT, n=N, slots=result), f, indent=1)

    ref = dict((s, fn) for s, fn, ic in vtmem.get(VT, []))
    diffs = []
    for rec in result:
        if rec["kind"]=="null": continue
        if rec["slot"] in ref and ref[rec["slot"]] != rec["target"]:
            diffs.append((rec["slot"], rec["target"], ref[rec["slot"]]))
    print("\nCROSSCHECK vs vtable_members.tsv: %d slots compared, %d diffs" %
          (sum(1 for r in result if r["kind"]!="null"), len(diffs)))
    for d in diffs[:20]:
        print("  DIFF slot %d byte=%08X ref=%08X" % d)

    print("\n=== slots with any draw primitive in direct callees or depth-3 closure ===")
    for rec in result:
        if rec["kind"]=="null": continue
        if rec["direct_prims"] or rec["closure_prims"]:
            print("  slot %d (+0x%X) tgt=%08X size=%s direct=%s closure=%s first=%s" % (
                rec["slot"], rec["toff"], rec["target"], rec["atlas_size"],
                rec["direct_prims"], rec["closure_prims"], rec["first"][:2]))

if __name__ == "__main__":
    main()
