import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### factory slot0 = 006C2A50 (QI?) full")
for i in dis(0x6C2A50, 130):
    print("   " + fmt(i))
    if i.mnemonic.startswith("ret"):
        break
print()
print("### imm refs inside 006C2A50..006C2AC0 (IIDs?)")
for i in dis(0x6C2A50, 130):
    if i.mnemonic in ("cmp", "mov") and "0x" in i.op_str:
        print("   " + fmt(i))
print()
print("### 0041CFFE.. object deleting dtor 0041CFE0 tail")
for i in dis(0x41CFE0, 260):
    print("   " + fmt(i))
    if i.mnemonic.startswith("ret"):
        break
print()
print("### 007258D0")
for i in list(dis(0x7258D0, 80))[:14]:
    print("   " + fmt(i))
