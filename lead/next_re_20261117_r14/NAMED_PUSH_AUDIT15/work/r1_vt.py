import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

VT = 0x007F794C
SLOT_OFF = 0x3C
va = 0x007B10C0

print("=== 1) vt slot check ===")
print(f"vt={VT:08X} slot_off={SLOT_OFF:#x} slot_addr={VT+SLOT_OFF:08X}")
for off in range(-8, 0x60, 4):
    a = VT+off
    v = u32(a)
    mark = ""
    if off == SLOT_OFF: mark = "   <<< claimed slot"
    if v == va: mark += "   [== entry]"
    print(f"  vt{off:+#05x} @{a:08X} = {v:08X}{mark}")

print()
print("=== 2) COL / RTTI ===")
col_ptr = u32(VT-4)
print(f"[vt-4] @{VT-4:08X} = {col_ptr:08X}")
if is_va(col_ptr):
    r = print_col(VT)

print()
print("=== 3) alt vtable candidates: who else has COL pointing to same TD? ===")
