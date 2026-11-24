"""S10: instruction ORDER around the placement latch inside the functions that
BOTH call slot 73 (mode 0) AND write [obj+0x74] directly.

If such a function writes [obj+0x74]=0 *before* the slot-73 mode-0 call, the
detach is a guaranteed no-op (0x5F5850 returns 0), so the cell chain is never
cleaned -> a real bypass path.

Run: python s10_order.py > ..\\EVIDENCE\\s10_order.log 2>&1
"""
import capstone
import w152_core as C

X = capstone.x86

# (function entry, interesting store addresses inside it)
TARGETS = [
    (0x004B0F20, [0x4B1A5D, 0x4B1A74, 0x4B1A8B, 0x4B1AA8]),
    (0x00514310, [0x5149FA, 0x514A1E]),
    (0x00543330, [0x543727]),
    (0x0054BA30, [0x54BB46, 0x54BB7D, 0x54BD23]),
    (0x0054BD30, [0x54BE22, 0x54BE8A, 0x54BFD4]),
    (0x0054BFF0, [0x54C18C, 0x54C1A3, 0x54C2C5, 0x54C373]),
    (0x0054C550, [0x54C60D, 0x54C645]),
    (0x0054D0F0, [0x54D134, 0x54D6BD]),
    (0x00581140, [0x5811F8, 0x5811FF, 0x5818E0, 0x5818E7]),
    (0x005F3900, [0x5F392A, 0x5F394B, 0x5F3951]),
    (0x0065EC30, [0x65ECD8]),
    (0x006A05F0, [0x6A109F, 0x6A10B6, 0x6A10CD, 0x6A10E7]),
    (0x006B4BE0, [0x6B4C4E]),
    (0x006E8A90, [0x6E8AF0, 0x6E8B14, 0x6E8B1A]),
]

WINDOW = 26


def is_slot124(ins):
    if ins.mnemonic != "call" or not ins.operands:
        return None
    o = ins.operands[0]
    if o.type == X.X86_OP_MEM and o.mem.disp == 0x124 and o.mem.index == 0:
        return o.mem.base and ins.reg_name(o.mem.base)
    return None


def main():
    for entry, stores in TARGETS:
        inss = C.disas_fn(entry)
        if not inss:
            print("!! no decode for %08X" % entry)
            continue
        idx = {ins.address: i for i, ins in enumerate(inss)}
        slot_sites = [(i, ins) for i, ins in enumerate(inss) if is_slot124(ins)]
        print("=" * 78)
        print("=== fn %s  instructions=%d  slot73 sites=%d ===" % (
            C.fn_label(entry), len(inss), len(slot_sites)))
        for st in stores:
            if st not in idx:
                print("   store %08X NOT on a decoded boundary" % st)
                continue
            i = idx[st]
            print("   ---- store %08X at insn#%d ; slot73 sites=%s" % (
                st, i, [("%08X" % s.address) for _, s in slot_sites] or "NONE"))
            lo, hi = max(0, i - WINDOW), min(len(inss), i + WINDOW)
            for j in range(lo, hi):
                mark = "  <<=== STORE" if inss[j].address == st else ""
                s = is_slot124(inss[j])
                if s:
                    mark += "  <<=== SLOT73"
                print("     " + C.fmt(inss[j]) + mark)
            print("")


main()
