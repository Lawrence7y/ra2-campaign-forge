import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

# Row 1: 007B10C0 S18
va = 0x007B10C0
print("="*78)
print(f"ENTRY {va:08X}  first 0x180 bytes")
dump(va, 0x180)
