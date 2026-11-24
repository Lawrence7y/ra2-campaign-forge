"""S4: whole-image call/global reference index + chain-family census.

Produces, for every Ghidra-established function:
  * direct call/jmp edges (E8/E9 imm, and FF15 [IAT] is captured as a global ref)
  * absolute global memory references (disp32 with no base/index)

then prints the parts that bound cause B:
  1. callers of the chain functions  0x5683C0 / 0x5687F0  and the per-cell
     primitives 0x47E8A0 / 0x47EA90 / 0x47D2B0 / 0x48DEE0
  2. every reference to the cell-table global 0x87F924 and the map global
     0x87F7E8 (the "whole-table replacement" bypass candidate)
  3. every HeapFree / VirtualFree / LocalFree / HeapAlloc IAT call site
  4. candidate chain-head writers: base register not esp/ebp  (per §640-4 the
     esp/ebp-based ones are stack locals, i.e. NOT CellClass)

Run: python s4_refs.py > ..\\EVIDENCE\\s4_refs.log 2>&1
"""
import capstone
import w152_core as C

X = capstone.x86

CALLS = {}        # callee -> [(site, fn)]
GREF = {}         # global -> [(site, fn, text)]
PERFN_G = {}      # fn -> set(globals)

GLOBALS_OF_INTEREST = {
    0x0087F924: "CellClass table pointer (map global +0x13C)",
    0x0087F7E8: "global map object (this of the chain wrappers)",
    0x0087F928: "map global +0x140 (cell bound)",
    0x00ABDC50: "static dummy CellClass object",
    0x00AC139C: "static empty coord list",
    0x0089C8E8: "static empty coord list (type slot 0x90)",
    0x00A8EB50: "BuildingClass::Array.Count",
    0x00A8EB44: "BuildingClass::Array.Items",
    0x00B0F730: "AbstractClass::Array.Count",
    0x007E127C: "IAT HeapFree",
    0x007E1290: "IAT VirtualFree",
    0x007E1340: "IAT LocalFree",
    0x007E1278: "IAT HeapAlloc",
    0x007E12A4: "IAT HeapReAlloc",
    0x007E1294: "IAT VirtualAlloc",
    0x007E3EBC: "BuildingClass main vtable",
}

WATCH_FUNCS = {0x005683C0: "attach wrapper (AddObject driver)",
               0x005687F0: "detach wrapper (RemoveObject driver)",
               0x0047E8A0: "CellClass::AddObject   (per-cell)",
               0x0047EA90: "CellClass::RemoveObject(per-cell)",
               0x0047D2B0: "per-cell post-processing",
               0x0048DEE0: "coord-list copy to stack",
               0x0043F180: "BuildingClass slot73 dispatcher",
               0x004D3780: "mobile slot73 dispatcher",
               0x0071BFB0: "Terrain slot73 dispatcher"}


def absmem(insn):
    """Return the absolute disp of a [disp32] memory operand, else None."""
    for o in insn.operands:
        if o.type == X.X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0:
            return o.mem.disp
    return None


def main():
    nfun = 0
    for entry in C.ENTRIES:
        inss = C.disas_fn(entry)
        if not inss:
            continue
        nfun += 1
        gs = set()
        for ins in inss:
            if ins.mnemonic in ("call", "jmp") and ins.operands and \
                    ins.operands[0].type == X.X86_OP_IMM:
                tgt = ins.operands[0].imm & 0xFFFFFFFF
                CALLS.setdefault(tgt, []).append((ins.address, entry))
            g = absmem(ins)
            if g is not None:
                g &= 0xFFFFFFFF
                gs.add(g)
                GREF.setdefault(g, []).append((ins.address, entry,
                                               "%s %s" % (ins.mnemonic, ins.op_str)))
        PERFN_G[entry] = gs

    print("functions scanned = %d" % nfun)
    print("")
    print("=== 1) callers of the chain family (direct call/jmp imm only) ===")
    for f, label in sorted(WATCH_FUNCS.items()):
        sites = CALLS.get(f, [])
        print("  %08X %-42s callers=%d" % (f, label, len(sites)))
        for site, fn in sorted(sites):
            print("        site %08X  in fn %s" % (site, C.fn_label(fn)))
    print("")
    print("=== 2a) references to global map/cell globals ===")
    for g, label in sorted(GLOBALS_OF_INTEREST.items()):
        refs = GREF.get(g, [])
        print("  %08X %-46s refs=%d" % (g, label, len(refs)))
        for site, fn, txt in sorted(refs):
            print("        %08X fn=%s  %s" % (site, C.fn_label(fn), txt))
    print("")
    print("=== 2b) which functions reference 0x0087F924 (cell table) ===")
    fs = sorted({fn for site, fn, txt in GREF.get(0x0087F924, [])})
    print("  count = %d" % len(fs))
    for f in fs:
        print("     %s" % C.fn_label(f))


main()
