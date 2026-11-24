"""Row engine v2: table/slot + RTTI chain + every .text site that materialises a table VA.

Site discovery is done on raw bytes (dword occurrences inside .text), then verified by
disassembling a small window and checking that some instruction's immediate == the VA.
"""
import sys
from pe import (BY_ADDR, TEXT_LO, TEXT_HI, u32, read, cstr, fmt, MD2,
                find_imm32_occurrences, rtti_of_table, slots_of_table)

ROWS = [
    ("004684E0", "BulletClass::slot10", 0x007E46E4),
    ("00629FD0", "ParasiteClass::slot23", 0x007EF890),
    ("0075E0C0", "WarheadTypeClass::slot5", 0x007F6B30),
    ("0075E2C0", "WarheadTypeClass::slot6", 0x007F6B30),
    ("00772CD0", "WeaponTypeClass::slot5", 0x007F73B8),
    ("00772EB0", "WeaponTypeClass::slot6", 0x007F73B8),
]


def insn_containing(occ, value):
    """Find an instruction inside a window around `occ` whose immediate operand == value."""
    lo = occ - 12
    hi = occ + 8
    b = read(lo, hi - lo)
    if b is None:
        return None
    for base in range(lo, occ + 1):
        bb = read(base, 16)
        for i in MD2.disasm(bb, base):
            if i.address == occ:  # imm starts exactly here -> not our instr
                break
            if i.id == 0:          # skipdata pseudo-instruction
                if i.address > occ:
                    break
                continue
            for op in i.operands:
                if op.type == 2 and op.imm == value:
                    return i
            if i.address > occ:
                break
    return None


def sites_for(value, restrict_text=True):
    out = []
    for occ in find_imm32_occurrences(value):
        if restrict_text and not (TEXT_LO <= occ < TEXT_HI):
            if not restrict_text:
                out.append((occ, None))
            continue
        i = insn_containing(occ, value)
        out.append((occ, i))
    return out


def func_extent(entry, cap=4000):
    """Linear walk; stop when reaching a hole of >=8 non-decoded bytes or cap."""
    a = entry
    out = []
    bad = 0
    while a < TEXT_HI and len(out) < cap:
        i = BY_ADDR.get(a)
        if i is None:
            bad += 1
            a += 1
            if bad >= 8:
                break
            continue
        bad = 0
        out.append(i)
        a += i.size
    return out


def main():
    for entry_s, name, vt in ROWS:
        entry = int(entry_s, 16)
        print("=" * 92)
        print("ROW %s   name=%s" % (entry_s, name))
        occ = find_imm32_occurrences(entry)
        print("  [hold-tables] entry as dword at: %s" % ", ".join("%08X" % o for o in occ))
        slots = slots_of_table(vt)
        idxs = [k for k, v in enumerate(slots) if v == entry]
        print("  [table] vt=%08X slotcount=%d ; entry at slot(s)=%s" % (vt, len(slots), idxs))
        for k in idxs:
            print("        mem[%08X] = %08X" % (vt + 4 * k, u32(vt + 4 * k)))
        rt = rtti_of_table(vt)
        print("  [rtti] [vt-4]=COL=%08X sig=%s ; [COL+0xC]=TD=%08X ; name@TD+8=%s -> %r" % (
            rt.get("col") or 0, rt.get("col_sig"), rt.get("td") or 0,
            "%08X" % (rt.get("name_at") or 0), rt.get("name")))
        print("  [rtti-raw TD] %s" % (read(rt.get("td") or 0, 40).hex() if rt.get("td") else None))
        print("  [sites] every dword occurrence of %08X in whole image:" % vt)
        for o in find_imm32_occurrences(vt):
            where = "TEXT" if TEXT_LO <= o < TEXT_HI else "DATA"
            i = insn_containing(o, vt) if where == "TEXT" else None
            print("     %s %08X  %s" % (where, o, (fmt(i) if i else "(not an imm operand / data)")))
        print()


if __name__ == "__main__":
    main()
