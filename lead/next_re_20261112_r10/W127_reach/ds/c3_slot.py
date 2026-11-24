"""C3 part 3: resolve the RTTI properly.

Key facts to establish:
 - 0x7F1094 IS a vtable start (preceded by COL ptr 0x809060, and the code-ptr
   run cannot extend backwards: 0x7F1090 is in .rdata, not a code ptr).
 - COL 0x809060 layout read from bytes:
       +0x00 00000000
       +0x04 00000000
       +0x08 00000000
       +0x0C 00816C70   <- points at the TypeDescriptor (not a sig)
       +0x10 00809050   <- self-referencing COL (pSelf)
       +0x14 00000000
   So this is the VC6-style COL: {sig, offset, cdOffset, pTD, pSelf, ...}
   with sig/offset/cdOffset all zero, and the COL POINTER stored at vt-4 is
   actually 0x809050 (the 'single inheritance' COL) not 0x809060.
   CHECK: u32(0x7F1090) = 0x809060. 0x809060+0x10 == 0x809050? no: 0x809050.
   Let's verify by reading 0x809050 too.
 - TD 0x816C70: +0x00 vftable 0x7F9594, +0x04 spare, +0x08 name ptr 0x816C78
   -> '.?AVScrollClass@@'   (CONFIRMED: the name lives at 0x816C78 in .data)
"""
from base import BUF, IB, u32, s32, cstr, in_raw, blob

def show(va, n, label):
    print("  %-22s @%08X n=%d raw=%s  %s" % (label, va, n, in_raw(va, n), blob(va, n).hex()))

print("=== 1. TypeDescriptor for ScrollClass ===")
td = 0x00816C70
show(td, 0x10, "TD")
print("   TD+0x00 vftable  = %08X" % u32(td))
print("   TD+0x04 spare    = %08X" % u32(td + 4))
print("   TD+0x08 name ptr = %08X -> %r" % (u32(td + 8), cstr(u32(td + 8), 40)))
print("   type_info vftable %08X is in .rdata? %s" % (u32(td), 0x007E1000 <= u32(td) < 0x00811074))

print()
print("=== 2. COL chain: what is at vt-4 and around 0x809050 / 0x809060 ===")
vt = 0x007F1094
print("   u32(vt-4)=u32(%08X) = %08X" % (vt - 4, u32(vt - 4)))
for a in (0x00809040, 0x00809050, 0x00809060):
    show(a, 0x18, "COL?")
    print("     dwords: " + " ".join("%08X" % u32(a + i) for i in (0, 4, 8, 0xC, 0x10, 0x14)))
print()
print("   which COL points at TD 0x816C70?")
for col in (0x00809050, 0x00809060):
    vals = [u32(col + i) for i in (0, 4, 8, 0xC, 0x10, 0x14)]
    hit = [i for i, v in enumerate(vals) if v == td]
    print("     COL %08X: TD match at offset(s) %s" % (col, [hex(i * 4) for i in hit]))

print()
print("=== 3. so the vtable's COL pointer is 0x809060; its pTD is at +0x0C ===")
print("   RTTI chain CONFIRMED:")
print("     vt       = %08X" % vt)
print("     [vt-4]   = %08X  (COL)" % u32(vt - 4))
print("     COL+0x0C = %08X  (pTypeDescriptor)" % u32(u32(vt - 4) + 0xC))
print("     TD+0x08  = %08X  -> %r" % (u32(td + 8), cstr(u32(td + 8), 40)))
print("   NOTE: the COL at 0x809060 has a self-pointer at +0x10 == 0x809050,")
print("   i.e. the actual COL struct begins at 0x809050 and 0x809060 is the")
print("   'vt-4 stored value'. Verify both readings are consistent.")
print("     u32(0x809060+0x10) = %08X" % u32(0x809060 + 0x10))
print("     if COL base were 0x809050: pTD at +0x0C = %08X  (name %r)" %
      (u32(0x00809050 + 0xC), cstr(u32(u32(0x00809050 + 0xC) + 8), 40) if in_raw(u32(0x00809050 + 0xC), 0x10) else None))

print()
print("=== 4. slot numbering: 0x7F10BC within table starting 0x7F1094 ===")
print("   (0x7F10BC - 0x7F1094)/4 = %d" % ((0x7F10BC - 0x7F1094) // 4))
print("   entry at that index = %08X" % u32(0x007F10BC))

print()
print("=== 5. is 0x006922E0 a real function body or an adjustor thunk? ===")
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
print("   raw bytes @0x006922E0: %s" % blob(0x006922E0, 24).hex())
for ins in md.disasm(blob(0x006922E0, 32), 0x006922E0):
    print("     %08X  %-16s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    if ins.mnemonic in ("ret",):
        break
