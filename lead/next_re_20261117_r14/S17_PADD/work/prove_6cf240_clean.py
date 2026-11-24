"""Clean RTTI/holder + direct-call count for 006CF240 (Line C)."""
import re_lib as R

ENTRY = 0x006CF240
print("=== holders of 006CF240 (raw dword scan across mapped file bytes) ===")
for h in R.holder_scan(ENTRY):
    print(f"  holder dword @ 0x{h:08X}")
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
            print(f"    vt=0x{vt:08X} slot={k} (+0x{k*4:X}) COL=0x{col:08X} TD=0x{td:08X} name={nm!r}")
            print(f"    verify vt[{k}]=0x{R.read_u32(vt+k*4):08X}  (entry=0x{ENTRY:08X})")

tv, tsize, tp = R.TEXT
bnd = sorted(set(s for s, t in R.sweep_e8_boundary(tv, tv+tsize) if t == ENTRY))
raw = sorted(set(s for s, t in R.sweep_e8(tv, tv+tsize) if t == ENTRY))
print(f"\nboundary-valid direct call sites to 0x{ENTRY:08X}: {len(bnd)}")
print("first 8:", [hex(s) for s in bnd[:8]])
print("raw E8-byte hits:", len(raw))
# self-loop check: none of the sites are inside [entry, entry+0x74]
inbody = [s for s in bnd if ENTRY <= s < ENTRY + 0x74]
print("self-loop sites (inside body):", [hex(s) for s in inbody])
