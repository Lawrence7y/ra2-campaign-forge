import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
for a in (0x410170, 0x4101c0, 0x4101f0, 0x410260):
    print(f"=== {a:08X} ===")
    print(show(b.dis(a, 14)))
print("=== 006D1E80 (dtor?) callers/push ===")
print("callers:", [hex(x) for x in b.callers_of(0x6D1E80)])
print("push sites:", [hex(x) for x in b.push_sites(0x6D1E80)])
print("=== 006D1E30 (copy ctor?) callers ===")
print([hex(x) for x in b.callers_of(0x6D1E30)])
print("push sites:", [hex(x) for x in b.push_sites(0x6D1E30)])
print("\n=== ATEXIT helper 7C978A ===")
print(show(b.dis(0x7C978A, 5)))
print("=== does anything push 006D1C20 and call 7C978A? (checked) ===")
