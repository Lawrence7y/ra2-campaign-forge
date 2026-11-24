# -*- coding: utf-8 -*-
"""probe: are the new register-relative vptr-write hits real instruction boundaries?

Checks the writes found for the two documented DEAD tables and disassembles a window
ending at each candidate site, so the site is validated as an instruction start by
capstone rather than accepted from a raw byte match.
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_vt as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


def boundaries_in(lo, hi):
    """instruction start addresses produced by a linear sweep over [lo,hi)"""
    out = set()
    for insn in MD.disasm(P.IMG[P.TRO + (lo - P.TSTART):P.TRO + (hi - P.TSTART)], lo):
        out.add(insn.address)
    return out


for vt in (0x007E43E8, 0x007E17EC, 0x007E43C8, 0x007E17CC):
    print("=== writes of 0x%08X : %d" % (vt, len(P.WRITES_BY_VT.get(vt, []))))
    for site, kind, absv in P.WRITES_BY_VT.get(vt, []):
        fn = P.containing_fn(site)
        dead = fn in P.REG_DTORS
        # validate: is site an instruction start of a sweep starting 48 bytes earlier?
        lo = site - 48
        bset = boundaries_in(lo, site + 8)
        is_bound = site in bset
        ctx = P.IMG[P.TRO + (site - P.TSTART) - 6:P.TRO + (site - P.TSTART) + 10].hex(" ")
        print("  site 0x%08X kind=%-3s abs=%s fn=0x%s dead_fn=%s boundary=%s   [%s]"
              % (site, kind, ("0x%08X" % absv) if absv else "-",
                 ("%08X" % fn) if fn else "None", dead, is_bound, ctx))
