from core import *

def show(lo, hi, title):
    print("=== %s [%08X,%08X) ===" % (title, lo, hi))
    for l in dis_lines(lo, hi):
        print(l)
    print()

# find backward padding before 007471BF to locate host function head
print("=== bytes 00747040..007471C0 (find function head / padding) ===")
raw = read(0x00747040, 0x180)
for off in range(0, len(raw), 16):
    va = 0x00747040 + off
    print("%08X  %s" % (va, raw[off:off + 16].hex(" ")))
print()
show(0x00747080, 0x00747200, "region A linear")
