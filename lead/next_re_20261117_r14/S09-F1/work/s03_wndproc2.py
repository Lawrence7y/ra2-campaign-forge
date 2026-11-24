"""S09-F1 recon 03: WndProc msg tables + registration + input pump + PushWord."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()

print("=== WndProc jump table @ 0x54FB64 (WM 0x202..0x209) ===")
for i in range(8):
    print("  msg %04X -> %08X" % (0x202+i, b.u32(0x54FB64+i*4)))

print("\n=== WndProc code 0x54F950..0x54FB4C ===")
print(dump(b, 0x54F950, 0x1FC))

print("\n=== WndProc common exit 0x54FB18..0x54FB4C ===")
print(dump(b, 0x54FB18, 0x34))

print("\n=== RegisterClassA call site @ 0x777CA5 (context) ===")
print(dump(b, 0x777C50, 0x110))

print("\n=== input pump PeekMessageA @ 0x53EB16 context ===")
print(dump(b, 0x53EAC0, 0x110))

print("\n=== DispatchMessageA @ 0x53E8A1 context ===")
print(dump(b, 0x53E860, 0x80))

print("\n=== PushWord 0x54F1C0 ===")
print(dump(b, 0x54F1C0, 0x90))
print("\n=== PushWord helper 0x54F200 ===")
print(dump(b, 0x54F200, 0x100))
