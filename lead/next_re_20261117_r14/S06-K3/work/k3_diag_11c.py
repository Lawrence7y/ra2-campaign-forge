"""Diagnose 0x11C read sites and 0x566xxx write sites from V2 scan.
Check genuine CellClass provenance, and whether 0x566xxx writes are real cell field writes.
"""
from lib import *
import bisect, struct
GETCELLAT=0x5657A0
asrt=sorted(atlas.items()); keys=[k for k,v in asrt]
def func_of(a):
    i=bisect.bisect_right(keys,a)-1
    if i>=0:
        e,sz=asrt[i]
        if e<=a<e+sz: return (e,sz)
    return None

READS=[0x5784A2,0x578686,0x58683A,0x586F04,0x57798B,0x575F81]
WRITES=[0x5665B5,0x566673,0x5666BB,0x56677F]
for label,sites in [('READ',READS),('WRITE',WRITES)]:
    for s in sites:
        print(f"\n{'='*66}\n{label} {s:#x} func={func_of(s)}")
        lo=s-0x50
        for ins in disasm(lo,(s-lo)+0x14):
            if ins.id==0: continue
            mark='<<<' if ins.address==s else ''
            print(f"  {ins.address:08X}: {ins.bytes.hex():<16} {ins.mnemonic} {ins.op_str} {mark}")
