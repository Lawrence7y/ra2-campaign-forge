from base import BUF, IB, u32, cstr, in_raw, blob
print("=== TD 0x816C70 raw dump, byte by byte ===")
raw = blob(0x00816C70, 0x18)
print("  ", raw.hex(), "  (%r)" % raw)
print()
print("=== TD 0x816C58 raw dump ===")
print("  ", blob(0x00816C58, 0x18).hex())
print()
print("=== find the name pointer: which dword in TD == 0x816C78 ? ===")
for td in (0x00816C70, 0x00816C58):
    for off in range(0, 0x18, 4):
        v = u32(td + off)
        if v == 0x00816C78 or v == 0x00816C60:
            print("  TD %08X + 0x%02X = %08X  <-- name pointer" % (td, off, v))
print()
print("=== the exact bytes at the name ===")
print("  0x816C78:", blob(0x00816C78, 32), cstr(0x00816C78, 40))
print("  0x816C60:", blob(0x00816C60, 32), cstr(0x00816C60, 40))
print()
print("=== so TD layout: name is at TD+0x0C, NOT TD+0x08 ===")
for td in (0x00816C70, 0x00816C58):
    print("  TD %08X: +0x00=%08X +0x04=%08X +0x08=%08X +0x0C=%08X" %
          (td, u32(td), u32(td+4), u32(td+8), u32(td+0xC)))
    print("           name ->", cstr(u32(td+0xC), 40) if in_raw(u32(td+0xC),4) else None)
