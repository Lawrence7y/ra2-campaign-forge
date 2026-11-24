"""AUDIT7: for candidate stream-slot functions, report vtable membership (vt, slot index, RTTI name)."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *

FNS = {
    0x00774979: 'ReadFile-chain',
    0x007D4BE1: 'WriteFile-chain A',
    0x007CF383: 'Read+WriteFile chain',
    0x00774C65: 'WriteFile-chain B',
    0x00774F47: 'WriteFile-chain C',
    0x0065CCD8: 'Read+WriteFile chain 2',
    0x004C8FDC: 'WriteFile-chain D',
    0x00551629: 'WriteFile-chain E',
}

for f, tag in sorted(FNS.items()):
    print(f"\n=== {f:08X} ({tag}) ===")
    for sec, va in find_dword(f):
        vt, idx = vtable_containing(va)
        r = rtti_of_vtable(vt)
        nm = r['name']
        print(f"  slot {va:08X} in {sec} vtable {vt:08X} index={idx} (+0x{idx*4:X}) RTTI={nm!r} col={r['col'] and hex(r['col'])}")
