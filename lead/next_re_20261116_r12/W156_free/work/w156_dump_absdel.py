"""Dump context around 0x4F5EFC (write to AbstractClass::Array.Count) and 0x43BB72."""
import w156_core as C
print("=== 0x4F54A0 around the Count write 0x4F5EFC ===")
for ins in C.disas_range(0x4F5E80, 0xA0):
    print("  " + C.fmt(ins))
