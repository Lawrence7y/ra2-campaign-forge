# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import Image, EXE

img = Image(EXE)
for va, n, lab in ((0x0043B71F, 10, "0043B71F capstone"),
                   (0x00517D9D, 10, "00517D9D"),
                   (0x00521A11, 10, "00521A11"),
                   (0x00517ACC, 10, "00517ACC"),
                   (0x007EB240, 12, "007EB240 (slot122/123 区)"),
                   (0x007EB054, 4, "007EB054 (vt-4) 007EB058"),
                   (0x007E3EB8, 4, "007E3EB8 (vt-4) 007E3EBC"),
                   (0x008033B8, 16, "008033B8 COL"),
                   (0x007FC360, 16, "007FC360 COL(Building)"),
                   (0x00825510, 24, "Infantry TD+8"),
                   (0x00818D68, 24, "Building TD+8")):
    b = img.read(va, n)
    print("%-28s %08X : %s" % (lab, va, b.hex(" ").upper()))
