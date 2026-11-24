import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
TACT = 0x007F4348
print("=== Tactical main vtable slots 0..14 ===")
for i in range(15):
    v = b.u32(TACT + 4 * i)
    print(f"  slot {i:2d} (+{i*4:#04x}) = {v and format(v,'08X')}  {b.hexat(TACT+4*i,4)}")
print("\n=== slot5 = 006DBD20 (claimed Load?) ===")
print(show(b.dis(0x6DBD20, 26)))
print("\n=== slot3 = 006DBCE0 ===")
print(show(b.dis(0x6DBCE0, 10)))
print("\n=== slot7 = 004103E0 ===")
print(show(b.dis(0x4103E0, 14)))
print("\n=== helpers used: who calls 00410380 (Read) ===")
print([hex(x) for x in b.callers_of(0x410380)][:20])
print("=== who calls 00410320 (Write) ===")
print([hex(x) for x in b.callers_of(0x410320)][:20])
