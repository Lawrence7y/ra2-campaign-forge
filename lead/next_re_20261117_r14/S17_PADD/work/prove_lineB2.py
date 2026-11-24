"""Full fixed-window bodies + direct E8 call counts for Line B slotN candidates."""
import re_lib as R

CANDS = {
    "004A2990": ("CStreamClass::slot0 (QueryInterface?)", 0x004A2990),
    "004A2A20": ("CStreamClass::slot3 (Read?)", 0x004A2A20),
    "004A2CD0": ("CStreamClass::slot4 (Write?)", 0x004A2CD0),
    "006CF430": ("SwizzleManagerClass::slot0 (QueryInterface?)", 0x006CF430),
}

for key, (label, va) in CANDS.items():
    print("=" * 100)
    print("[%s] %s @ 0x%08X" % (key, label, va))
    b = R.read_bytes(va, 0x120)
    print("bytes:", b.hex() if b else None)
    # full disasm of fixed window (do not stop at ret)
    for a, mn, op, sz, bh in R.disasm(va, 0x120):
        print("  %08X  %-20s %-8s %s" % (a, bh, mn, op))
    tv, ts, _ = R.TEXT
    bnd = sorted(set(s for s, t in R.sweep_e8_boundary(tv, tv+ts) if t == va))
    raw = sorted(set(s for s, t in R.sweep_e8(tv, tv+ts) if t == va))
    print("  DIRECT E8 calls (boundary): %d  raw: %d  first=%s" % (
        len(bnd), len(raw), [hex(x) for x in bnd[:6]]))
