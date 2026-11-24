"""Diagnose +0x3C read sites: dump context + function containment + provenance origin.
Test whether the 5 reads are genuinely CellClass* or 'other-class reads' (audit warning).
"""
from lib import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, bisect

SITES = [0x575FF4,0x576059,0x5760B9,0x576124,0x576189]
GETCELLAT=0x5657A0

# atlas sorted entries for containment (discipline D: function interval containment)
atlas_sorted = sorted(atlas.items())
keys=[k for k,v in atlas_sorted]
def func_of(addr):
    i=bisect.bisect_right(keys,addr)-1
    if i>=0:
        e,sz=atlas_sorted[i]
        if e<=addr<e+sz: return (e,sz)
    return None

for s in SITES:
    print(f"\n{'='*70}\nREAD SITE {s:#x}  func={func_of(s)}")
    lo=max(s-0x60,0)
    for ins in disasm(lo, (s-lo)+0x20):
        if ins.id==0: continue
        mark='<<<' if ins.address==s else ''
        print(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str} {mark}")

# also: how many functions call GetCellAt, and is 0x575xxx region reached from one?
print(f"\n{'='*70}\nWhich GetCellAt call sites are near 0x575000-0x576200 ?")
for va in range(0x574000,0x576300):
    if u8(va)==0xE8:
        b=read(va,5)
        if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==GETCELLAT:
            print(f"  GCA call @ {va:#x} func={func_of(va)}")
