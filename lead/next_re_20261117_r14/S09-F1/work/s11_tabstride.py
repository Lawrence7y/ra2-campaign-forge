"""S09-F1 recon 11: verify tab array stride at +0x1544 (pointer array vs inline structs)."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()

for addr in (0x6A61C0, 0x6A63C8, 0x6A7590, 0x6A4E6C, 0x6A77B6):
    print("\n=== context @ %08X ==="%(addr-0x28))
    print(dump(b, addr-0x28, 0x80))

# Look at SetActiveTab 0x6A7590 for tab stride constant
print("\n=== SetActiveTab 0x6A7590 first 0x120 ===")
print(dump(b, 0x6A7590, 0x120))
