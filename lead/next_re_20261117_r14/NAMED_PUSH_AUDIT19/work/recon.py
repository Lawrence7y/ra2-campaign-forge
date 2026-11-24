"""Generic per-entry recon: vtables holding entry, RTTI, write points, callers, body."""
import sys
from re_lib import Bin, IMAGEBASE, TEXT_LO, TEXT_HI, fmt_ins

def analyze(b, entry, body_size=320):
    print("=" * 100)
    print(f"ENTRY {entry:08X}   section={b.secname(entry)}")
    print("=" * 100)

    # ---- 1. occurrences of entry as dword anywhere ----
    occ = b.find_imm32(entry)
    print(f"[A] entry 作为 4 字节值出现 {len(occ)} 次:")
    cands = []
    for va in occ:
        sec = b.secname(va)
        pre = b.u32(va - 4) if va >= 4 else None
        rt = b.rtti_from_vt(va - 4) if (pre is not None and IMAGEBASE <= (pre or 0) < 0xC00000) else None
        name = rt["name"] if rt else None
        print(f"   @{va:08X} ({sec}) preceding dword={pre!r} -> name={name!r}")
        if name:
            vt = va - 4
            slots = b.slot_of(vt, entry)
            cands.append((vt, va, rt, slots))
    print()

    # ---- 2. per candidate vtable: dump + write points ----
    for vt, slotaddr, rt, slots in cands:
        print(f"[B] vtable {vt:08X}  COL={rt['col']:08X} sig={rt.get('sig')} pTD={rt['pTD']:#x} pCHD={rt['pchd']:#x}")
        print(f"    name={rt['name']!r}  slot(s) whose value==entry: {slots}  (slotaddr {(vt+4*slots[0]):08X})")
        print(f"    vt[0]={b.u32(vt):08X} vt[1]={b.u32(vt+4):08X} vt[2]={b.u32(vt+8):08X}")
        print(f"    TD+8 u32={rt['td_u32_at_8']:#x}  TD+8 str={b.cstr(rt['pTD']+8)!r}")
        print(f"    vt dump (first 14):")
        for i, v in b.vt_dump(vt, 14):
            mark = "  <== entry" if v == entry else ""
            print(f"      slot{i:2d} (+0x{4*i:02X})  {v if v is None else format(v,'08X')}{mark}")
        # write points
        w = b.vt_writers(vt)
        print(f"    [C] 全镜像 imm32==vt 写点 {len(w)} 处:")
        for rec in w:
            print(f"      imm@{rec['imm_at']:08X}  ins@{rec['ins_va'] if rec['ins_va'] is not None else 0:08X}  {rec['text']}   bytes[{rec['bytes']}]")
        print()

    # ---- 3. direct callers ----
    cs = b.callers_direct(entry)
    print(f"[D] direct callers (E8, site+5+rel32==entry): {len(cs)} -> {[f'{x:08X}' for x in cs]}")
    # also push/jmp refs
    for va in occ:
        ins = b.containing_instr(va)
        print(f"    value@{va:08X} in ins: {fmt_ins(ins)}")

    # ---- 4. body ----
    print(f"\n[E] body from {entry:08X} ({body_size} bytes):")
    for ins in b.func(entry, body_size):
        print("   ", fmt_ins(ins))


if __name__ == "__main__":
    b = Bin()
    for a in sys.argv[1:]:
        analyze(b, int(a, 16))
