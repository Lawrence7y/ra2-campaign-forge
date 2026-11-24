# -*- coding: utf-8 -*-
"""Check vt 007F3FE8 slot0 (callee of call [eax] in 006BF690) return convention."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def dump(ea, maxbytes=0xA0, maxi=50, title=""):
    print("="*64)
    print("FUNC %s %s atlas=%s" % (C.hx(ea), title, C.ATLAS.get(C.hx(ea))))
    for i,ins in enumerate(C.disasm_body(ea,maxbytes)):
        if i>=maxi: print(" ...trunc"); break
        print("  %s: %-9s %-38s ; %s"%(C.hx(ins.address),ins.mnemonic,ins.op_str,ins.bytes.hex().upper()))

def vtable(vt,n=6):
    print("--- VT %s ---"%C.hx(vt))
    for i in range(n):
        print("  [%+02X] slot#%d = %s"%(4*i,i,C.hx(C.u32(vt+4*i))))
    c=C.u32(vt-4); ci=C.parse_col(c) if c else None
    if ci:
        t=C.parse_td(ci['td'])
        print("  COL=%s pTD=%s name=%r"%(C.hx(c),C.hx(ci['td']),t['name'] if t else None))

vtable(0x007F3FE8,6)
s0=C.u32(0x007F3FE8)
print("slot0 -> %s"%C.hx(s0))
dump(s0,0xA0,50,"slot0 of vt007F3FE8 = callee of call [eax] in 006BF690")

# also confirm 006BEF10's call [eax] target slot0 of vt 007E5DAC = 004A2990
print("\n006BEF10: [esi] after ctor 004A2820 = 007E5DAC slot0 =", C.hx(C.u32(0x007E5DAC)))
print("006BF690: [esi] after ctor 006CAEC0 = 007F3FE8 slot0 =", C.hx(C.u32(0x007F3FE8)))
