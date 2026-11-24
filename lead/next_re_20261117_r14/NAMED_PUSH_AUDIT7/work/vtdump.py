"""AUDIT7: dump candidate container vtables side by side (slots + RTTI)."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *

VTS = [0x007E9D64, 0x007E9D84, 0x007EA464, 0x007EA484, 0x007EA424, 0x007EA444,
       0x007E91EC, 0x007E920C, 0x007EA3A4, 0x007EA3C4]

for vt in VTS:
    r = rtti_of_vtable(vt)
    print(f"\n=== vtable {vt:08X}  RTTI col={r['col'] and hex(r['col'])} td={r['td'] and hex(r['td'])} name={r['name']!r}")
    for i in range(10):
        v = u32(vt + 4 * i)
        mark = ''
        if v and in_text(v):
            b = fast_body = None
            mark = ''
        print(f"   +{i*4:#04x} slot#{i}: {v and f'{v:08X}'}")
