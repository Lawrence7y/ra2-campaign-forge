from core import *

def show(lo, hi, title):
    print("=== %s [%08X,%08X) ===" % (title, lo, hi))
    for l in dis_lines(lo, hi):
        print(l)
    print()

show(0x004E7450, 0x004E74F0, "container ctor/dtor pair near 004E747F/004E74AA")
print("=== current .data value at 0xA83CE0 (static init) ===")
print("  [0xA83CE0] = %08X" % u32(0xA83CE0))
print("  [0xA83CE4] = %08X" % u32(0xA83CE4))
print("  [0xA83CE8] = %08X" % u32(0xA83CE8))
print("  [0xA83CEC] = %08X" % u32(0xA83CEC))
print("  [0xA83CF0] = %08X" % u32(0xA83CF0))
print("  [0xA83CF4] = %08X" % u32(0xA83CF4))
print()
show(0x00747200, 0x00747270, "ctor add path 00747203..")
