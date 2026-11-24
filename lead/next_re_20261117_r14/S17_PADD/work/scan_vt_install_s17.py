"""Find constructor installs of CStreamClass vtables 0x7E5D94 / 0x7E5DAC (ring 4)."""
import struct
import re_lib as R

VTS = {0x7E5D94: "CStreamClass primary vt (slot3=Read, slot6=QI?)",
       0x7E5DAC: "CStreamClass secondary vt (slot0=QI, slot4=Write?)"}

tv, ts, tp = R.TEXT
blob = R.DATA[R.va_to_off(tv):R.va_to_off(tv)+ts]

for vt, label in VTS.items():
    print("=" * 100)
    print("vtable 0x%08X : %s" % (vt, label))
    needle = struct.pack("<I", vt)
    pos = 0
    hits = []
    while True:
        pos = blob.find(needle, pos)
        if pos < 0:
            break
        site = tv + pos
        hits.append(site)
        pos += 1
    print("  raw occurrences in .text: %d -> %s" % (
        len(hits), [hex(h) for h in hits[:30]]))
    for site in hits[:40]:
        # try to determine instruction: look at bytes from site-6..site+4
        b = R.read_bytes(site - 8, 16)
        dis = R.disasm(site - 8, 16)
        print("    @0x%08X bytes=%s" % (site, b.hex() if b else None))
        for a, mn, op, sz, bh in dis:
            mark = " <-- imm here" if a == site else ""
            print("       %08X %-16s %-8s %s%s" % (a, bh, mn, op, mark))
