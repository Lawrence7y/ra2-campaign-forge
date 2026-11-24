import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

sites = [
    ("A", 0x0040D1B6, 0x0040D130, 0x40),   # global obj init?
    ("B", 0x0040D295, 0x0040D270, 0x60),
    ("C", 0x005BDA4A, 0x005BDA20, 0x60),
    ("D", 0x005BE0AE, 0x005BE080, 0x70),
]
for tag, site, start, n in sites:
    print("="*76)
    print(f"[{tag}] write site ~{site:08X}  (immediate operand at {site:08X})")
    dump(start, n)
    print()
