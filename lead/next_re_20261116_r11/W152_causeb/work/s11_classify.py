"""S11: classify every 4-byte writer of [reg+0xE4] / [reg+0xE8] (chain heads).

A writer is "CellClass-context" only if its containing function shows cell
fingerprints.  Everything else is the §640-4 same-offset collision (other
classes using +0xE4 for their own fields).

Fingerprints tested per containing function:
  T  references the cell table pointer  [0x87F924]
  I  contains the cell-index idiom       shl reg,9   (y*512+x)
  A  calls CellClass::AddObject          0x47E8A0
  R  calls CellClass::RemoveObject       0x47EA90
  D  calls the per-cell post hook        0x47D2B0
  G  contains a guarded head fixup `cmp [reg+0xE4/8],X` (the §640-3 shape)

Run: python s11_classify.py > ..\\EVIDENCE\\s11_classify.log 2>&1
"""
import capstone
import w152_core as C

X = capstone.x86


def scan_fn(entry):
    inss = C.disas_fn(entry)
    refs_table = False
    shift9 = False
    calls = set()
    guarded = []
    stores = []
    for ins in inss:
        for o in ins.operands:
            if o.type == X.X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0 \
                    and (o.mem.disp & 0xFFFFFFFF) == 0x87F924:
                refs_table = True
        if ins.mnemonic == "shl" and len(ins.operands) == 2 and \
                ins.operands[1].type == X.X86_OP_IMM and ins.operands[1].imm == 9:
            shift9 = True
        if ins.mnemonic in ("call", "jmp") and ins.operands and \
                ins.operands[0].type == X.X86_OP_IMM:
            calls.add(ins.operands[0].imm & 0xFFFFFFFF)
        if ins.mnemonic == "cmp" and len(ins.operands) == 2:
            o = ins.operands[0]
            if o.type == X.X86_OP_MEM and o.mem.disp in (0xE4, 0xE8) and o.mem.index == 0:
                guarded.append(ins)
        if ins.mnemonic.startswith("mov") and ins.operands and \
                ins.operands[0].type == X.X86_OP_MEM and \
                ins.operands[0].mem.disp in (0xE4, 0xE8) and \
                ins.operands[0].mem.index == 0 and ins.operands[0].size == 4:
            stores.append(ins)
    return refs_table, shift9, calls, guarded, stores


def main():
    items = []
    for entry in C.ENTRIES:
        refs_table, shift9, calls, guarded, stores = scan_fn(entry)
        if not stores:
            continue
        fp = ""
        fp += "T" if refs_table else "-"
        fp += "I" if shift9 else "-"
        fp += "A" if 0x47E8A0 in calls else "-"
        fp += "R" if 0x47EA90 in calls else "-"
        fp += "D" if 0x47D2B0 in calls else "-"
        fp += "G" if guarded else "-"
        items.append((entry, fp, [s.address for s in stores], guarded))
    print("functions with a 4-byte store to [reg+0xE4] or [reg+0xE8]: %d" % len(items))
    print("cols: T=reads[0x87F924] I=shl*,9 A=calls AddObject R=calls RemoveObject")
    print("      D=calls 0x47D2B0 G=contains cmp [reg+0xE4/8],X")
    print("")
    print("%-12s %-7s %-4s %s" % ("function", "flags", "n", "store sites"))
    cellish = 0
    for entry, fp, sites, guarded in sorted(items, key=lambda x: (-len(x[1].replace('-', '')), x[0])):
        iscell = fp[2] == 'A' or fp[3] == 'R'
        if iscell:
            cellish += 1
        print("%-12s %-7s %-4d %s%s" % (
            "%08X" % entry, fp, len(sites),
            " ".join("%08X" % s for s in sites),
            "   <== AddObject/RemoveObject caller" if iscell else ""))
    print("")
    print("direct Add/Remove-object callers among chain-head writers: %d" % cellish)
    print("")
    print("=== the four legacy §640-3 'conditional head fixup' sites ===")
    for a in (0x436A2D, 0x62FEFE, 0x678874, 0x6F105D):
        e = C.owning_fn(a)
        refs_table, shift9, calls, guarded, stores = scan_fn(e)
        fp = ("T" if refs_table else "-") + ("I" if shift9 else "-") + \
             ("A" if 0x47E8A0 in calls else "-") + ("R" if 0x47EA90 in calls else "-") + \
             ("D" if 0x47D2B0 in calls else "-") + ("G" if guarded else "-")
        print("  site %08X  fn=%s  flags=%s  guarded_cmps=%d" % (
            a, C.fn_label(e), fp, len(guarded)))


main()
