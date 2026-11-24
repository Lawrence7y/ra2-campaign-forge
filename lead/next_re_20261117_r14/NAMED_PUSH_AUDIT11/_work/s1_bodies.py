import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]

print("SHA", SHA, "ImageBase", hex(IMAGEBASE))
for n in SECTIONS:
    print(f"  sec {n[0]:<10} va={n[1]:#010x} vsz={n[2]:#x} rawsz={n[3]:#x} raw={n[4]:#x}")

for e in ENTRIES:
    va = int(e, 16)
    print("=" * 100)
    print(f"ENTRY {e}  section={sec_of(va)[0]}  bytes={hexs(va, 16)}")
    ins = dis(va, 200)
    for i in ins:
        print("   " + fmt(i))
