"""RTTI + holder-table + direct-call evidence for 006CF240 (Line C)."""
import re_lib as R

ENTRY = 0x006CF240
print("=== holders of 006CF240 (raw dword scan) ===")
for h in R.holder_scan(ENTRY):
    print(f"  holder dword @ 0x{h:08X}")
    # try candidate vtable bases: holder - k*4 for k=0..15, check RTTI COL just below
    for k in range(0, 17):
        vt = h - k * 4
        col = R.read_u32(vt - 4)
        if col is None:
            continue
        td = R.read_u32(col + 0xC)
        if td is None:
            continue
        nm = R.read_cstr(td + 8)
        if nm and (".?AV" in nm or ".?AU" in nm):
            print(f"    vt candidate 0x{vt:08X}: slot {k} -> COL 0x{col:08X} TD 0x{td:08X} name {nm!r}")
            print(f"    verify vt[{k}] = 0x{R.read_u32(vt + k*4):08X}")

print("\n=== direct E8 call sites to 006CF240 (boundary-validated) ===")
tv, tsize, tp = R.TEXT
sites = []
for site, target in R.sweep_e8_boundary(tv, tv + tsize):
    if target == ENTRY:
        sites.append(site)
for s in sites:
    # print 24 bytes around call and check self-loop (entry not inside caller body roughly)
    b = R.read_bytes(s - 6, 16)
    ins = R.disasm(s - 6, 16)
    print(f"  site 0x{s:08X}  target=0x{target:08X}  bytes {b.hex() if b else None}")
    for a, mn, op, sz, bh in ins:
        print(f"      {a:08X} {bh:<16} {mn:<8} {op}")

print("\n=== raw E8 byte hits to 006CF240 (count) ===")
raw = [s for s, t in R.sweep_e8(tv, tv + tsize) if t == ENTRY]
print("  raw hits:", [hex(s) for s in raw])
