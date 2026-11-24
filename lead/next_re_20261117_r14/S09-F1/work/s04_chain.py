"""S09-F1 recon 04: registered WndProc chain + input consumption + LMBUp callers."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

print("=== top-level WndProc @ 0x7775C0 (first 0x120) ===")
print(dump(b, 0x7775C0, 0x120))

print("\n=== context around call to InputMgr::WndProc @ 0x7779CB ===")
print(dump(b, 0x777980, 0x80))

print("\n=== who calls 0x7775C0 (top WndProc)? ===")
print(" direct callers:", calls.get(0x7775C0, []))
print(" jmp callers:", jmps.get(0x7775C0, []))

# main input consumer: GetEvent callers context
for site, label in [(0x55E04E, "GetEvent in 0x55DEE0"), (0x432E18, "GetEvent in 0x432C70")]:
    print("\n=== %s @ %08X context ===" % (label, site))
    print(dump(b, site-0x30, 0x90))

# LMBUp callers
for site, label in [(0x69328B, "LMBUp caller 0x69328B"), (0x653D58, "LMBUp caller 0x653D58")]:
    print("\n=== %s context ===" % label)
    print(dump(b, site-0x40, 0xA0))
