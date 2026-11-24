from base import pe, IB, u32, cstr, in_raw, blob, DATA, RDATA
print("=== .data section: PointerToRawData vs VirtualAddress ===")
print("  .data VA=%08X rawptr=%08X rawsize=%08X" % (DATA["va"], DATA["rawptr"], DATA["rawsize"]))
print("  => file_off = VA - %08X + %08X  (delta %d)" % (DATA["va"], DATA["rawptr"], DATA["rawptr"] - DATA["va"]))
print("  => the string at FILE OFFSET 0x816C78 lives at VA %08X" %
      (0x00816C78 + (DATA["rawptr"] - DATA["va"])))
print()
print("=== TypeDescriptor decoding using the CORRECT VA ===")
# the TD name string was found at file offset 0x816C78; convert to VA
va_name = 0x00816C78 + (DATA["rawptr"] - DATA["va"])
print("  name VA = %08X -> %r" % (va_name, cstr(va_name, 40)))
# data directory walk: pTD from COL 0x809060
col = 0x00809060
td = u32(col + 0xC)
print("  COL %08X +0x0C = %08X (pTD)" % (col, td))
print("  TD raw %08X: %s" % (td, blob(td, 0x10).hex()))
print("  TD+0x00 = %08X (type_info vftable)" % u32(td))
print("  TD+0x04 = %08X" % u32(td+4))
print("  TD+0x08 = %08X" % u32(td+8))
print("  TD+0x08 -> %r" % cstr(u32(td+8), 40) if in_raw(u32(td+8),4) else "n/a")
print()
print("  VERDICT: TD+0x08 = %08X and the bytes there are %r" %
      (u32(td+8), cstr(u32(td+8), 40)))
