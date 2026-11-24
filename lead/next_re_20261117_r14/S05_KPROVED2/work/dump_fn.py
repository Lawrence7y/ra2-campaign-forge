"""Dump disassembly of an entry with entry-relative offsets + CFG extent.
Usage: python dump_fn.py <entry_hex> [max_insns]"""
import sys, pickle
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work")
from pe_helpers import *
from capstone import *

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
D = pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'rb'))
insns, addr2i = D['insns'], D['addr2i']

def dump(entry, maxn=600):
    i=addr2i.get(entry)
    if i is None:
        print("entry not at instruction boundary"); return
    cnt=0
    for a,sz,m,o,b in insns[i:]:
        if cnt>=maxn: break
        hexb=b.hex()
        print(f"+0x{a-entry:04X}  {a:08X}  {hexb:<20} {m:<8} {o}")
        cnt+=1
        # stop if ret then several int3/nop padding
        if m.startswith('ret'):
            # look ahead 3 insns for padding / next-prologue
            pass
        cnt2=cnt

if __name__=='__main__':
    e=int(sys.argv[1],16)
    maxn=int(sys.argv[2],16) if len(sys.argv)>2 else 600
    dump(e,maxn)
