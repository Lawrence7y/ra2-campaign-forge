import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
print("=== 00410320 .. 004103e0 linear ===")
for ins in b.dis(0x410320, 0x60):
    print(f(ins))
print("\n=== 00410380 (claim: empty stream, 90B) ===")
for ins in b.dis(0x410380, 0x30):
    print(f(ins))
