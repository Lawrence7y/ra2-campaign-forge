from pehelp import *
sec = next(s for s in SECTIONS if s[4] == '.rdata')
v, vs, raw, rs, _ = sec
data = pe.get_data(raw, rs)
for nm in [b'CellClass', b'MapClass', b'Cell', b'Map']:
    print(f"=== search {nm} in .rdata ===")
    idx = data.find(nm)
    cnt = 0
    while idx != -1 and cnt < 30:
        va = v + idx
        # print surrounding printable
        lo = max(0, idx - 24); hi = min(rs, idx + 40)
        snippet = data[lo:hi]
        printable = ''.join(chr(c) if 32 <= c < 127 else '.' for c in snippet)
        print(f"  {va:#x}: {printable}")
        idx = data.find(nm, idx + 1); cnt += 1
    print("  count shown:", cnt)
