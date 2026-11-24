import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
for c in (0x6C4F4C, 0x6C4C4C, 0x6C47CC):
    st = b.func_back(c)
    print(f"### caller of ctor @{c:08X}; function start {st and hex(st)}")
    print(show(b.dis(st, 60), "  "))
    print()
