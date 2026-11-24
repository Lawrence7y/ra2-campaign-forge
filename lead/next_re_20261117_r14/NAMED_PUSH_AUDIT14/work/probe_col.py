import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n"+"="*72); print(t); print("="*72)

# Dump raw COL bytes for each claimed vtable base
for vt in [0x7E7F7C, 0x7E8344, 0x7ECE34]:
    colva = vt - 4
    sec(f"vtable {vt:08X} -> COL @ {colva:08X}")
    print("raw bytes:", hexb(colva, 20))
    sig=struct.unpack('<I',rd(colva,4))[0]
    off=struct.unpack('<I',rd(colva+4,4))[0]
    cd=struct.unpack('<I',rd(colva+8,4))[0]
    ptd=struct.unpack('<I',rd(colva+12,4))[0]
    pchd=struct.unpack('<I',rd(colva+16,4))[0]
    print(f"sig={sig} offset={off} cd={cd} pTD=0x{ptd:X} pCHD=0x{pchd:X}")
    print(f"  pTD as RVA -> VA 0x{0x400000+ptd:X}, as VA directly 0x{ptd:X}")
    for cand in (0x400000+ptd, ptd):
        if is_va(cand):
            print(f"  TD cand 0x{cand:X}: bytes {hexb(cand,40)}")
