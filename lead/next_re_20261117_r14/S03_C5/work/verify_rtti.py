"""Verify ring ② (RTTI class) for S03 candidates, self-written.
For a given (vt, slot) read vt[slot]==entry, then COL=[vt-4], TD=[COL+0xC], name=cstr(TD+8).
Also do the P3 table-length constraint analysis: scan all image 4-byte hits of entry,
group by candidate vtable base, check which hits survive the table-length constraint.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

# candidates: entry -> (vt, slot, name_from_tsv)
CANDS = {
 "00431F10": (0x7e1668, 5, "CDFileClass::vslot5"),
 "00431F70": (0x7e3a2c, 7, "BufferIOFileClass::vslot7"),
 "00432050": (0x7e1668, 12, "CDFileClass::vslot12"),
 "004322A0": (0x7e1668, 9, "CDFileClass::vslot9"),
 "004325C0": (0x7e1668, 13, "CDFileClass::vslot13"),
 "00473AE0": (0x7e16b0, 12, "CCFileClass::slot12"),
 "00473B10": (0x7e16b0, 9, "CCFileClass::slot9"),
 "00473C00": (0x7e16b0, 11, "CCFileClass::slot11"),
 "00473CE0": (0x7e16b0, 13, "CCFileClass::slot13"),
 "00473FC0": (0x7e16b0, 2, "CCFileClass::slot2"),
 "0047AAB0": (0x7e1668, 7, "CDFileClass::slot7"),
 "0047AE10": (0x7e1668, 2, "CDFileClass::slot2"),
 "0047AF10": (0x7e1668, 8, "CDFileClass::slot8"),
 "0055C7C0": (0x7ed394, 2, "LZOStraw::slot2"),
 "00631D30": (0x7e4d78, 1, "FilePipe::slot1"),
 "0065CB50": (0x7f0904, 7, "RawFileClass::slot7"),
 "0065CCA0": (0x7f0904, 13, "RawFileClass::slot13"),
 "0065CCE0": (0x7f0904, 9, "RawFileClass::slot9"),
 "0065CDD0": (0x7f0904, 12, "RawFileClass::slot12"),
 "0065CF00": (0x7f0904, 10, "RawFileClass::slot10"),
 "0065D0D0": (0x7f0904, 11, "RawFileClass::slot11"),
 "0065D190": (0x7e1668, 4, "CDFileClass::slot4"),
 "0065D1F0": (0x7e1668, 14, "CDFileClass::slot14"),
 "0065D240": (0x7e1668, 15, "CDFileClass::slot15"),
}

def rtti_chain(vt):
    """Read COL/TD/name for a vtable base vt."""
    col = C.u32(vt - 4)
    if col is None:
        return None
    td = C.u32(col + 0xC)
    if td is None:
        return None
    name = C.cstr(td + 8)
    return {"vt": "0x%x" % vt, "col": "0x%x" % col, "td": "0x%x" % td, "name": name}

def scan_all_va_hits(entry_va):
    """Scan entire mapped image for 4-byte little-endian == entry_va (as a vtable slot value)."""
    pe = C.get_pe()
    hits = []
    pat = struct.pack("<I", entry_va)
    data = C._data
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        # map file offset to VA
        rva = None
        for s in pe.sections:
            if s.PointerToRawData <= i < s.PointerToRawData + s.SizeOfRawData:
                rva = s.VirtualAddress + (i - s.PointerToRawData)
                break
        if rva is not None:
            hits.append(C.IMAGE_BASE + rva)
        start = i + 1
    return hits

out = {}
for e, (vt, slot, name) in CANDS.items():
    entry = int(e, 16)
    slotval = C.u32(vt + slot*4)
    chain = rtti_chain(vt)
    ok = (slotval == entry)
    rec = {"entry": e, "tsv_name": name, "vt": "0x%x" % vt, "slot": slot,
           "vt_slot_val": ("0x%x" % slotval) if slotval is not None else None,
           "vt_slot_eq_entry": ok, "chain": chain}
    out[e] = rec
    flag = "OK" if (ok and chain and chain["name"] and chain["name"].startswith(".?A")) else "FAIL"
    nm = chain["name"] if chain else None
    print("%s %s vt=%s slot=%2d slotval=%s chain=%s [%s]" % (
        flag, e, rec["vt"], slot, rec["vt_slot_val"], nm, name))

with open(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "rtti_verify.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("\nwrote EVIDENCE/rtti_verify.json")
