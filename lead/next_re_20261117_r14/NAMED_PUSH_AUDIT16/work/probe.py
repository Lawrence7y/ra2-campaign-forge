"""Per-entry probes: function extent, vtable occurrences of entry, RTTI chain."""
import sys
from pe import (BY_ADDR, ORDER, TEXT_LO, TEXT_HI, u32, read, cstr, ins_at,
                find_imm32_occurrences, rtti_of_table, slots_of_table, fmt)


def func_extent(entry, cap=3000):
    """Linear walk from entry until a terminator (ret / unconditional jmp to far / int3 pad)."""
    a = entry
    out = []
    pad = 0
    while a < TEXT_HI and len(out) < cap:
        i = BY_ADDR.get(a)
        if i is None:
            # unmatched byte
            out.append(None)
            a += 1
            continue
        out.append(i)
        a += i.size
        pad = pad + 1 if i.mnemonic in ("int3", "nop") else 0
        if i.mnemonic in ("ret", "retf") or i.mnemonic.startswith("ret"):
            break
        if pad >= 4:
            break
    return out


def tables_containing(value):
    """Every position where `value` appears as an aligned 4-byte code pointer that could be a vtable slot."""
    res = []
    for pos in find_imm32_occurrences(value):
        # try every base <= pos such that (pos-base)%4==0, base-4 readable, [base-4] a plausible COL
        for back in range(0, 4 * 64, 4):
            base = pos - back
            if base < 0x400000:
                continue
            col = u32(base - 4)
            if col is None or not (0x400000 <= col < 0x400000 + 0x400000):
                continue
            sig = u32(col)
            if sig != 0:
                continue
            td = u32(col + 0xC)
            if td is None or not (0x400000 <= td < 0x400000 + 0x400000):
                continue
            nm = td + 8
            name = cstr(nm, 300)
            if not name.startswith(".?"):
                continue
            res.append(dict(slotpos=pos, base=base, slot=back // 4, col=col, td=td,
                            name_ptr=nm, name=name))
            break
    return res


def report(entry):
    print("=" * 78)
    print("ENTRY %08X" % entry)
    ins = func_extent(entry)
    real = [i for i in ins if i]
    print("  extent: %d insns, %08X..%08X, ends on %s" % (
        len(real), entry, real[-1].address, real[-1].mnemonic if real else "?"))
    print("  --- tables containing entry (as aligned slot) ---")
    tabs = tables_containing(entry)
    if not tabs:
        print("    NONE")
    for t in tabs:
        slots = slots_of_table(t["base"])
        print("    slotpos=%08X base=%08X slot=%d/%d slotlen=%d" % (
            t["slotpos"], t["base"], t["slot"], len(slots), len(slots)))
        print("      COL=%08X sig=%s TD=%08X name=%s" % (
            t["col"], hex(u32(t["col"])), t["td"], t["name"]))
    print("  --- calls in body ---")
    for i in real:
        if i.mnemonic == "call":
            print("     " + fmt(i))
    print("  --- body ---")
    for i in real:
        print("   " + fmt(i))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        report(int(a, 16))
