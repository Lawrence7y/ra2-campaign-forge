#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean full disasm of 0x47C3D0 (true end 0x47C4C7) -> EVIDENCE."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')
print("0x47C3D0..0x47C4C7 full disassembly (function end = ret 0xc @ 0x47C4BC, pad to 0x47C4C7)")
for i in disasm(0x47C3D0,0x47C4C8-0x47C3D0,skipdata=True):
    if is_data(i): continue
    m=""
    if i.mnemonic=='ret': m="  ; FUNCTION END"
    if i.mnemonic=='setg': m="  ; selector=1 branch"
    print(fmt_insn(i)+m)
