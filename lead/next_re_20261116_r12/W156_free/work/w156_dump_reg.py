"""Dump the building-array registration code in constructor 0x43B740 and the NOFUNC init/clear funcs."""
import w156_core as C

print("=== ctor 0x43B740 registration region 0x43BAC0..0x43BB60 ===")
for ins in C.disas_range(0x43BAC0, 0xA0):
    print("  " + C.fmt(ins))

print("\n=== NOFUNC init 0x4E6B60..0x4E6B9D ===")
for ins in C.disas_range(0x4E6B60, 0x40):
    print("  " + C.fmt(ins))

print("\n=== NOFUNC clear 0x4E6BA0..0x4E6BDC ===")
for ins in C.disas_range(0x4E6BA0, 0x40):
    print("  " + C.fmt(ins))
