import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
E = 0x006DBE00
print("=== entry bytes ===")
print(b.hexat(E, 96))
print("\n=== linear disasm from entry ===")
print(show(b.func(E, maxbytes=0x200)))
print("\n=== func_start ===", hex(b.func_back(E) or 0))
print("\n=== caller 006D1D54 region (ctor claim) ===")
print(show(b.dis(0x006D1D20, 30)))
