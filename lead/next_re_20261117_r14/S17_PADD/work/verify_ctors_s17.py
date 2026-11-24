"""Verify enclosing functions of CStreamClass vtable install sites (ring 4 live constructor check)."""
import re_lib as R

TAB = chr(9)
atlas = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
lines = open(atlas, "r", encoding="utf-8", errors="replace").read().splitlines()
funcs = []
for ln in lines[1:]:
    c = ln.split(TAB)
    if len(c) >= 2:
        try:
            funcs.append((int(c[0], 16), int(c[1], 10)))
        except ValueError:
            pass
funcs.sort()

def enclosing(va):
    best = None
    for e, sz in funcs:
        if e <= va < e + sz:
            best = (e, sz)
    return best

for site in [0x4a285e, 0x4a2889, 0x4a3119]:
    enc = enclosing(site)
    print("install site 0x%08X enclosing func=%s" % (
        site, ("0x%08X size 0x%X" % enc) if enc else "NOT IN ATLAS"))
    if enc:
        e, sz = enc
        print("  first 40 instructions of ctor:")
        for a, mn, op, bs, bh in R.disasm(e, min(sz, 0x200)):
            print("    %08X %-16s %-7s %s" % (a, bh, mn, op))
        print()

# Check atexit registrations referencing these ctor entries
print("=== atexit (call 0x7C978A) sites whose pushed arg matches a ctor entry ===")
tv, ts, _ = R.TEXT
ctor_entries = [0x4a2800, 0x4a2880, 0x4a3100]
for site, target in R.sweep_e8_boundary(tv, tv+ts):
    if target != 0x7C978A:
        continue
    b = R.read_bytes(site-12, 12)
    dis = R.disasm(site-12, 12)
    txt = " | ".join("%X:%s %s" % (a, m, o) for a, m, o, s, h in dis)
    print("  atexit call @0x%08X: %s bytes=%s" % (site, txt, b.hex() if b else None))
