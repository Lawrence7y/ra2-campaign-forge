import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()

print("=== base LocomotionClass ctor 0055A6C0 ===")
print(show(b.dis(0x55A6C0, 12)))

print("\n=== ctor caller contexts (operator new?) ===")
for ctor, c, sz in ((0x0069EC50, 0x6C4F4C, 0x70), (0x00718000, 0x6C4C4C, 0x4C), (0x0075AA90, 0x6C47CC, 0x3C)):
    print(f"--- ctor {ctor:08X} caller {c:08X} (expect push {sz:#x})")
    print(show(b.dis(c - 0x24, 16), "    "))

print("\n=== 0069ECF0 region (2nd writer 0069ECF3) ===")
print(show(b.dis(0x69ECE0, 20)))
print("\n=== 0069EE90 (3rd writer 0069EEB3; ship vt slot5) ===")
print(show(b.dis(0x69EE90, 26)))
print("\n=== 006A42B0 (4th writer; ship vt slot8) ===")
print(show(b.dis(0x6A42A8, 14)))
