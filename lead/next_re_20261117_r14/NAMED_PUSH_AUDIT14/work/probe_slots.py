import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n"+"="*72); print(t); print("="*72)

sec("DropPod MAIN vtable 0x7E8344 slot layout (slot6 @ +0x18 = 0x7E835C)")
for i in range(9):
    a = 0x7E8344 + i*4
    print(f"  slot{i} @{a:08X} = 0x{u32(a):08X}")
print(">>> slot6 expected 0x004B62C0, actual:", hex(u32(0x7E835C)))

sec("Drive MAIN vtable 0x7E7F7C first 3 slots")
for i in range(3):
    a=0x7E7F7C+i*4; print(f"  slot{i} @{a:08X} = 0x{u32(a):08X}")
sec("Jumpjet MAIN vtable 0x7ECE34 first 3 slots")
for i in range(3):
    a=0x7ECE34+i*4; print(f"  slot{i} @{a:08X} = 0x{u32(a):08X}")

sec("first-slot first-6-bytes of each MAIN table (expect 53 8b 5c 24 08 55 = real fn)")
for vt in [0x7E7F7C,0x7E8344,0x7ECE34]:
    tgt=u32(vt)
    print(f"  main {vt:08X} slot0 -> {tgt:08X}: {hexb(tgt,6)}")
