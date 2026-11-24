import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
E = 0x0069EE30
print("=== bytes at entry ===")
print(b.hexat(E, 128))
print("\n=== disasm from entry ===")
ins = b.dis(E, 45)
for i in ins:
    print(f(i))
print("\nfunc_back:", hex(b.func_back(E) or 0))
print("\n=== 0055A9B0 (claimed base QI) ===")
for i in b.dis(0x55A9B0, 60):
    print(f(i))
