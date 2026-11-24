import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

print("=== SECTIONS ===")
for s in R.BIN.sections:
    print(f"  {s['name']:<8} va={s['va']:08X} vsize={s['vsize']:08X} raw={s['raw']:08X} rawsize={s['rawsize']:08X}")

def raw_read(va, n):
    for s in R.BIN.sections:
        if s["va"] <= va < s["va"] + s["vsize"]:
            off = s["raw"] + (va - s["va"])
            if off + n <= s["raw"] + s["rawsize"]:
                return R.BIN.pe.__data__[off:off+n]
    return None

print("=== vtable 0x7e4a28 region (raw) ===")
b = raw_read(0x7E4A00, 0x80)
if b:
    for i in range(0, len(b), 4):
        import struct
        v = struct.unpack("<I", b[i:i+4])[0]
        print(f"  {0x7E4A00+i:08X}: {v:08X}")

print("=== COL / TD chain for vptr 0x7e4a28 ===")
for vt in [0x7e4a28]:
    col = R.u32(vt-4)
    print(f"vptr {vt:08X} -> COL {col:08X}")
    if 0x400000 < col < 0x900000:
        sig = R.u32(col)
        off = R.u32(col+4)
        cd = R.u32(col+8)
        td = R.u32(col+0xC)
        print(f"  COL sig={sig:08X} off={off:08X} cd={cd:08X} TD={td:08X}")
        if 0x400000 < td < 0x900000:
            # TD+8 inline name (x86)
            try:
                name = R.cstr(td+8, 100)
                print(f"  TD+8 name = {name!r}")
            except Exception as e:
                print("  name err", e)

print("=== raw at 0x887734 ===")
b = raw_read(0x887734, 0x40)
print(b.hex() if b else "NOT IN RAW")
