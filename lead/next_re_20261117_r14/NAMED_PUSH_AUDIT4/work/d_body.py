"""Row 1: 006BF810 dispatch to per-row checks. Step A: dump body + ② vt/RTTI."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt

img = Img()
ENTRY = int(sys.argv[1], 16)
print("=== BODY %08X ===" % ENTRY)
for ins in img.body(ENTRY):
    print(fmt(ins))
