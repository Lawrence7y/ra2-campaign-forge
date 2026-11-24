"""S5: immediate-operand scan (globals loaded with `mov reg,imm` / `push imm`)
plus full disassembly of the functions that define the chain contract and the
four slot-73 dispatchers.

Run: python s5_dump.py > ..\\EVIDENCE\\s5_dump.log 2>&1
"""
import capstone
import w152_core as C

X = capstone.x86

WATCH_IMM = {
    0x0087F924: "cell table ptr",
    0x0087F7E8: "global map object",
    0x00ABDC50: "static dummy CellClass",
    0x00AC139C: "static empty coord list",
    0x0089C8E8: "static empty coord list (type)",
    0x007E3EBC: "BuildingClass main vtable",
    0x007E3AD0: "voc/other vtable",
    0x0047E8A0: "AddObject",
    0x0047EA90: "RemoveObject",
    0x0047D2B0: "per-cell post",
    0x005683C0: "attach wrapper",
    0x005687F0: "detach wrapper",
    0x0048DEE0: "coord copy",
}

DUMP = [
    (0x005683C0, "attach wrapper  (0x5683C0)"),
    (0x005687F0, "detach wrapper  (0x5687F0)"),
    (0x0047E8A0, "CellClass::AddObject  (0x47E8A0)"),
    (0x0047EA90, "CellClass::RemoveObject (0x47EA90)"),
    (0x0043F180, "BuildingClass slot73 dispatcher (0x43F180)"),
    (0x004D3780, "mobile slot73 dispatcher (0x4D3780)"),
    (0x0071BFB0, "Terrain slot73 dispatcher (0x71BFB0)"),
    (0x0071BFB0, ""),
]


def imm_refs():
    hits = {}
    for entry in C.ENTRIES:
        for ins in C.disas_fn(entry):
            for o in ins.operands:
                if o.type != X.X86_OP_IMM:
                    continue
                v = o.imm & 0xFFFFFFFF
                if v in WATCH_IMM:
                    hits.setdefault(v, []).append((ins.address, entry, C.fmt(ins)))
    return hits


def main():
    print("=== immediate references to watched globals ===")
    hits = imm_refs()
    for g, label in sorted(WATCH_IMM.items()):
        lst = hits.get(g, [])
        print("  %08X %-32s immediate-refs=%d" % (g, label, len(lst)))
        for site, fn, txt in sorted(lst):
            print("        %s   fn=%s" % (txt, C.fn_label(fn)))
    print("")
    seen = set()
    for entry, label in DUMP:
        if not label or entry in seen:
            continue
        seen.add(entry)
        print("")
        print("=" * 78)
        print("=== %s   entry=%08X size=%s ===" % (label, entry, C.fn_size(entry)))
        print("=" * 78)
        for ins in C.disas_fn(entry):
            fnm = C.owning_fn(ins.address)
            mark = "" if fnm == entry else "   <-- leaves fn (owner %08X)" % fnm
            print(C.fmt(ins) + mark)


main()
