import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
print("=== full 00410320..00410440 ===")
ins = b.func(0x410320, maxbytes=0x140)
print(show(ins))
print("n =", len(ins), "start", hex(b.func_back(0x410375) or 0))

print("\n=== adjacent: 00410300 / 00410310 / 00410450 (siblings) ===")
for a in (0x410300, 0x410310, 0x4103e0, 0x410450, 0x410470):
    print(f"-- {a:08X}")
    print(show(b.func(a, maxbytes=0x60), "    "))

print("\n=== bytes at 007F4348..007F4358 ===")
print(b.hexat(0x7F4340, 0x30))

print("\n=== who else references 00410320 (callers) ===")
print([hex(x) for x in b.callers_of(0x410320)][:40])
